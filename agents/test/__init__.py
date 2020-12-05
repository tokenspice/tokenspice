import unittest

from agents.test.AgentWallet_test import AgentWalletTest
from agents.test.BaseAgent_test import BaseAgentTest
from agents.test.GrantGivingAgent_test import GrantGivingAgentTest
from agents.test.GrantTakingAgent_test import GrantTakingAgentTest
from agents.test.MarketplacesAgent_test import MarketplacesAgentTest
from agents.test.MinterAgents_test import MinterAgentsTest
from agents.test.OCEANBurnerAgent_test import OCEANBurnerAgentTest
from agents.test.RouterAgent_test import RouterAgentTest

TestClasses = [
    AgentWalletTest,
    BaseAgentTest,
    GrantGivingAgentTest,
    GrantTakingAgentTest,
    MarketplacesAgentTest,
    MinterAgentsTest,
    OCEANBurnerAgentTest,
    RouterAgentTest,
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
