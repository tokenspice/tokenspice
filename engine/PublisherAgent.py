import logging
log = logging.getLogger('marketagents')

import enforce
import random

from engine.BaseAgent import BaseAgent
from engine.PoolAgent import PoolAgent
from util.constants import POOL_WEIGHT_DT, POOL_WEIGHT_OCEAN
from web3engine import bfactory, bpool, datatoken, dtfactory, globaltokens
from web3tools.web3util import toBase18
        
@enforce.runtime_validation    
class PublisherAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        
    def takeStep(self, state) -> None:
        if self._doCreatePool():
            agent_name = self._createPoolAgent(state)

        if self._doSellStake(state):
            self._sellStake(state)

    def _doCreatePool(self) -> bool:
        return (self.OCEAN() > 200.0) #magic number

    def _createPoolAgent(self, state) -> str:
        assert self.OCEAN() > 0.0, "should not call if no OCEAN"
        wallet = self._wallet._web3wallet
        OCEAN = globaltokens.OCEANtoken()
        
        #name
        pool_i = len(state.agents.filterToPool())
        dt_name = f'DT{pool_i}'
        pool_agent_name = f'pool{pool_i}'
        
        #new DT
        DT = self._createDatatoken(dt_name, mint_amt=1000.0) #magic number

        #new pool
        pool_address = bfactory.BFactory().newBPool(from_wallet=wallet)
        pool = bpool.BPool(pool_address)

        #bind tokens & add initial liquidity
        OCEAN_bind_amt = self.OCEAN() #magic number: use all the OCEAN
        DT_bind_amt = 20.0 #magic number
                
        DT.approve(pool.address, toBase18(DT_bind_amt), from_wallet=wallet)
        OCEAN.approve(pool.address, toBase18(OCEAN_bind_amt),from_wallet=wallet)
        
        pool.bind(DT.address, toBase18(DT_bind_amt),
                  toBase18(POOL_WEIGHT_DT), from_wallet=wallet)
        pool.bind(OCEAN.address, toBase18(OCEAN_bind_amt),
                  toBase18(POOL_WEIGHT_OCEAN), from_wallet=wallet)
        
        pool.finalize(from_wallet=wallet)

        #create agent
        pool_agent = PoolAgent(pool_agent_name, pool)
        state.addAgent(pool_agent)
        
        return pool_agent.name

    def _createDatatoken(self,dt_name:str,mint_amt:float)-> datatoken.Datatoken:
        """Create datatoken contract and mint DTs to self."""
        wallet = self._wallet._web3wallet
        DT_address = dtfactory.DTFactory().createToken(
            '', dt_name, dt_name, toBase18(mint_amt), from_wallet=wallet)
        DT = datatoken.Datatoken(DT_address)
        DT.mint(wallet.address, toBase18(mint_amt), from_wallet=wallet)
        return DT

    def _doSellStake(self, state) -> bool:
        if not state.agents.filterByNonzeroStake(self):
            return False
        return (random.random() < 0.1) #magic number. FIXME - be more timebased

    def _sellStake(self, state):
        pool_agents = state.agents.filterByNonzeroStake(self)
        pool_name = random.choice(list(pool_agents))
        pool_agent = pool_agents[pool_name]
        self._sellStakeOfPool(pool_agent)

    def _sellStakeOfPool(self, pool_agent:PoolAgent):
        BPT = self.BPT(pool_agent.pool)
        assert BPT > 0.0
        BPT_sell = 0.10 * BPT #magic number -- sell 10% of current stake
        pool_agent.pool.exitPool(
            poolAmountIn_base=toBase18(BPT_sell), 
            minAmountsOut_base=[toBase18(0.0),toBase18(0.0)],
            from_wallet=self._wallet._web3wallet)
        
