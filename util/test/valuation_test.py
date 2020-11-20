import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('valuation')

import numpy
import unittest

from util.valuation import *

class valuationTest(unittest.TestCase):

    def test_ps(self):
        self.assertEqual(firmValuationPS(1e3, 30.0), 30e3)
        
    def test_pe(self):
        self.assertEqual(firmValuationPE(1e3, 20.0), 20e3)
        
    def test_OCEANprice(self):
        self.assertEqual(OCEANprice(10e9, 1e9), 10.0)
        
