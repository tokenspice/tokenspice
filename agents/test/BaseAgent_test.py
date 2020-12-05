import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('baseagent')

import enforce
import unittest

from agents.BaseAgent import *

@enforce.runtime_validation
class MyTestAgent(BaseAgent):
    def takeStep(self, state):
        pass

@enforce.runtime_validation
class BaseAgentTest(unittest.TestCase):
        
    def testInit(self):
        agent = MyTestAgent("agent1", USD=1.1, OCEAN=1.2)
        self.assertEqual(agent.name, "agent1")
        self.assertEqual(agent.USD(), 1.1)
        self.assertEqual(agent.OCEAN(), 1.2)
        self.assertTrue("MyTestAgent" in str(agent))
        
    def testReceiveAndSend(self):
        #agents are of arbitary classes
        agent = MyTestAgent("agent1", USD=0.0, OCEAN=3.30)
        agent2 = MyTestAgent("agent2", USD=0.0, OCEAN=3.30)
                
        #USD
        self.assertAlmostEqual(agent.USD(), 0.00)
        agent.receiveUSD(13.25)
        self.assertAlmostEqual(agent.USD(), 13.25)

        agent._transferUSD(None, 1.10)
        self.assertAlmostEqual(agent.USD(), 12.15)

        self.assertAlmostEqual(agent2.USD(), 0.00)
        agent._transferUSD(agent2, 1.00)
        self.assertAlmostEqual(agent.USD(), 12.15 - 1.00)
        self.assertAlmostEqual(agent2.USD(), 0.00 + 1.00)
        
        #OCEAN
        self.assertAlmostEqual(agent.OCEAN(), 3.30)
        agent.receiveOCEAN(2.01)
        self.assertAlmostEqual(agent.OCEAN(), 5.31)

        agent._transferOCEAN(None, 0.20)
        self.assertAlmostEqual(agent.OCEAN(), 5.11)

        self.assertAlmostEqual(agent2.OCEAN(), 3.30)
        agent._transferOCEAN(agent2, 0.10)
        self.assertAlmostEqual(agent.OCEAN(),   5.11 - 0.10)
        self.assertAlmostEqual(agent2.OCEAN(),  3.30 + 0.10)
