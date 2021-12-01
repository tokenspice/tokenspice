from enforce_typing import enforce_types
from typing import List
from agents.DataconsumerAgent import DataconsumerAgent
from agents.PoolAgent import PoolAgent
from util import globaltokens
from util.base18 import toBase18
from util.constants import S_PER_HOUR


@enforce_types
class v3DataconsumerAgent(DataconsumerAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)

        self._s_since_speculate = 0
        self._s_between_speculates = 8 * S_PER_HOUR  # magic number

    def _candPoolAgents(self, state) -> List[PoolAgent]:
        """Pools that this agent can afford to buy 1.0 datatokens from,
        at least based on a first approximation.
        """
        OCEAN_address = globaltokens.OCEAN_address()
        OCEAN = self.OCEAN()
        OCEAN_base = toBase18(OCEAN)

        pool_agents = state.agents.filterToPool()
        # exclude rugged pool
        for pool_name in state.ss.rugged_pools:
            del pool_agents[pool_name]
        all_pool_agents = pool_agents.values()

        cand_pool_agents = []
        for pool_agent in all_pool_agents:
            pool = pool_agent.pool
            DT_address = pool_agent.datatoken_address

            tokenBalanceIn = pool.getBalance(OCEAN_address)
            tokenWeightIn = pool.getDenormalizedWeight(OCEAN_address)
            tokenBalanceOut = pool.getBalance(DT_address)
            tokenWeightOut = pool.getDenormalizedWeight(DT_address)
            tokenAmountOut = toBase18(1.0) #number of DTs
            swapFee = pool.getSwapFee()

            OCEANamountIn_base = pool.calcInGivenOut(
                tokenBalanceIn,
                tokenWeightIn,
                tokenBalanceOut,
                tokenWeightOut,
                tokenAmountOut,
                swapFee
            )

            if OCEANamountIn_base < OCEAN_base:
                cand_pool_agents.append(pool_agent)

        return cand_pool_agents
