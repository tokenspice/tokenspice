from enforce_typing import enforce_types
import random

from agents.PoolAgent import PoolAgent
from sol057.contracts.oceanv3 import oceanv3util
from engine import AgentBase
from util import globaltokens
from util.base18 import toBase18
from util.constants import S_PER_DAY

@enforce_types
class PublisherAgent(AgentBase.AgentBaseEvm):
    def __init__(self, name:str, USD:float, OCEAN:float,
                 DT_init:float = 1000.0, #magic numbers, this line & below
                 DT_stake:float = 20.0,
                 pool_weight_DT:float = 3.0,
                 pool_weight_OCEAN:float = 7.0,
                 s_between_create:int = 7 * S_PER_DAY,
                 s_between_unstake:int = 3 * S_PER_DAY,
                 s_between_sellDT:int = 15 * S_PER_DAY
    ):
        super().__init__(name, USD, OCEAN)

        self._DT_init:float = DT_init
        self._DT_stake:float = DT_stake
        self._pool_weight_DT:float = pool_weight_DT
        self._pool_weight_OCEAN:float = pool_weight_OCEAN

        self._s_since_create:int = 0
        self._s_between_create:int = s_between_create 

        self._s_since_unstake:int = 0
        self._s_between_unstake:int = s_between_unstake

        self._s_since_sellDT:int = 0
        self._s_between_sellDT:int = s_between_sellDT

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

    def _doCreatePool(self) -> bool:
        if self.OCEAN() < 200.0:  # magic number
            return False
        return self._s_since_create >= self._s_between_create

    def _createPoolAgent(self, state) -> PoolAgent:
        assert self.OCEAN() > 0.0, "should not call if no OCEAN"
        account = self._wallet._account
        OCEAN = globaltokens.OCEANtoken()

        # name
        pool_i = len(state.agents.filterToPool())
        dt_name = f"DT{pool_i}"
        pool_agent_name = f"pool{pool_i}"

        # new DT
        DT = self._createDatatoken(dt_name, mint_amt=self._DT_init)

        # new pool
        pool = oceanv3util.newBPool(account)

        # bind tokens & add initial liquidity
        OCEAN_bind_amt = self.OCEAN()  # magic number: use all the OCEAN
        DT_bind_amt = self._DT_stake 

        DT.approve(pool.address, toBase18(DT_bind_amt), {"from": account})
        OCEAN.approve(pool.address, toBase18(OCEAN_bind_amt), {"from": account})

        pool.bind(
            DT.address,
            toBase18(DT_bind_amt),
            toBase18(self._pool_weight_DT),
            {"from": account},
        )
        pool.bind(
            OCEAN.address,
            toBase18(OCEAN_bind_amt),
            toBase18(self._pool_weight_OCEAN),
            {"from": account},
        )

        pool.finalize({"from": account})

        # create agent
        pool_agent = PoolAgent(pool_agent_name, pool)
        state.addAgent(pool_agent)
        self._wallet.resetCachedInfo()

        return pool_agent

    def _doUnstakeOCEAN(self, state) -> bool:
        if not state.agents.filterByNonzeroStake(self):
            return False
        return self._s_since_unstake >= self._s_between_unstake

    def _unstakeOCEANsomewhere(self, state):
        """Choose what pool to unstake and by how much. Then do the action."""
        pool_agents = state.agents.filterByNonzeroStake(self)
        pool_agent = random.choice(list(pool_agents.values()))
        BPT = self.BPT(pool_agent.pool)
        BPT_unstake = 0.10 * BPT  # magic number
        self.unstakeOCEAN(BPT_unstake, pool_agent.pool)

    def _doSellDT(self, state) -> bool:
        if not self._DTsWithNonzeroBalance(state):
            return False
        return self._s_since_sellDT >= self._s_between_sellDT

    def _sellDTsomewhere(self, state, perc_sell: float = 0.01):
        """Choose what DT to sell and by how much. Then do the action."""

        cand_DTs = self._DTsWithNonzeroBalance(state)
        assert cand_DTs, "only call this method if have DTs w >0 balance"
        DT = random.choice(cand_DTs)

        DT_balance_amt = self.DT(DT)
        assert DT_balance_amt > 0.0
        DT_sell_amt = perc_sell * DT_balance_amt  # magic number

        cand_pools = self._poolsWithDT(state, DT)
        assert cand_pools, "there should be at least 1 pool with this DT"
        pool = random.choice(cand_pools)

        self._wallet.sellDT(pool, DT, DT_sell_amt)

    def _poolsWithDT(self, state, DT) -> list:
        """Return a list of pools that have this DT. Typically exactly 1 pool"""
        return [
            pool_agent.pool
            for pool_agent in state.agents.filterToPool().values()
            if pool_agent.datatoken.address == DT.address
        ]

    def _DTsWithNonzeroBalance(self, state) -> list:
        """Return a list of Datatokens that this agent has >0 balance of"""
        pool_agents = state.agents.filterToPool().values()
        DTs = [pool_agent.datatoken for pool_agent in pool_agents]
        return [DT for DT in DTs if self.DT(DT) > 0.0]

    def _createDatatoken(self, dt_name: str, mint_amt: float):
        """Create datatoken contract and mint DTs to self."""
        account = self._wallet._account
        DT = oceanv3util.newDatatoken("", dt_name, dt_name, toBase18(mint_amt), account)
        DT.mint(account.address, toBase18(mint_amt), {"from": account})
        self._wallet.resetCachedInfo()
        return DT
