from enforce_typing import enforce_types
import random
from typing import List

from assets.agents.PoolAgent import PoolAgent
from engine.AgentBase import AgentBase
from web3engine import bpool, datatoken, globaltokens
from web3tools.web3util import fromBase18, toBase18
from util import constants             

@enforce_types
class DataconsumerAgent(AgentBase):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        
        self._s_since_buy = 0
        self._s_between_buys = 3 * constants.S_PER_DAY #magic number
        
    def takeStep(self, state) -> None:
        self._s_since_buy += state.ss.time_step
        
        if self._doBuyDT(state):
            self._s_since_buy = 0
            self._buyDT(state)

    def _doBuyDT(self, state):
        cand_pool_agents = self._candPoolAgents(state)
        if not cand_pool_agents:
            return False
        else:
            return self._s_since_buy >= self._s_between_buys

    def _candPoolAgents(self, state) -> List[PoolAgent]:
        """Pools that this agent can afford to buy 1.0 datatokens from,
        at least based on a first approximation. 
        """
        OCEAN_address = globaltokens.OCEAN_address()
        OCEAN = self.OCEAN()
        OCEAN_base = toBase18(OCEAN)
        all_pool_agents = state.agents.filterToPool().values()
        cand_pool_agents = []
        for pool_agent in all_pool_agents:
            pool = pool_agent.pool
            DT_address = pool_agent.datatoken_address
            
            pool_DT_balance_base = pool.getBalance_base(DT_address)
            pool_OCEAN_balance_base = pool.getBalance_base(OCEAN_address)
            pool_DT_weight_base = pool.getDenormalizedWeight_base(DT_address)
            pool_OCEAN_weight_base = pool.getDenormalizedWeight_base(OCEAN_address)
            pool_swapFee_base = pool.getSwapFee_base()

            DT_amount_out_base = toBase18(1.0)

            spotPriceBefore_base = pool.getSpotPrice_base(
                tokenIn_address=OCEAN_address,
                tokenOut_address=DT_address)
            OCEANamountIn_base = pool.calcInGivenOut_base(
                tokenBalanceIn_base=pool_OCEAN_balance_base,
                tokenWeightIn_base=pool_OCEAN_weight_base,
                tokenBalanceOut_base=pool_DT_balance_base,
                tokenWeightOut_base=pool_DT_weight_base,
                tokenAmountOut_base=DT_amount_out_base,
                swapFee_base=pool_swapFee_base)

            if OCEANamountIn_base < OCEAN_base:
                cand_pool_agents.append(pool_agent)
                
        return cand_pool_agents

    def _buyDT(self, state):
        """Buy, and consume dataset"""
        DT_buy_amt = 1.0
        max_OCEAN_allow = self.OCEAN()
        OCEANtoken = globaltokens.OCEANtoken()

        cand_pool_agents = self._candPoolAgents(state)
        assert cand_pool_agents
        pool_agent = random.choice(cand_pool_agents)
        
        pool = pool_agent.pool
        DT = pool_agent.datatoken

        self._wallet.buyDT(pool, DT, DT_buy_amt, max_OCEAN_allow)
