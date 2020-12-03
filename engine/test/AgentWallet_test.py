import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('wallet')

import enforce
import unittest

from engine.AgentWallet import *

@enforce.runtime_validation
class AgentWalletTest(unittest.TestCase):

    def testStr(self):
        w = AgentWallet()        
        self.assertTrue("AgentWallet" in str(w))
        
    def testInitiallyEmpty(self):
        w = AgentWallet()
        
        self.assertEqual(w.USD(), 0.0)
        self.assertEqual(w.OCEAN(), 0.0)
        
    def testInitiallyFilled(self):
        w = AgentWallet(USD=1.2, OCEAN=3.4)
        
        self.assertEqual(w.USD(), 1.2)
        self.assertEqual(w.OCEAN(), 3.4)
        
    def testUSD(self):
        w = AgentWallet()

        w.depositUSD(13.25)
        self.assertEqual(w.USD(), 13.25)
        
        w.depositUSD(1.00)
        self.assertEqual(w.USD(), 14.25)
        
        w.withdrawUSD(2.10)
        self.assertEqual(w.USD(), 12.15)
        
        w.depositUSD(0.0)
        w.withdrawUSD(0.0)
        self.assertEqual(w.USD(), 12.15)

        self.assertEqual(w.totalUSDin(), 13.25+1.0)

        with self.assertRaises(AssertionError):
            w.depositUSD(-5.0)
        
        with self.assertRaises(AssertionError):
            w.withdrawUSD(-5.0)
        
        with self.assertRaises(ValueError):
            w.withdrawUSD(1000.0)
        
    def testOCEAN(self):
        w = AgentWallet()

        w.depositOCEAN(13.25)
        self.assertEqual(w.OCEAN(), 13.25)
        
        w.depositOCEAN(1.00)
        self.assertEqual(w.OCEAN(), 14.25)
        
        w.withdrawOCEAN(2.10)
        self.assertEqual(w.OCEAN(), 12.15)
        
        w.depositOCEAN(0.0)
        w.withdrawOCEAN(0.0)
        self.assertEqual(w.OCEAN(), 12.15)
        
        self.assertEqual(w.totalOCEANin(), 13.25+1.0)

        with self.assertRaises(AssertionError):
            w.depositOCEAN(-5.0)
        
        with self.assertRaises(AssertionError):
            w.withdrawOCEAN(-5.0)
        
        with self.assertRaises(ValueError):
            w.withdrawOCEAN(1000.0)
            
    def testFloatingPointRoundoff(self):
        w = AgentWallet(USD=2.4, OCEAN=2.4)
        w.withdrawUSD(2.4000000000000004) #should not get ValueError
        w.withdrawOCEAN(2.4000000000000004) #
        self.assertEqual(w.USD(), 0.0)
        self.assertEqual(w.OCEAN(), 0.0)
