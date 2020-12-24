import logging
log = logging.getLogger('marketagents')

from enforce_typing import enforce_types # type: ignore[import]
import random

from agents.BaseAgent import BaseAgent
from web3engine import bpool, datatoken, globaltokens
from web3tools.web3util import toBase18
            
@enforce_types
class PoolAgent(BaseAgent):    
    def __init__(self, name: str, pool:bpool.BPool):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._pool:bpool.BPool = pool
        
        self._dt_address = self._datatokenAddress()
        self._dt = datatoken.Datatoken(self._dt_address)

    @property
    def pool(self) -> bpool.BPool:
        return self._pool
    
    @property
    def datatoken_address(self) -> str:
        return self._dt_address
    
    @property
    def datatoken(self) -> datatoken.Datatoken:
        return self._dt
        
    def takeStep(self, state):
        #it's a smart contract robot, it doesn't initiate anything itself
        pass
        
    def _datatokenAddress(self):
        addrs = self._pool.getCurrentTokens()
        assert len(addrs) == 2
        OCEAN_addr = globaltokens.OCEANtoken().address
        for addr in addrs:
            if addr != OCEAN_addr:
                return addr
        raise AssertionError("should never get here")
