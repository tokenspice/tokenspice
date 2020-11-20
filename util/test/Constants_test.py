import unittest
        
import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('constants')
        
from util.constants import *

class ConstantsTest(unittest.TestCase):

    def testINF(self):
        self.assertTrue(INF > 1.0)

    def testSeconds(self):
        self.assertTrue(0 <
                        S_PER_MIN <
                        S_PER_HOUR <
                        S_PER_DAY  <
                        S_PER_WEEK <
                        S_PER_MONTH <
                        S_PER_YEAR)
        self.assertEqual(S_PER_HOUR, 60 * 60)
        self.assertEqual(S_PER_WEEK, 60 * 60 * 24 * 7)
        self.assertEqual(S_PER_YEAR, 60 * 60 * 24 * 365)

        self.assertTrue(isinstance(S_PER_HOUR, int))
        self.assertTrue(isinstance(S_PER_DAY, int))
        self.assertTrue(isinstance(S_PER_WEEK, int))
        self.assertTrue(isinstance(S_PER_MONTH, int))
        self.assertTrue(isinstance(S_PER_YEAR, int))

    def testTotalOceanSupply(self):
        self.assertTrue(1e6 < TOTAL_OCEAN_SUPPLY < 2e9)
        self.assertTrue(isinstance(TOTAL_OCEAN_SUPPLY, float))

