"""Implement SpeculatorAgent *and* StakerspeculatorAgent.py
-parent: SpeculatorAgentBase
-child: SpeculatorAgent - speculate via buying & selling DT
-child: StakerspeculatorAgent - speculate via staking & unstaking
"""

from abc import abstractmethod
import random
from typing import List

from enforce_typing import enforce_types

from engine import AgentBase
from util import constants

# magic numbers
DEFAULT_s_between_speculates = 1 * constants.S_PER_DAY


@enforce_types
class SpeculatorAgentBase(AgentBase.AgentBaseEvm):
    def __init__(
        self,
        name: str,
        USD: float,
        OCEAN: float,
        s_between_speculates: int = DEFAULT_s_between_speculates,
    ):
        super().__init__(name, USD, OCEAN)

        self._s_since_speculate: int = 0
        self._s_between_speculates: int = s_between_speculates

    def takeStep(self, state):
        self._s_since_speculate += state.ss.time_step

        if self._doSpeculateAction(state):
            self._s_since_speculate = 0
            self._speculateAction(state)

    def _doSpeculateAction(self, state):
        pool_agents = self._poolsForSpeculate(state)
        if not pool_agents:
            return False

        return self._s_since_speculate >= self._s_between_speculates

    @abstractmethod
    def _speculateAction(self, state):
        pass

    @staticmethod
    def _poolsForSpeculate(state) -> List[AgentBase.AgentBaseAbstract]:
        pool_agents = state.agents.filterToPool()

        if hasattr(state, "rugged_pools"):
            for pool_name in state.rugged_pools:
                del pool_agents[pool_name]

        pool_agents = pool_agents.values()
        return pool_agents


class SpeculatorAgent(SpeculatorAgentBase):
    """Speculates by buying and selling DT"""

    def _speculateAction(self, state):
        pool_agents = self._poolsForSpeculate(state)
        assert pool_agents, "need pools to be able to speculate"

        pool_agent = random.choice(list(pool_agents))
        pool = pool_agent.pool

        DT = self.DT(pool_agent.datatoken)
        datatoken = pool_agent.datatoken

        max_OCEAN_allow = self.OCEAN()
        if DT > 0.0 and random.random() < 0.50:  # magic number
            DT_sell_amt = 1.0 * DT  # magic number
            self._wallet.sellDT(pool, datatoken, DT_sell_amt)

        else:
            DT_buy_amt = 1.0  # magic number
            self._wallet.buyDT(pool, datatoken, DT_buy_amt, max_OCEAN_allow)


@enforce_types
class StakerspeculatorAgent(SpeculatorAgentBase):
    """Speculates by staking and unstaking"""

    def _speculateAction(self, state):
        pool_agents = self._poolsForSpeculate(state)
        assert pool_agents, "need pools to be able to speculate"

        pool = random.choice(list(pool_agents)).pool
        BPT = self.BPT(pool)

        if BPT > 0.0 and random.random() < 0.50:  # magic number
            BPT_sell = 0.10 * BPT  # magic number
            self.unstakeOCEAN(BPT_sell, pool)

        else:
            OCEAN_stake = 0.10 * self.OCEAN()  # magic number
            self.stakeOCEAN(OCEAN_stake, pool)
