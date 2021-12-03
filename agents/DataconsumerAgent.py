import random
from typing import List

from enforce_typing import enforce_types

from agents.PoolAgent import PoolAgent
from engine import AgentBase
from util import globaltokens
from util.base18 import toBase18
from util import constants

# magic numbers
DEFAULT_s_between_buys = 3 * constants.S_PER_DAY
DEFAULT_profit_margin_on_consume = 0.2


@enforce_types
class DataconsumerAgent(AgentBase.AgentBaseEvm):
    def __init__(
        self,
        name: str,
        USD: float,
        OCEAN: float,
        s_between_buys: int = DEFAULT_s_between_buys,
        profit_margin_on_consume: float = DEFAULT_profit_margin_on_consume,
    ):  # pylint: disable=too-many-arguments
        super().__init__(name, USD, OCEAN)

        self._s_since_buy = 0
        self._s_between_buys = s_between_buys
        self._profit_margin_on_consume = profit_margin_on_consume

    def takeStep(self, state) -> None:
        self._s_since_buy += state.ss.time_step
        if self._doBuyAndConsumeDT(state):
            self._s_since_buy = 0
            self._buyAndConsumeDT(state)

    def _doBuyAndConsumeDT(self, state):
        cand_pool_agents = self._candPoolAgents(state)
        if not cand_pool_agents:
            return False
        return self._s_since_buy >= self._s_between_buys

    def _candPoolAgents(  # pylint: disable=too-many-locals
        self, state
    ) -> List[PoolAgent]:
        """Pools that this agent can afford to buy 1.0 datatokens from,
        at least based on a first approximation.
        """
        OCEAN_address = globaltokens.OCEAN_address()
        OCEAN_base = toBase18(self.OCEAN())
        all_pool_agents = state.agents.filterToPool()

        cand_pool_agents = []
        for pool_name, pool_agent in all_pool_agents.items():
            # filter 1: pool rugged?
            if hasattr(state, "rugged_pools") and pool_name in state.rugged_pools:
                continue

            # filter 2: agent has enough funds?
            pool = pool_agent.pool
            DT_address = pool_agent.datatoken_address

            tokenBalanceIn = pool.getBalance(OCEAN_address)
            tokenWeightIn = pool.getDenormalizedWeight(OCEAN_address)
            tokenBalanceOut = pool.getBalance(DT_address)
            tokenWeightOut = pool.getDenormalizedWeight(DT_address)
            tokenAmountOut = toBase18(1.0)  # number of DTs
            swapFee = pool.getSwapFee()

            OCEANamountIn_base = pool.calcInGivenOut(
                tokenBalanceIn,
                tokenWeightIn,
                tokenBalanceOut,
                tokenWeightOut,
                tokenAmountOut,
                swapFee,
            )

            if OCEANamountIn_base >= OCEAN_base:
                continue

            # passed all filters! Add this agent
            cand_pool_agents.append(pool_agent)

        return cand_pool_agents

    def _buyAndConsumeDT(self, state):
        """Buy dataset, then consume it"""
        DT_buy_amt = 1.0  # buy just enough to consume once
        max_OCEAN_allow = self.OCEAN()

        cand_pool_agents = self._candPoolAgents(state)
        assert cand_pool_agents
        pool_agent = random.choice(cand_pool_agents)

        pool = pool_agent.pool
        DT = pool_agent.datatoken

        DT_before = self.DT(DT)
        OCEAN_before = self.OCEAN()

        # buy
        self._wallet.buyDT(pool, DT, DT_buy_amt, max_OCEAN_allow)

        DT_after = self.DT(DT)
        OCEAN_after = self.OCEAN()

        assert DT_after == (DT_before + DT_buy_amt)
        assert OCEAN_after < OCEAN_before

        OCEAN_spend = OCEAN_before - OCEAN_after

        # consume
        publisher_agent = state.agents.agentByAddress(pool_agent.controller_address)
        self._wallet.transferDT(publisher_agent._wallet, DT, DT_buy_amt)

        # get business value due to consume
        OCEAN_returned = OCEAN_spend * (1.0 + self._profit_margin_on_consume)
        self.receiveOCEAN(OCEAN_returned)

        return OCEAN_spend
