import logging
log = logging.getLogger('agents')

from enforce_typing import enforce_types

from agents.BaseAgent import BaseAgent
                        
@enforce_types
class GrantGivingAgent(BaseAgent):
    """
    Disburses funds at a fixed # evenly-spaced intervals.
    Same amount each time.
    """
    def __init__(self, name: str, USD: float, OCEAN: float,
                 receiving_agent_name: str,
                 s_between_grants: int,  n_actions: int):
        super().__init__(name, USD, OCEAN)
        self._receiving_agent_name: str = receiving_agent_name
        self._s_between_grants: int = s_between_grants
        self._USD_per_grant: float = USD / float(n_actions)
        self._OCEAN_per_grant: float = OCEAN / float(n_actions)
        
        self._tick_last_disburse = None
        
    def takeStep(self, state):
        do_disburse = False
        if self._tick_last_disburse is None:
            do_disburse = True
        else:
            n_ticks_since = state.tick - self._tick_last_disburse
            n_s_since = n_ticks_since * state.ss.time_step
            n_s_thr = self._s_between_grants            
            do_disburse = (n_s_since >= n_s_thr)
        
        if do_disburse:
            self._disburseFunds(state)
            self._tick_last_disburse = state.tick

    def _disburseFunds(self, state):
        #same amount each time
        receiving_agent = state.getAgent(self._receiving_agent_name)
        
        USD = min(self.USD(), self._USD_per_grant)
        self._transferUSD(receiving_agent, USD)
                
        OCEAN = min(self.OCEAN(), self._OCEAN_per_grant)
        self._transferOCEAN(receiving_agent, OCEAN)
    
