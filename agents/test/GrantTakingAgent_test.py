import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('agents')

import enforce
import unittest

from agents import BaseAgent, GrantTakingAgent
from engine import SimState, SimStrategy

@enforce.runtime_validation
class GrantTakingAgentTest(unittest.TestCase):
        
    def testGrantTakingAgent(self):
        class DummySimState:
            def __init__(self):
                pass
                
            def OCEANprice(self) -> float:
                return 3.0
        state = DummySimState()
        a = GrantTakingAgent.GrantTakingAgent("foo", USD=10.0, OCEAN=20.0)
        self.assertEqual(a._spent_at_tick, 0.0)

        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertEqual(a.OCEAN(), 0.0)
        self.assertEqual(a._spent_at_tick, 10.0 + 20.0*3.0)
        
        a.takeStep(state)
        self.assertEqual(a._spent_at_tick, 0.0)

        a.receiveUSD(5.0)
        a.takeStep(state)
        self.assertEqual(a._spent_at_tick, 5.0)
        
        a.takeStep(state)
        self.assertEqual(a._spent_at_tick, 0.0)
                  
        
                         
                         
