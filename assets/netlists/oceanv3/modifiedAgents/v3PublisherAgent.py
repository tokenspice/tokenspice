from enforce_typing import enforce_types
from assets.agents.PublisherAgent import PublisherAgent
from assets.agents.PoolAgent import PoolAgent
from web3engine import bfactory, bpool, globaltokens
from web3tools.web3util import toBase18

@enforce_types
class v3PublisherAgent(PublisherAgent):
    def _createPoolAgent(self, state) -> PoolAgent:
        assert self.OCEAN() > 0.0, "should not call if no OCEAN"
        wallet = self._wallet._web3wallet
        OCEAN = globaltokens.OCEANtoken()
        
        #name
        pool_i = len(state.agents.filterToPool())
        dt_name = f'DT{pool_i}'
        pool_agent_name = f'pool{pool_i}'
        
        #new DT
        DT = self._createDatatoken(dt_name, mint_amt=state.ss.DT_init) #magic number

        #new pool
        pool_address = bfactory.BFactory().newBPool(from_wallet=wallet)
        pool = bpool.BPool(pool_address)

        #bind tokens & add initial liquidity
        OCEAN_bind_amt = int(self.OCEAN()) #magic number: use all the OCEAN
        DT_bind_amt = state.ss.DT_stake
                
        DT.approve(pool.address, toBase18(DT_bind_amt), from_wallet=wallet)
        OCEAN.approve(pool.address, toBase18(OCEAN_bind_amt),from_wallet=wallet)
        
        pool.bind(DT.address, toBase18(DT_bind_amt),
                  toBase18(state.ss.pool_weight_DT), from_wallet=wallet)
        pool.bind(OCEAN.address, toBase18(OCEAN_bind_amt),
                  toBase18(state.ss.pool_weight_OCEAN), from_wallet=wallet)
        
        pool.finalize(from_wallet=wallet)

        #create agent
        pool_agent = PoolAgent(pool_agent_name, pool)
        state.addAgent(pool_agent)
        self._wallet.resetCachedInfo()
        
        return pool_agent