import logging
log = logging.getLogger('marketagents')

import enforce
import random

from agents.BaseAgent import BaseAgent
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
            
@enforce.runtime_validation
class PoolAgent(BaseAgent):    
    def __init__(self, name: str, pool:bpool.BPool):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._bpool:bpool.BPool = pool

    @property
    def pool(self) -> bpool.BPool:
        return self._bpool
        
    def takeStep(self, state):
        #it's a smart contract robot, it doesn't initiate anything itself
        pass

    def sellStake(self, BPT_sell:float, agent):
        """'agent' sells BPT back into this pool"""
        self.pool.exitPool(
            poolAmountIn_base=toBase18(BPT_sell), 
            minAmountsOut_base=[toBase18(0.0),toBase18(0.0)],
            from_wallet=agent._wallet._web3wallet)
        
