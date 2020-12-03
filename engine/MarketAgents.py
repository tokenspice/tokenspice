import logging
log = logging.getLogger('marketagents')

import enforce

from engine.BaseAgent import BaseAgent
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
            
@enforce.runtime_validation
class PoolAgent(BaseAgent):    
    def __init__(self, name: str, pool:bpool.BPool):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        #FIXME
        
    def takeStep(self, state):
        #FIXME
        pass

class PublisherAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
                
        self.pool_agents = [] #list of PoolAgent

        #HACK - just add one pool agent
        pool_agent = self._createNewPoolAgent() 
        self.pool_agents.append(pool_agent) 
        
    def takeStep(self, state) -> None:
        create_new_pool = False #FIXME: have fancier way to choose

        if create_new_pool:
            pool_agent = self._createNewPoolAgent()
            self.pools.append(pool_agent)

    def _createNewPoolAgent(self) -> PoolAgent:
        wallet = self._wallet._web3wallet
        
        #create new dt
        amount = toBase18(1000.0) #magic number
        dt_factory = dtfactory.DTFactory()
        dt_address = dt_factory.createToken('', 'DT', 'DT', amount, wallet)
        dt = datatoken.Datatoken(dt_address)            

        #new pool
        pool_factory = bfactory.BFactory()
        pool_address = pool_factory.newBPool(from_wallet=wallet)
        pool = bpool.BPool(pool_address)

        #bind tokens, add liquidity, etc. 
        # FIXME. How: see test_2tokens_basic

        #create agent and return
        pool_agent = PoolAgent("pool1", pool)
        return pool_agent
        
@enforce.runtime_validation
class StakerspeculatorAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        #FIXME
        
    def takeStep(self, state):
        #FIXME
        pass
        
@enforce.runtime_validation
class DataconsumerAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        #FIXME
        
    def takeStep(self, state):
        #FIXME
        pass
