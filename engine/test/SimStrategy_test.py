import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('simstrategy')

import enforce
from enforce.exceptions import RuntimeTypeError
import sys
import unittest

from engine.SimStrategy import *

@enforce.runtime_validation
class SimStrategyTest(unittest.TestCase):

    def testBasic(self):
        ss = SimStrategy()
        self.assertTrue(ss.save_interval >= 1)
        self.assertTrue(ss.max_ticks > 0)
        
    def testAnnualMktsGrowthRate(self):
        ss = SimStrategy()
        self.assertTrue(hasattr(ss, 'growth_rate_if_0_sales'))
        self.assertTrue(hasattr(ss, 'max_growth_rate'))
        self.assertTrue(hasattr(ss, 'tau'))

        ss.growth_rate_if_0_sales = -0.25
        ss.max_growth_rate = 0.5
        ss.tau = 0.075
        
        self.assertEqual(ss.annualMktsGrowthRate(0.0), -0.25)
        self.assertEqual(ss.annualMktsGrowthRate(0.0+1*ss.tau),
                         -0.25 + 0.75/2.0)
        self.assertEqual(ss.annualMktsGrowthRate(0.0+2*ss.tau),
                         -0.25 + 0.75/2.0 + 0.75/4.0)
        self.assertEqual(ss.annualMktsGrowthRate(1e6), 0.5)
        
    def testSetMaxTicks(self):
        ss = SimStrategy()
        ss.setMaxTicks(14)
        self.assertEqual(ss.max_ticks, 14)
        
    def testStr(self):
        ss = SimStrategy()
        self.assertTrue("SimStrategy" in str(ss))

    def testSchedule(self):
        s = Schedule(30, 5)
        self.assertEqual(s.interval, 30)
        self.assertEqual(s.n_actions, 5)
        self.assertTrue("Schedule" in str(s))

        with self.assertRaises(AssertionError): s = Schedule(0, 5)
        with self.assertRaises(AssertionError): s = Schedule(-1, 5)
        with self.assertRaises(AssertionError): s = Schedule(30, 0)
        with self.assertRaises(AssertionError): s = Schedule(30, -1)

        
