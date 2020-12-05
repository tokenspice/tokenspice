import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('agents')

import enforce
import math
import unittest

from agents.MarketplacesAgent import MarketplacesAgent
from engine import SimState, SimStrategy
from util.constants import S_PER_DAY, S_PER_YEAR

@enforce.runtime_validation
class MarketplacesAgentTest(unittest.TestCase):
        
    def testMarketplacesAgent1_basic(self):
        a = MarketplacesAgent("mkts", 0.0, 0.0, "toll", 10.0, 0.1, 1)
        self.assertEqual(a.numMarketplaces(), 10.0)
        self.assertEqual(a.revenuePerMarketplacePerSecond(), 0.1, 1.0)
        
    def testMarketplacesAgent2_growthRatePerTick_000(self):
        a = MarketplacesAgent("mkts", 0.0, 0.0, "toll", 10.0, 0.1, S_PER_YEAR)
        self.assertEqual(a._growthRatePerTick(0.0), 0.0)
        self.assertEqual(a._growthRatePerTick(0.25), 0.25)
        
    def testMarketplacesAgent3_growthRatePerTick_025(self):        
        a = MarketplacesAgent("mkts", 0.0, 0.0, "toll", 10.0, 0.1, S_PER_DAY)
        self.assertEqual(a._growthRatePerTick(0.0), 0.0)
        self.assertEqual(a._growthRatePerTick(0.25),
                         self._annualToDailyGrowthRate(0.25))
        
    def testMarketplacesAgent4_takeStep(self):
        class DummyTollAgent:
            def __init__(self):
                self.USD = 3.0
            def receiveUSD(self, USD):
                self.USD += USD
                
        class DummyKpis:
            def mktsRNDToSalesRatio(self):
                return 0.0
            
        class DummySS:
            def __init__(self):
                self.time_step = S_PER_DAY
            def annualMktsGrowthRate(self, dummy_ratio):
                return 0.25
                
        class DummySimState:
            def __init__(self):
                self.kpis, self.ss = DummyKpis(), DummySS()
                self._toll_agent = DummyTollAgent()
            def marketplacePercentTollToOcean(self) -> float:
                return 0.05
            def getAgent(self, name: str):
                assert name == "toll_agent"
                return self._toll_agent
                
        state = DummySimState()        
        a = MarketplacesAgent(name="marketplaces", USD=10.0, OCEAN=20.0,
                              toll_agent_name="toll_agent",
                              n_marketplaces=100.0,
                              revenue_per_marketplace_per_s=2.0,
                              time_step=state.ss.time_step)
        g = self._annualToDailyGrowthRate(0.25)
        
        a.takeStep(state)
        self.assertEqual(a._n_marketplaces, 100.0*(1.0+g))
        self.assertEqual(a._revenue_per_marketplace_per_s, 2.0 * (1.0+g))
        self.assertEqual(
            a._salesPerTick(),
            a._n_marketplaces * a._revenue_per_marketplace_per_s * S_PER_DAY)
        expected_toll = 0.05 * a._salesPerTick()
        self.assertEqual(state._toll_agent.USD, 3.0 + expected_toll)
        
        a.takeStep(state)
        self.assertEqual(a._n_marketplaces, 100.0*(1.0+g)*(1.0+g))
        self.assertEqual(a._revenue_per_marketplace_per_s, 2.0*(1.0+g)*(1.0+g))

        for i in range(10):
            a.takeStep(state)
        self.assertAlmostEqual(a._n_marketplaces,
                               100.0*math.pow(1.0+g,1+1+10))
        self.assertAlmostEqual(a._revenue_per_marketplace_per_s,
                               2.0*math.pow(1.0+g,1+1+10))
                         
    def _annualToDailyGrowthRate(self, annual_growth_rate: float) -> float:
        return math.pow(1.0 + annual_growth_rate, 1/365.0) - 1.0
        
                         
                         
