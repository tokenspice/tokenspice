import logging
log = logging.getLogger('marketagents')

import enforce
import random

from agents.BaseAgent import BaseAgent
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
from util import constants
                    
@enforce.runtime_validation
class StakerspeculatorAgent(BaseAgent):
    """Speculates by staking and unstaking"""
    
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)

        self._s_since_speculate = 0
        self._s_between_speculates = 8 * constants.S_PER_HOUR #magic number
        
    def takeStep(self, state):
        self._s_since_speculate += state.ss.time_step

        if self._doSpeculateAction(state):
            self._s_since_speculate = 0
            self._speculateAction(state)

    def _doSpeculateAction(self, state):
        pool_agents = state.agents.filterToPool().values()
        if not pool_agents:
            return False
        else:
            return self._s_since_speculate >= self._s_between_speculates

    def _speculateAction(self, state):
        pool_agents = state.agents.filterToPool().values()
        assert pool_agents, "need pools to be able to speculate"
        
        pool_agent = random.choice(pool_agents)
        BPT = self.BPT(pool_agent.pool)
        
        if BPT > 0.0 and random.random() < 0.50: #magic number
            BPT_sell = 0.10 * BPT #magic number
            self.unstakeOCEAN(BPT_sell, pool_agent.pool)
            
        else:
            OCEAN = 0.10 * self.OCEAN() #magic number
            pool_agent.stakeOCEAN(OCEAN_stake, pool_agent.pool)
        
            
