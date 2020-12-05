import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('agents')

import enforce
import unittest

from agents.BaseAgent import BaseAgent
from agents.GrantGivingAgent import GrantGivingAgent
from engine import SimState, SimStrategy
from util.constants import S_PER_DAY

@enforce.runtime_validation
class GrantGivingAgentTest(unittest.TestCase):
        
    def testGrantGivingAgent(self):
        ss = SimStrategy.SimStrategy()
        assert hasattr(ss, 'time_step')
        ss.time_step = S_PER_DAY

        state = SimState.SimState(ss)
        
        class SimpleAgent(BaseAgent):
            def takeStep(self, state):
                pass
        state.agents["a1"] = a1 = SimpleAgent("a1", 0.0, 0.0)
        self.assertEqual(a1.OCEAN(), 0.0) 
        
        g1 = GrantGivingAgent(
            "g1", USD=0.0, OCEAN=1.0,
            receiving_agent_name="a1",
            s_between_grants=S_PER_DAY*3, n_actions=4)
        self.assertEqual(g1.OCEAN(), 1.0) 

        g1.takeStep(state); state.tick += 1 #tick = 1 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*1/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*1/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 2
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*1/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*1/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 3
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*1/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*1/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 4 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*2/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*2/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 5
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*2/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*2/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 6
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*2/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*2/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 7 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*3/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*3/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 8
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*3/4)
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*3/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 9
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*3/4)
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*3/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 10 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*4/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*4/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 11
        g1.takeStep(state); state.tick += 1 #tick = 12
        g1.takeStep(state); state.tick += 1 #tick = 13 #don't disperse, 0 left
        
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*4/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*4/4)
