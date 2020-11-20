import unittest

from util.test.Constants_test import ConstantsTest
from util.test.mathutil_test import mathutilTest
from util.test.strutil_test import strutilTest
from util.test.valuation_test import valuationTest

TestClasses = [
    ConstantsTest,
    mathutilTest,
    strutilTest,
    valuationTest,
    ]

def unittest_suite():
    return unittest.TestSuite(
      [unittest.makeSuite(t,'test') for t in TestClasses]
    )    

allSuites = [
    'util.test.unittest_suite',
]

def test_suite():
    return importSuite(allSuites, globals())
