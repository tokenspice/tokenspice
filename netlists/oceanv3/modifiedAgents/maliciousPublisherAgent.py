from enforce_typing import enforce_types
from typing import List
from agents.PublisherAgent import PublisherAgent
from agents.PoolAgent import PoolAgent
from sol057.contracts.oceanv3 import oceanv3util
from util import globaltokens
from util.base18 import toBase18
from util.constants import S_PER_DAY, S_PER_HOUR

@enforce_types
class maliciousPublisherAgent(PublisherAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        
        self._s_since_create = 0
        self._s_between_create = 10 * S_PER_DAY #magic number

        self._s_wait_to_rug = 5 * S_PER_DAY
        self._s_rug_time = 1 * S_PER_DAY
        
        self._s_since_unstake = 0
        self._s_between_unstake = 1 * S_PER_HOUR #magic number
        
        self._s_since_sellDT = 0
        self._s_between_sellDT = 1 * S_PER_HOUR #magic number

        self.pools = [] # type: List[str]
    
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
        
        if self._s_since_create == self._s_wait_to_rug:
            if len(self.pools)>0:
                state.ss.rugged_pools.append(self.pools[-1])
    
    def _createPoolAgent(self, state) -> PoolAgent:
        assert self.OCEAN() > 0.0, "should not call if no OCEAN"
        account = self._wallet._account
        OCEAN = globaltokens.OCEANtoken()
        
        #name
        pool_i = len(state.agents.filterToPool())
        dt_name = f'DT{pool_i}'
        pool_agent_name = f'pool{pool_i}'
        
        #new DT
        DT = self._createDatatoken(dt_name, mint_amt=state.ss.m_DT_init) #magic number

        #new pool
        pool = oceanv3util.newBPool(account)

        #bind tokens & add initial liquidity
        OCEAN_bind_amt = self.OCEAN() #magic number: use all the OCEAN
        DT_bind_amt = state.ss.m_DT_stake
                
        DT.approve(pool.address, toBase18(DT_bind_amt), {'from':account})
        OCEAN.approve(pool.address, toBase18(OCEAN_bind_amt),{'from':account})
        
        pool.bind(DT.address, toBase18(DT_bind_amt),
                  toBase18(state.ss.pool_weight_DT), {'from':account})
        pool.bind(OCEAN.address, toBase18(OCEAN_bind_amt),
                  toBase18(state.ss.pool_weight_OCEAN), {'from':account})
        
        pool.finalize({'from':account})

        #create agent
        pool_agent = PoolAgent(pool_agent_name, pool)
        state.addAgent(pool_agent)
        self._wallet.resetCachedInfo()

        self.pools.append(pool_agent_name)
        
        return pool_agent
    def _doUnstakeOCEAN(self, state) -> bool:
        if not state.agents.filterByNonzeroStake(self):
            return False
        return (self._s_since_unstake >= self._s_between_unstake) & (self._s_since_create>=self._s_wait_to_rug) \
            & (self._s_since_create <= self._s_wait_to_rug + self._s_rug_time)

    def _unstakeOCEANsomewhere(self, state):
        """unstake the lastest create pool"""
        pool_agent = state.getAgent(self.pools[-1])
        BPT = self.BPT(pool_agent.pool)
        BPT_unstake = 0.20 * BPT #magic number
        self.unstakeOCEAN(BPT_unstake, pool_agent.pool)

    def _doSellDT(self, state) -> bool:
        if not self._DTsWithNonzeroBalance(state):
            return False
        return (self._s_since_sellDT >= self._s_between_sellDT) & (self._s_since_create>=self._s_wait_to_rug) \
            & (self._s_since_create <= self._s_wait_to_rug + self._s_rug_time)

    def _sellDTsomewhere(self, state, perc_sell:float=0.20):
        """Choose what DT to sell and by how much. Then do the action."""
        pool_agent = state.getAgent(self.pools[-1])
        pool = pool_agent.pool
        DT   = pool_agent.datatoken
        DT_balance_amt = self.DT(DT)
        DT_sell_amt = perc_sell * DT_balance_amt
        
        self._wallet.sellDT(pool, DT, DT_sell_amt)
