import logging
log = logging.getLogger('marketagents')

import enforce
import random

from engine.BaseAgent import BaseAgent
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
            
class PublisherAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        
    def takeStep(self, state) -> None:
        if self._doCreateNewPool():
            agent_name = self._createNewPoolAgent(state)

    def _doCreateNewPool(self) -> bool:
        return (random.random() < 0.1) #FIXME HACK #magic number

    def _createNewPoolAgent(self, state) -> str:
        #name
        pool_i = len(state.poolAgents())
        dt_name = f'DT{pool_i}'
        agent_name = f'pool{pool_i}'
        
        #create new dt
        wallet = self._wallet._web3wallet
        amt = toBase18(1000.0) #magic number
        dt_factory = dtfactory.DTFactory()
        dt_address = dt_factory.createToken('', dt_name, dt_name, amt, wallet)
        dt = datatoken.Datatoken(dt_address)            

        #new pool
        pool_factory = bfactory.BFactory()
        pool_address = pool_factory.newBPool(from_wallet=wallet)
        pool = bpool.BPool(pool_address)

        #bind tokens, add liquidity, etc. 
        # FIXME. How: see test_2tokens_basic. Be sure that self.OCEAN() is ok.

        #create agent and return
        agent = PoolAgent(agent_name, pool)
        state.addAgent(agent)
        return agent.name
        
