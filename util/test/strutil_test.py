import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('strutil')

from enforce.exceptions import RuntimeTypeError
import random
import unittest

from util import mathutil
from util.strutil import *

class strutilTest(unittest.TestCase):

    def testStrMixin(self):
        class Foo(StrMixin):
            def __init__(self):
                self.x = 1
                self.y = 2
                self.d = {"a":3, "b":4}
                self.d2 = {}
                self.__ignoreVal = "ignoreVal"

            def ignoreMethod(self):
                pass

        f = Foo()
        s = str(f)
        s2 = s.replace(" ","")
        self.assertTrue("Foo={" in s)
        self.assertTrue("x=1" in s2)
        self.assertTrue("y=2" in s2)
        self.assertTrue("d=dict={" in s2)
        self.assertTrue("d2={}" in s2)
        self.assertTrue("'a':3" in s2)
        self.assertTrue("'b':4" in s2)
        self.assertTrue("Foo}" in s)
        self.assertFalse("ignoreVal" in s)
        self.assertFalse("ignoreMethod" in s)

    def testDictStr(self):
        d = {"a":3, "b":4}
        s = dictStr(d)
        s2 = s.replace(" ","")
        self.assertTrue("dict={" in s)
        self.assertTrue("'a':3" in s2)
        self.assertTrue("'b':4" in s2)
        self.assertTrue("dict}" in s)
        
    def testEmptyDictStr(self):
        d = {}
        s = dictStr(d)
        self.assertEqual(s, "{}")
                
    def testAsCurrency(self):
        self.assertEqual(asCurrency(0), "$0.00")
        self.assertEqual(asCurrency(0.0), "$0.00")
        self.assertEqual(asCurrency(10), "$10.00")
        self.assertEqual(asCurrency(10.0), "$10.00")
        self.assertEqual(asCurrency(1234.567), "$1,234.57")
        self.assertEqual(asCurrency(2e6), "$2,000,000.00")
        self.assertEqual(asCurrency(2e6+0.03), "$2,000,000.03")
    
        self.assertEqual(asCurrency(0, decimals=False), "$0")
        self.assertEqual(asCurrency(0.0, False), "$0")
        self.assertEqual(asCurrency(10, False), "$10")
        self.assertEqual(asCurrency(10.0, False), "$10")
        self.assertEqual(asCurrency(1234.567, False), "$1,235")
        self.assertEqual(asCurrency(2e6, False), "$2,000,000")
        self.assertEqual(asCurrency(2e6+0.03, False), "$2,000,000")
        
    def testPrettyBigNum1_DoRemoveZeros(self):
        #decimals needed
        self.assertEqual(prettyBigNum(1.23456e13), "1.23e13")
        self.assertEqual(prettyBigNum(1.23456e12), "1.23e12")
        self.assertEqual(prettyBigNum(1.23456e11), "123B")
        self.assertEqual(prettyBigNum(1.23456e10), "12.3B")
        self.assertEqual(prettyBigNum(1.23456e9), "1.23B")
        self.assertEqual(prettyBigNum(1.23456e8), "123M")
        self.assertEqual(prettyBigNum(1.23456e7), "12.3M")
        self.assertEqual(prettyBigNum(1.23456e6), "1.23M")
        self.assertEqual(prettyBigNum(1.23456e5), "123K")
        self.assertEqual(prettyBigNum(1.23456e4), "12.3K")
        self.assertEqual(prettyBigNum(1.23456e3), "1.23K")
        self.assertEqual(prettyBigNum(1.23456e2), "123")
        self.assertEqual(prettyBigNum(1.23456e1), "12.3")
        self.assertEqual(prettyBigNum(1.23456e0), "1.23")
        self.assertEqual(prettyBigNum(1.23456e-1), "0.12")
        self.assertEqual(prettyBigNum(1.23456e-2), "1.23e-2")
        self.assertEqual(prettyBigNum(1.23456e-3), "1.23e-3")
        self.assertEqual(prettyBigNum(1.23456e-10), "1.23e-10")

        #decimals not needed
        self.assertEqual(prettyBigNum(1e13), "1e13")
        self.assertEqual(prettyBigNum(1e12), "1e12")
        self.assertEqual(prettyBigNum(1e11), "100B")
        self.assertEqual(prettyBigNum(1e10), "10B")
        self.assertEqual(prettyBigNum(1e9), "1B")
        self.assertEqual(prettyBigNum(1e8), "100M")
        self.assertEqual(prettyBigNum(1e7), "10M")
        self.assertEqual(prettyBigNum(1e6), "1M")
        self.assertEqual(prettyBigNum(1e5), "100K")
        self.assertEqual(prettyBigNum(1e4), "10K")
        self.assertEqual(prettyBigNum(1e3), "1K")
        self.assertEqual(prettyBigNum(1e2), "100")
        self.assertEqual(prettyBigNum(1e1), "10")
        self.assertEqual(prettyBigNum(1), "1")
        self.assertEqual(prettyBigNum(1e-1), "0.1")
        self.assertEqual(prettyBigNum(1e-2), "1e-2")
        self.assertEqual(prettyBigNum(1e-3), "1e-3")
        self.assertEqual(prettyBigNum(1e-10), "1e-10")

        #catch roundoff properly
        self.assertEqual(prettyBigNum(57.02e10), "570B")
        self.assertEqual(prettyBigNum(57.02e9), "57B")
        self.assertEqual(prettyBigNum(57.02e8), "5.7B")
        self.assertEqual(prettyBigNum(57.02e7), "570M")
        self.assertEqual(prettyBigNum(57.02e6), "57M")
        self.assertEqual(prettyBigNum(57.02e5), "5.7M")
        self.assertEqual(prettyBigNum(57.02e4), "570K")
        self.assertEqual(prettyBigNum(57.02e3), "57K")
        self.assertEqual(prettyBigNum(57.02), "57")
        self.assertEqual(prettyBigNum(27.02), "27")

        #zero
        self.assertEqual(prettyBigNum(0), "0")
        self.assertEqual(prettyBigNum(0.0), "0")

        #negative
        self.assertEqual(prettyBigNum(-1.23456e13), "-1.23e13")
        self.assertEqual(prettyBigNum(-1.23456e11), "-123B")
        self.assertEqual(prettyBigNum(-1.23456e7), "-12.3M")
        self.assertEqual(prettyBigNum(-1.23456e3), "-1.23K")
        self.assertEqual(prettyBigNum(-1.23456e2), "-123")
        self.assertEqual(prettyBigNum(-1.23456e-1), "-0.12")
        self.assertEqual(prettyBigNum(-1.23456e-3), "-1.23e-3")

        self.assertEqual(prettyBigNum(-1e13), "-1e13")
        self.assertEqual(prettyBigNum(-1e10), "-10B")
        self.assertEqual(prettyBigNum(-1e7), "-10M")
        self.assertEqual(prettyBigNum(-1e5), "-100K")
        self.assertEqual(prettyBigNum(-1e1), "-10")
        self.assertEqual(prettyBigNum(-1e-1), "-0.1")
        self.assertEqual(prettyBigNum(-1e-10), "-1e-10")

    def generatePairsForPrettyBigNum2_Random_DoRemoveZeroes(self):        
        for i in range(100):
            power = random.choice(list(range(-4, 14)))
            sigfigs = random.choice([1,2,3,4,5])
            x = random.random() * pow(10, power)
            x = mathutil.round_sig(x, sigfigs)

            s = prettyBigNum(x) #prettyBigNum(x, remove_zeroes=False)
            print("            (%15s, '%s')," % (x, s))

    def testPrettyBigNum2_Random_DoRemoveZeroes(self):
        #these are generated via method above, then manually fixed as needed
        x_s_pairs = [
            (         1200.0, '1.2K'),
            (          5.284, '5.28'),
            (2380000000000.0, '2.38e12'),
            (          0.071, '7.1e-2'),
            (        86000.0, '86K'),
            (     49300000.0, '49.3M'),
            (      4020000.0, '4.02M'),
            (   9600000000.0, '9.6B'),
            (4800000000000.0, '4.8e12'),
            (      3000000.0, '3M'),
            (          6.256, '6.26'),
            (        89500.0, '89.5K'),
            ( 156170000000.0, '156B'),
            (        80000.0, '80K'),
            (    710000000.0, '710M'),
            (        0.65312, '0.65'),
            ( 553000000000.0, '553B'),
            (           0.04, '4e-2'),
            (       6.03e-05, '6.03e-5'),
            (     90300000.0, '90.3M'),
            ( 828000000000.0, '828B'),
            (        0.09939, '9.94e-2'),
            (      5552000.0, '5.55M'),
            (         0.0004, '4e-4'),
            (        10000.0, '10K'),
            (       513000.0, '513K'),
            (        0.00097, '9.7e-4'),
            (        52325.0, '52.3K'),
            (     90000000.0, '90M'),
            (        0.00266, '2.66e-3'),
            (       400000.0, '400K'),
            (       400000.0, '400K'),
            (    107480000.0, '107M'),
            (6785200000000.0, '6.79e12'),
            (     33680000.0, '33.7M'),
            (       625000.0, '625K'),
            (  52790000000.0, '52.8B'),
            (  51354000000.0, '51.4B'),
            (        71660.0, '71.7K'),
            (2726000000000.0, '2.73e12'),
            (          671.6, '672'),
            (     10000000.0, '10M'),
            (   3415000000.0, '3.42B'),
            (        0.00272, '2.72e-3'),
            (      3000000.0, '3M'),
            (      0.0004171, '4.17e-4'),
            (       0.002181, '2.18e-3'),
            (       400000.0, '400K'),
            (  20000000000.0, '20B'),
            (     1.8458e-05, '1.85e-5'),
            (       403000.0, '403K'),
            (       3.81e-05, '3.81e-5'),
            (          2e-05, '2e-5'),
            (   6800000000.0, '6.8B'),
            (1000000000000.0, '1e12'),
            (4405300000000.0, '4.41e12'),
            (      0.0048122, '4.81e-3'),
            (       891000.0, '891K'),
            (     99000000.0, '99M'),
            (           50.0, '50'),
            (          0.128, '0.13'),
            (  23440000000.0, '23.4B'),
            (        41000.0, '41K'),
            (7271100000000.0, '7.27e12'),
            (3230000000000.0, '3.23e12'),
            (          64.99, '65'),
            (    740000000.0, '740M'),
            (       217000.0, '217K'),
            (          900.0, '900'),
            (            6.0, '6'),
            (         0.7631, '0.76'),
            (           0.04, '4e-2'),
            (     61700000.0, '61.7M'),
            (         0.0449, '4.49e-2'),
            (    737360000.0, '737M'),
            (   3415000000.0, '3.42B'),
            (  81244000000.0, '81.2B'),
            (        4.9e-05, '4.9e-5'),
            (      9493000.0, '9.49M'),
            ]
        for (x, target_s) in x_s_pairs:
            self.assertEqual(prettyBigNum(x), target_s)

    def testPrettyBigNum3_Random_DontRemoveZeros(self):
        #these are generated via method above, then manually fixed as needed
        x_s_pairs = [
            (         1200.0, '1.20K'),
            (          5.284, '5.28'),
            (2380000000000.0, '2.38e12'),
            (          0.071, '7.10e-2'),
            (        86000.0, '86.00K'),
            (     49300000.0, '49.30M'),
            (      4020000.0, '4.02M'),
            (   9600000000.0, '9.60B'),
            (4800000000000.0, '4.80e12'),
            (      3000000.0, '3.00M'),
            (          6.256, '6.26'),
            (        89500.0, '89.50K'),
            ( 156170000000.0, '156.17B'),
            (        80000.0, '80.00K'),
            (    710000000.0, '710.00M'),
            (        0.65312, '0.65'),
            ( 553000000000.0, '553.00B'),
            (           0.04, '4.00e-2'),
            (       6.03e-05, '6.03e-5'),
            (     90300000.0, '90.30M'),
            ( 828000000000.0, '828.00B'),
            (        0.09939, '9.94e-2'),
            (      5552000.0, '5.55M'),
            (         0.0004, '4.00e-4'),
            (        10000.0, '10.00K'),
            (       513000.0, '513.00K'),
            (        0.00097, '9.70e-4'),
            (        52325.0, '52.33K'),
            (     90000000.0, '90.00M'),
            (        0.00266, '2.66e-3'),
            (       400000.0, '400.00K'),
            (    107480000.0, '107.48M'),
            (6785200000000.0, '6.79e12'),
            (     33680000.0, '33.68M'),
            (       625000.0, '625.00K'),
            (  52790000000.0, '52.79B'),
            (  51354000000.0, '51.35B'),
            (        71660.0, '71.66K'),
            (2726000000000.0, '2.73e12'),
            (          671.6, '671.60'),
            (     10000000.0, '10.00M'),
            (   3415000000.0, '3.42B'),
            (        0.00272, '2.72e-3'),
            (      3000000.0, '3.00M'),
            (      0.0004171, '4.17e-4'),
            (       0.002181, '2.18e-3'),
            (       400000.0, '400.00K'),
            (  20000000000.0, '20.00B'),
            (     1.8458e-05, '1.85e-5'),
            (       403000.0, '403.00K'),
            (       3.81e-05, '3.81e-5'),
            (          2e-05, '2.00e-5'),
            (   6800000000.0, '6.80B'),
            (1000000000000.0, '1.00e12'),
            (4405300000000.0, '4.41e12'),
            (      0.0048122, '4.81e-3'),
            (       891000.0, '891.00K'),
            (     99000000.0, '99.00M'),
            (           50.0, '50.00'),
            (          0.128, '0.13'),
            (  23440000000.0, '23.44B'),
            (        41000.0, '41.00K'),
            (7271100000000.0, '7.27e12'),
            (3230000000000.0, '3.23e12'),
            (          64.99, '64.99'),
            (    740000000.0, '740.00M'),
            (       217000.0, '217.00K'),
            (          900.0, '900.00'),
            (            6.0, '6.00'),
            (         0.7631, '0.76'),
            (           0.04, '4.00e-2'),
            (     61700000.0, '61.70M'),
            (         0.0449, '4.49e-2'),
            (    737360000.0, '737.36M'),
            (   3415000000.0, '3.42B'),
            (  81244000000.0, '81.24B'),
            (        4.9e-05, '4.90e-5'),
            (      9493000.0, '9.49M'),
            ]
        for (x, target_s) in x_s_pairs:
            self.assertEqual(prettyBigNum(x,False), target_s)
                
