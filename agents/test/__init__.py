import unittest

from agents.test.Agents_test import AgentsTest
from agents.test.BaseAgent_test import BaseAgentTest
from agents.test.MinterAgents_test import MinterAgentsTest
from agents.test.AgentWallet_test import AgentWalletTest

TestClasses = [
    AgentsTest,
    BaseAgentTest,
    MinterAgentsTest,
    AgentWalletTest,
]

def unittest_suite():
    return unittest.TestSuite(
      [unittest.makeSuite(t,'test') for t in TestClasses]
    )    

allSuites = [
    'agents.test.unittest_suite',
]

def test_suite():
    return importSuite(allSuites, globals())
