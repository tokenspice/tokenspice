import logging
log = logging.getLogger('marketagents')

import enforce
import random

from engine.BaseAgent import BaseAgent
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
            
@enforce.runtime_validation
class PoolAgent(BaseAgent):    
    def __init__(self, name: str, pool:bpool.BPool):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self.pool = pool
        
    def takeStep(self, state):
        pass
