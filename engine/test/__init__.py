import unittest

from engine.test.Agents_test import AgentsTest
from engine.test.BaseAgent_test import BaseAgentTest
from engine.test.Kpis_test import KpisTest
from engine.test.MinterAgents_test import MinterAgentsTest
from engine.test.SimEngine_test import SimEngineTest
from engine.test.SimState_test import SimStateTest
from engine.test.SimStrategy_test import SimStrategyTest
from engine.test.AgentWallet_test import AgentWalletTest

TestClasses = [
    AgentsTest,
    BaseAgentTest,
    KpisTest,
    MinterAgentsTest,
    SimEngineTest, 
    SimStateTest,
    SimStrategyTest,
    AgentWalletTest,
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
