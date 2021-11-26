from enforce_typing import enforce_types
import random
from agents.StakerspeculatorAgent import StakerspeculatorAgent
from util.constants import  S_PER_HOUR

@enforce_types
class v3StakerspeculatorAgent(StakerspeculatorAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)

        self._s_since_speculate = 0
        self._s_between_speculates = 8 * S_PER_HOUR #magic number
    
    def _speculateAction(self, state):
        pool_agents = state.agents.filterToPool()
        # exclude rugged pool
        for pool_name in state.ss.rugged_pools:
            del pool_agents[pool_name]
        
        pool_agents = pool_agents.values()
        assert pool_agents, "need pools to be able to speculate"
        
        pool = random.choice(list(pool_agents)).pool
        BPT = self.BPT(pool)
        
        if BPT > 0.0 and random.random() < 0.50: #magic number
            BPT_sell = 0.10 * BPT #magic number
            self.unstakeOCEAN(BPT_sell, pool)
            
        else:
            OCEAN_stake = 0.10 * self.OCEAN() #magic number
            self.stakeOCEAN(OCEAN_stake, pool)
