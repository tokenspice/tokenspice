import logging
log = logging.getLogger('marketagents')

from enforce_typing import enforce_types
import random

from agents.BaseAgent import BaseAgent
from agents.PublisherAgent import PublisherAgent
from agents.StakerspeculatorAgent import StakerspeculatorAgent
from agents.DataconsumerAgent import DataconsumerAgent
from web3tools.web3util import toBase18
                    
@enforce_types
class DataecosystemAgent(BaseAgent):
    """Will operate as a high-fidelity replacement for MarketplacesAgents,
    when it's ready."""
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)        
        
    def takeStep(self, state):
        if self._doCreatePublisherAgent(state):
            self._createPublisherAgent(state)
            
        if self._doCreateStakerspeculatorAgent(state):
            self._createStakerspeculatorAgent(state)
            
        if self._doCreateDataconsumerAgent(state):
            self._createDataconsumerAgent(state)

    def _doCreatePublisherAgent(self, state) -> bool:
        #magic number: rule - only create if no agents so far
        return (not state.publisherAgents()) 
            
    def _createPublisherAgent(self, state) -> None:
        name = 'foo' #FIXME
        USD = 0.0 #FIXME magic number
        OCEAN = 1000.0 #FIXME magic number
        new_agent = PublisherAgent(name=name, USD=USD, OCEAN=OCEAN)
        state.addAgent(new_agent)

    def _doCreateStakerspeculatorAgent(self, state) -> bool:
        #magic number: rule - only create if no agents so far
        return (not state.stakerspeculatorAgents())  
            
    def _createStakerspeculatorAgent(self, state) -> None:
        name = 'foo' #FIXME
        USD = 0.0 #FIXME magic number
        OCEAN = 1000.0 #FIXME magic number
        new_agent = StakerspeculatorAgent(name=name, USD=USD, OCEAN=OCEAN)
        state.addAgent(new_agent)

    def _doCreateDataconsumerAgent(self, state) -> bool:
        #magic number: rule - only create if no agents so far
        return (not state.dataconumerAgents()) 
            
    def _createDataconsumerAgent(self, state) -> None:
        name = 'foo' #FIXME
        USD = 0.0 #FIXME magic number
        OCEAN = 1000.0 #FIXME magic number
        new_agent = DataconsumerAgent(name=name, USD=USD, OCEAN=OCEAN)
        state.addAgent(new_agent)
