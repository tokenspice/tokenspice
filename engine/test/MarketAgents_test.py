import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('marketagents')

import enforce
import unittest

from engine import BaseAgent, SimState, SimStrategy
from engine.MarketAgents import *

@enforce.runtime_validation
class MarketAgentsTest(unittest.TestCase):
    
    def testPublisherAgent(self):
        pass
    
    def testPoolAgent(self):
        pass
    
    def testStakerspeculatorAgent(self):
        pass
    
    def testDataconsumerAgent(self):
        pass
