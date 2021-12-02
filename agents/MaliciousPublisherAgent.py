from enforce_typing import enforce_types
from typing import List

from agents import PublisherAgent

#magic numbers
DEFAULT_s_wait_to_rug = int(PublisherAgent.DEFAULT_s_between_create/2)
DEFAULT_s_rug_time = int(DEFAULT_s_wait_to_rug/5)
PERCENT_UNSTAKE = 0.20

@enforce_types
class MaliciousPublisherAgent(PublisherAgent.PublisherAgent):
    def __init__(
            self, name:str, USD:float, OCEAN:float,
            #parameters like regular publisher
            DT_init:float = PublisherAgent.DEFAULT_DT_init,
            DT_stake:float = PublisherAgent.DEFAULT_DT_stake,
            pool_weight_DT:float = PublisherAgent.DEFAULT_pool_weight_DT,
            pool_weight_OCEAN:float = PublisherAgent.DEFAULT_pool_weight_OCEAN,
            s_between_create:int = PublisherAgent.DEFAULT_s_between_create,
            s_between_unstake:int = PublisherAgent.DEFAULT_s_between_unstake,
            s_between_sellDT:int = PublisherAgent.DEFAULT_s_between_sellDT,
                 
            #parameters new to malicous agent
            s_wait_to_rug:int = DEFAULT_s_wait_to_rug,
            s_rug_time:int = DEFAULT_s_rug_time,
    ):
        super().__init__(
            name, USD=USD, OCEAN=OCEAN,
            DT_init=DT_init,
            DT_stake=DT_stake,
            pool_weight_DT=pool_weight_DT,
            pool_weight_OCEAN=pool_weight_OCEAN,
            s_between_create=s_between_create,
            s_between_unstake=s_between_unstake,
            s_between_sellDT=s_between_sellDT,
        )

        self._s_wait_to_rug:int = s_wait_to_rug
        self._s_rug_time:int = s_rug_time

        self.pools = []  # type: List[str]

    def takeStep(self, state) -> None:
        self._s_since_create += state.ss.time_step
        self._s_since_unstake += state.ss.time_step
        self._s_since_sellDT += state.ss.time_step

        if self._doCreatePool():
            self._s_since_create = 0
            self._createPoolAgent(state)

        if self._doUnstakeOCEAN(state):
            self._s_since_unstake = 0
            self._unstakeOCEANsomewhere(state)

        if self._doSellDT(state):
            self._s_since_sellDT = 0
            self._sellDTsomewhere(state)

        if self._doRug(state):
            if len(self.pools) > 0:
                state.rugged_pools.append(self.pools[-1])

    def _createPoolAgent(self, state):
        pool_agent = super()._createPoolAgent(state)
        self.pools.append(pool_agent.name)
        return pool_agent

    def _doUnstakeOCEAN(self, state) -> bool:
        if not state.agents.filterByNonzeroStake(self):
            return False
        return (
            (self._s_since_unstake >= self._s_between_unstake)
            & (self._s_since_create >= self._s_wait_to_rug)
            & (self._s_since_create <= self._s_wait_to_rug + self._s_rug_time)
        )

    def _unstakeOCEANsomewhere(self, state):
        """Choose what pool to unstake and by how much. Then do the action."""
        #this agent unstakes the newest pool
        pool_agent = state.getAgent(self.pools[-1])
        BPT = self.BPT(pool_agent.pool)
        BPT_unstake = PERCENT_UNSTAKE * BPT  # magic number
        self.unstakeOCEAN(BPT_unstake, pool_agent.pool)

    def _doSellDT(self, state) -> bool:
        if not self._DTsWithNonzeroBalance(state):
            return False
        return (
            (self._s_since_sellDT >= self._s_between_sellDT)
            & (self._s_since_create >= self._s_wait_to_rug)
            & (self._s_since_create <= self._s_wait_to_rug + self._s_rug_time)
        )

    def _sellDTsomewhere(self, state, perc_sell: float = 0.20):
        """Choose what DT to sell and by how much. Then do the action."""
        #this agent unstakes the newest pool
        pool_agent = state.getAgent(self.pools[-1])
        pool = pool_agent.pool
        DT = pool_agent.datatoken
        DT_balance_amt = self.DT(DT)
        DT_sell_amt = perc_sell * DT_balance_amt

        self._wallet.sellDT(pool, DT, DT_sell_amt)

    def _doRug(self, state):
        return self._s_since_create == self._s_wait_to_rug and \
            len(self.pools) > 0

    def _rug(self, state):
        assert len(self.pools) > 0, "can't rug if no pools"
        assert hasattr(state, "rugged_pools"), "state needs 'rugged_pools attr"
        state.rugged_pools.append(self.pools[-1])
