from enforce_typing import enforce_types
import random

from engine.AgentBase import AgentBase
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
from util import constants
                    
@enforce_types
class SpeculatorAgent(AgentBase):
    """Speculates by buying and selling DT"""
    
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)

        self._s_since_speculate = 0
        self._s_between_speculates = 1 * constants.S_PER_DAY #magic number
        
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
        
        # pool = random.choice(list(pool_agents)).pool
        pool_agent = random.choice(list(pool_agents))
        pool = pool_agent.pool

        DT = self.DT(pool_agent.datatoken)
        datatoken = pool_agent.datatoken

        max_OCEAN_allow = self.OCEAN()
        if DT > 0.0 and random.random() < 0.50: #magic number
            DT_sell_amt = 1.0 * DT #magic number
            self._wallet.sellDT(pool,datatoken, DT_sell_amt)
            
        else:
            DT_buy_amt = 1.0 #magic number
            self._wallet.buyDT(pool, datatoken, DT_buy_amt, max_OCEAN_allow)