from enforce_typing import enforce_types
import random
from typing import List

from agents.PoolAgent import PoolAgent
from sol057.contracts.oceanv3 import oceanv3util
from engine import AgentBase
from util import globaltokens
from util.base18 import toBase18
from util.constants import S_PER_DAY

# magic numbers
DEFAULT_DT_init = 1000.0
DEFAULT_DT_stake = 20.0
DEFAULT_pool_weight_DT = 3.0
DEFAULT_pool_weight_OCEAN = 7.0
DEFAULT_s_between_create = 7 * S_PER_DAY
DEFAULT_s_between_unstake = 3 * S_PER_DAY
DEFAULT_s_between_sellDT = 15 * S_PER_DAY
PERCENT_UNSTAKE = 0.10

DEFAULT_is_malicious = False
DEFAULT_s_wait_to_rug = int(DEFAULT_s_between_create / 2)
DEFAULT_s_rug_time = int(DEFAULT_s_wait_to_rug / 5)


@enforce_types
class PublisherAgent(AgentBase.AgentBaseEvm):
    def __init__(
        self,
        name: str,
        USD: float,
        OCEAN: float,
        DT_init: float = DEFAULT_DT_init,
        DT_stake: float = DEFAULT_DT_stake,
        pool_weight_DT: float = DEFAULT_pool_weight_DT,
        pool_weight_OCEAN: float = DEFAULT_pool_weight_OCEAN,
        s_between_create: int = DEFAULT_s_between_create,
        s_between_unstake: int = DEFAULT_s_between_unstake,
        s_between_sellDT: int = DEFAULT_s_between_sellDT,
        is_malicious: bool = DEFAULT_is_malicious,
        s_wait_to_rug: int = DEFAULT_s_wait_to_rug,
        s_rug_time: int = DEFAULT_s_rug_time,
    ):
        super().__init__(name, USD, OCEAN)

        self._DT_init: float = DT_init
        self._DT_stake: float = DT_stake
        self._pool_weight_DT: float = pool_weight_DT
        self._pool_weight_OCEAN: float = pool_weight_OCEAN

        self._s_since_create: int = 0
        self._s_between_create: int = s_between_create

        self._s_since_unstake: int = 0
        self._s_between_unstake: int = s_between_unstake

        self._s_since_sellDT: int = 0
        self._s_between_sellDT: int = s_between_sellDT

        self._is_malicious: bool = is_malicious
        self._s_wait_to_rug: int = s_wait_to_rug
        self._s_rug_time: int = s_rug_time

        self.pools: List[str] = []  # pools created by this agent

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

        # update self.pools
        self.pools.append(pool_agent.name)

        return pool_agent

    def _doUnstakeOCEAN(self, state) -> bool:
        if not state.agents.filterByNonzeroStake(self):
            return False

        if self._is_malicious:
            return (
                (self._s_since_unstake >= self._s_between_unstake)
                & (self._s_since_create >= self._s_wait_to_rug)
                & (self._s_since_create <= self._s_wait_to_rug + self._s_rug_time)
            )
        else:
            return self._s_since_unstake >= self._s_between_unstake

    def _unstakeOCEANsomewhere(self, state):
        """Choose what pool to unstake and by how much. Then do the action."""
        pool_agents = state.agents.filterByNonzeroStake(self)
        pool_agent = random.choice(list(pool_agents.values()))
        BPT = self.BPT(pool_agent.pool)
        BPT_unstake = PERCENT_UNSTAKE * BPT
        self.unstakeOCEAN(BPT_unstake, pool_agent.pool)

    def _doSellDT(self, state) -> bool:
        if not self._DTsWithNonzeroBalance(state):
            return False
        if self._is_malicious:
            return (
                (self._s_since_sellDT >= self._s_between_sellDT)
                & (self._s_since_create >= self._s_wait_to_rug)
                & (self._s_since_create <= self._s_wait_to_rug + self._s_rug_time)
            )
        else:
            return self._s_since_sellDT >= self._s_between_sellDT

    def _sellDTsomewhere(self, state, perc_sell: float = 0.01):
        """Choose what DT to sell and by how much. Then do the action."""
        if self._is_malicious:
            # unstakes the newest pool
            pool_agent = state.getAgent(self.pools[-1])
            DT = pool_agent.datatoken
            pool = pool_agent.pool
        else:
            # random by DT, then pool (could be something else)
            cand_DTs = self._DTsWithNonzeroBalance(state)
            DT = random.choice(cand_DTs)
            cand_pools = self._poolsWithDT(state, DT)
            pool = random.choice(cand_pools)

        DT_balance_amt = self.DT(DT)
        assert DT_balance_amt > 0.0
        DT_sell_amt = perc_sell * DT_balance_amt
        self._wallet.sellDT(pool, DT, DT_sell_amt)

    def _doRug(self, state):
        if not self._is_malicious:
            return False
        if not self.pools:
            return False
        return self._s_since_create >= self._s_wait_to_rug

    def _rug(self, state):
        assert self._is_malicious, "should only call if malicious"
        assert self.pools, "can't rug if no pools"
        assert hasattr(state, "rugged_pools"), "state needs 'rugged_pools attr"
        state.rugged_pools.append(self.pools[-1])

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
