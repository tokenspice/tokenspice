import logging
log = logging.getLogger('marketagents')

import enforce
import random

from engine.BaseAgent import BaseAgent
from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools.web3util import toBase18
                    
@enforce.runtime_validation
class DataecosystemAgent(BaseAgent):
    """Will operate as a high-fidelity replacement for MarketplacesAgents,
    when it's ready."""
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        #FIXME
        
        
    def takeStep(self, state):
        #FIXME
        pass

        # new_agents.add(Agents.PublisherAgent(
        #     name = "publisher1", USD=0.0, OCEAN=0.0)) #magic number
        
        # new_agents.add(Agents.StakerspeculatorAgent(
        #     name = "stakerspeculator1", USD=0.0, OCEAN=0.0)) #magic number
        
        # new_agents.add(Agents.DataconsumerAgent(
        #     name = "dataconsumer1", USD=0.0, OCEAN=0.0)) #magic number
