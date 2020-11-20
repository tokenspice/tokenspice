import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('mathutil')

from enforce.exceptions import RuntimeTypeError
import numpy
import unittest
        
from util.mathutil import *

class mathutilTest(unittest.TestCase):

    def setUp(self):
        pass

    def isNumber(self):
        for x in [-2, 0, 2, 20000,
                  -2.1, -2.0, 0.0, 2.0, 2.1, 2e6]:
            self.assertTrue(isNumber(x))

        for x in [[], [1,2], {}, {1:2, 2:3}, None, "", "foo"]:
            self.assertFalse(isNumber(x))

    def testIntInStr(self):        
        self.assertEqual(intInStr("123"), 123)
        self.assertEqual(intInStr("sdds12"), 12)
        self.assertEqual(intInStr("sdds12afdsf3zz"), 123)
        self.assertEqual(intInStr("sdds12afdsf39sf#@#@9fdsj!!49sd"), 1239949)

        self.assertEqual(intInStr("34.56"), 3456)
        self.assertEqual(intInStr("0.00006"), 6)
        self.assertEqual(intInStr("10.00006"), 1000006)

        with self.assertRaises(ValueError): intInStr("")
        for v in [32, None, {}, []]:
            with self.assertRaises(RuntimeTypeError):
                intInStr(v)

    def testRange(self):
        r = Range(2.2)
        p = r.drawRandomPoint()
        self.assertEqual(p, 2.2)

        r = Range(-1.5, 2.5)
        for i in range(20):
            p = r.drawRandomPoint()
            self.assertTrue(-1.5 <= p <= 2.5)
        
        r = Range(2.3, None)
        p = r.drawRandomPoint()
        self.assertEqual(p, 2.3)
        
        r = Range(2.3, 2.3)
        p = r.drawRandomPoint()
        self.assertEqual(p, 2.3)

        with self.assertRaises(AssertionError): Range(3.0, 1.0)
            
        with self.assertRaises(RuntimeTypeError): Range(3)
        with self.assertRaises(RuntimeTypeError): Range("foo")
        with self.assertRaises(RuntimeTypeError): Range(3.0, "foo")
        
    def testRangeStr(self):
        r = Range(2.2)
        s = str(r)
        self.assertTrue("Range={" in s)
        self.assertTrue("min_" in s)
        self.assertTrue("2.2" in s)
        self.assertTrue("Range}" in s) 

    def testRandunif(self):
        for i in range(20):
            #happy path
            p = randunif(-1.5, 2.5)
            self.assertTrue(-1.5 <= p <= 2.5)

            p = randunif(-1.5, -0.5)
            self.assertTrue(-1.5 <= p <= -0.5)
            
            p = randunif(0.0, 100.0)
            self.assertTrue(0.0 <= p <= 100.0)

            #min = max
            p = randunif(-2.0, -2.0)
            self.assertEqual(p, -2.0)
            
            p = randunif(0.0, 0.0)
            self.assertEqual(p, 0.0)
            
            p = randunif(2.0, 2.0)
            self.assertEqual(p, 2.0)

        #exceptions
        with self.assertRaises(AssertionError): p = randunif(0.0, -1.0)

        with self.assertRaises(RuntimeTypeError): randunif(0.0, 3)
        with self.assertRaises(RuntimeTypeError): randunif(0, 3.0)
        with self.assertRaises(RuntimeTypeError): randunif(3.0, "foo")

    def test_round_sig(self):
        self.assertEqual(round_sig(123456, 1), 100000)
        self.assertEqual(round_sig(123456, 2), 120000)
        self.assertEqual(round_sig(123456, 3), 123000)
        self.assertEqual(round_sig(123456, 4), 123500)
        self.assertEqual(round_sig(123456, 5), 123460)
        self.assertEqual(round_sig(123456, 6), 123456)
    
        self.assertEqual(round_sig(1.23456, 1), 1.00000)
        self.assertEqual(round_sig(1.23456, 2), 1.20000)
        self.assertEqual(round_sig(1.23456, 3), 1.23000)
        self.assertEqual(round_sig(1.23456, 4), 1.23500)
        self.assertEqual(round_sig(1.23456, 5), 1.23460)
        self.assertEqual(round_sig(1.23456, 6), 1.23456)
    
        self.assertEqual(round_sig(1.23456e9, 1), 1.00000e9)
        self.assertEqual(round_sig(1.23456e9, 2), 1.20000e9)
        self.assertEqual(round_sig(1.23456e9, 3), 1.23000e9)
        self.assertEqual(round_sig(1.23456e9, 4), 1.23500e9)
        self.assertEqual(round_sig(1.23456e9, 5), 1.23460e9)
        self.assertEqual(round_sig(1.23456e9, 6), 1.23456e9)
