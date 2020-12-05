import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('agents')

import enforce
import unittest

from agents import BaseAgent, OCEANBurnerAgent
from engine import SimState, SimStrategy

@enforce.runtime_validation
class OCEANBurnerAgentTest(unittest.TestCase):

    def testOCEANBurnerAgent1_fixedOCEANprice(self):
        class DummySimState:
            def __init__(self):
                self._total_OCEAN_burned: float = 0.0
                self._total_OCEAN_burned_USD: float = 0.0
                
            def OCEANprice(self) -> float:
                return 2.0
        state = DummySimState()
        a = OCEANBurnerAgent.OCEANBurnerAgent("foo", USD=10.0, OCEAN=0.0)
        
        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertEqual(state._total_OCEAN_burned_USD, 10.0)
        self.assertEqual(state._total_OCEAN_burned, 5.0)
        self.assertEqual(a.OCEAN(), 0.0)

        a.receiveUSD(20.0)
        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertEqual(state._total_OCEAN_burned_USD, 30.0)
        self.assertEqual(state._total_OCEAN_burned, 15.0)

    def testOCEANBurnerAgent2_changingOCEANprice(self):
        class DummySimState:
            def __init__(self):
                self._total_OCEAN_burned: float = 0.0
                self._total_OCEAN_burned_USD: float = 0.0
                self._initial_OCEAN: float = 100.0
                
            def OCEANprice(self) -> float:
                return self.overallValuation() / self.OCEANsupply()

            def overallValuation(self) -> float:
                return 200.0

            def OCEANsupply(self) -> float:
                return self._initial_OCEAN - self._total_OCEAN_burned
            
        state = DummySimState()
        a = OCEANBurnerAgent.OCEANBurnerAgent("foo", USD=10.0, OCEAN=0.0)
        self.assertEqual(state.OCEANprice(), 2.0) #(val 200)/(supply 100)
        
        a.takeStep(state)
        self.assertTrue(0.0 < state.OCEANsupply() < 100.0)
        self.assertTrue(state.OCEANprice() > 2.0) 
        self.assertEqual(state.OCEANprice(), 200.0 / state.OCEANsupply())
        self.assertEqual(a.USD(), 0.0)
        self.assertAlmostEqual(state._total_OCEAN_burned_USD, 10.0)
        self.assertTrue(4.0 < state._total_OCEAN_burned < 5.0) 

        price1 = state.OCEANprice()
        a.receiveUSD(20.0)
        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertTrue(state.OCEANprice() > price1)
        self.assertAlmostEqual(state._total_OCEAN_burned_USD, 30.0)
        self.assertTrue(13.0 < state._total_OCEAN_burned < 15.0)
        
                          
                         
                         
