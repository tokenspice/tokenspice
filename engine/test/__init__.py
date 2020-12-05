import unittest

from engine.test.Kpis_test import KpisTest
from engine.test.SimEngine_test import SimEngineTest
from engine.test.SimState_test import SimStateTest
from engine.test.SimStrategy_test import SimStrategyTest

TestClasses = [
    KpisTest,
    SimEngineTest, 
    SimStateTest,
    SimStrategyTest,
]

def unittest_suite():
    return unittest.TestSuite(
      [unittest.makeSuite(t,'test') for t in TestClasses]
    )    

allSuites = [
    'engine.test.unittest_suite',
]

def test_suite():
    return importSuite(allSuites, globals())
