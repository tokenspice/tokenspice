import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('agents')

import enforce
import unittest

from agents import BaseAgent
from agents.Agents import *
from engine import SimState, SimStrategy
from util.constants import S_PER_DAY, S_PER_WEEK, S_PER_MONTH

@enforce.runtime_validation
class AgentsTest(unittest.TestCase):

    def testRouterAgent(self):
        #getting "tickOneMonthAgo" is tricky, so test it well
        ss = SimStrategy.SimStrategy()
        ss.time_step = S_PER_DAY
        state = SimState.SimState(ss)
        
        class SimpleAgent(BaseAgent):
            def takeStep(self, state):
                pass
        state.agents["a1"] = a1 = SimpleAgent("a1", 0.0, 0.0)
        state.agents["a2"] = a2 = SimpleAgent("a2", 0.0, 0.0)
        
        def perc_f1():
            return 0.2
        def perc_f2():
            return 0.8
        
        am = RouterAgent(
            "moneyrouter", 1.0, 10.0, {"a1" : perc_f1, "a2" : perc_f2})
        
        self.assertEqual(am._USD_per_tick, []) 
        self.assertEqual(am._OCEAN_per_tick, []) 
        self.assertEqual(am._tickOneMonthAgo(state), 0)
        self.assertEqual(am.monthlyUSDreceived(state), 0.0)
        self.assertEqual(am.monthlyOCEANreceived(state), 0.0)
        
        am.takeStep(state)
        self.assertEqual(a1.USD(), 0.2 * 1.0)
        self.assertEqual(a2.USD(), 0.8 * 1.0)
        
        self.assertEqual(a1.OCEAN(), 0.2 * 10.0)
        self.assertEqual(a2.OCEAN(), 0.8 * 10.0)
        
        self.assertEqual(am._USD_per_tick, [1.0])
        self.assertEqual(am._OCEAN_per_tick, [10.0])
        self.assertEqual(am._tickOneMonthAgo(state), 0)
        self.assertEqual(am.monthlyUSDreceived(state), 1.0)
        self.assertEqual(am.monthlyOCEANreceived(state), 10.0)
        
        am.takeStep(state)
        state.tick += 1
        am.takeStep(state)
        state.tick += 1
        
        self.assertEqual(am._USD_per_tick, [1.0, 0.0, 0.0])
        self.assertEqual(am._OCEAN_per_tick, [10.0, 0.0, 0.0])
        self.assertEqual(am._tickOneMonthAgo(state), 0)
        self.assertEqual(am.monthlyUSDreceived(state), 1.0)
        self.assertEqual(am.monthlyOCEANreceived(state), 10.0)

        #make a month pass, give $
        ticks_per_mo = int(S_PER_MONTH / float(state.ss.time_step))
        for i in range(ticks_per_mo):
            am.receiveUSD(2.0)
            am.receiveOCEAN(3.0)
            am.takeStep(state)
            state.tick += 1
        self.assertTrue(am._tickOneMonthAgo(state) > 1) #should be 2
        self.assertEqual(am.monthlyUSDreceived(state), 2.0 * ticks_per_mo)
        self.assertEqual(am.monthlyOCEANreceived(state), 3.0 * ticks_per_mo)
        
        #make another month pass, don't give $ this time
        for i in range(ticks_per_mo + 1):
            am.takeStep(state)
            state.tick += 1
        self.assertTrue(am._tickOneMonthAgo(state) > 1 + ticks_per_mo)
        self.assertEqual(am.monthlyUSDreceived(state), 0.0)
        self.assertEqual(am.monthlyOCEANreceived(state), 0.0)

    def testOCEANBurnerAgent1_fixedOCEANprice(self):
        class DummySimState:
            def __init__(self):
                self._total_OCEAN_burned: float = 0.0
                self._total_OCEAN_burned_USD: float = 0.0
                
            def OCEANprice(self) -> float:
                return 2.0
        state = DummySimState()
        a = OCEANBurnerAgent("foo", USD=10.0, OCEAN=0.0)
        
        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertEqual(state._total_OCEAN_burned_USD, 10.0)
        self.assertEqual(state._total_OCEAN_burned, 5.0)
        self.assertEqual(a.OCEAN(), 0.0)

        a.receiveUSD(20.0)
        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertEqual(state._total_OCEAN_burned_USD, 30.0)
        self.assertEqual(state._total_OCEAN_burned, 15.0)

    def testOCEANBurnerAgent2_changingOCEANprice(self):
        class DummySimState:
            def __init__(self):
                self._total_OCEAN_burned: float = 0.0
                self._total_OCEAN_burned_USD: float = 0.0
                self._initial_OCEAN: float = 100.0
                
            def OCEANprice(self) -> float:
                return self.overallValuation() / self.OCEANsupply()

            def overallValuation(self) -> float:
                return 200.0

            def OCEANsupply(self) -> float:
                return self._initial_OCEAN - self._total_OCEAN_burned
            
        state = DummySimState()
        a = OCEANBurnerAgent("foo", USD=10.0, OCEAN=0.0)
        self.assertEqual(state.OCEANprice(), 2.0) #(val 200)/(supply 100)
        
        a.takeStep(state)
        self.assertTrue(0.0 < state.OCEANsupply() < 100.0)
        self.assertTrue(state.OCEANprice() > 2.0) 
        self.assertEqual(state.OCEANprice(), 200.0 / state.OCEANsupply())
        self.assertEqual(a.USD(), 0.0)
        self.assertAlmostEqual(state._total_OCEAN_burned_USD, 10.0)
        self.assertTrue(4.0 < state._total_OCEAN_burned < 5.0) 

        price1 = state.OCEANprice()
        a.receiveUSD(20.0)
        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertTrue(state.OCEANprice() > price1)
        self.assertAlmostEqual(state._total_OCEAN_burned_USD, 30.0)
        self.assertTrue(13.0 < state._total_OCEAN_burned < 15.0)
        
    def testGrantGivingAgent(self):
        ss = SimStrategy.SimStrategy()
        assert hasattr(ss, 'time_step')
        ss.time_step = S_PER_DAY

        state = SimState.SimState(ss)
        
        class SimpleAgent(BaseAgent):
            def takeStep(self, state):
                pass
        state.agents["a1"] = a1 = SimpleAgent("a1", 0.0, 0.0)
        self.assertEqual(a1.OCEAN(), 0.0) 
        
        g1 = GrantGivingAgent(
            "g1", USD=0.0, OCEAN=1.0,
            receiving_agent_name="a1",
            s_between_grants=S_PER_DAY*3, n_actions=4)
        self.assertEqual(g1.OCEAN(), 1.0) 

        g1.takeStep(state); state.tick += 1 #tick = 1 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*1/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*1/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 2
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*1/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*1/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 3
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*1/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*1/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 4 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*2/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*2/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 5
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*2/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*2/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 6
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*2/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*2/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 7 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*3/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*3/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 8
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*3/4)
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*3/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 9
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*3/4)
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*3/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 10 #disperse here
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*4/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*4/4)
        
        g1.takeStep(state); state.tick += 1 #tick = 11
        g1.takeStep(state); state.tick += 1 #tick = 12
        g1.takeStep(state); state.tick += 1 #tick = 13 #don't disperse, 0 left
        
        self.assertEqual(g1.OCEAN(), 1.0 - 1.0*4/4) 
        self.assertEqual(a1.OCEAN(), 0.0 + 1.0*4/4)
        
    def testGrantTakingAgent(self):
        class DummySimState:
            def __init__(self):
                pass
                
            def OCEANprice(self) -> float:
                return 3.0
        state = DummySimState()
        a = GrantTakingAgent("foo", USD=10.0, OCEAN=20.0)
        self.assertEqual(a._spent_at_tick, 0.0)

        a.takeStep(state)
        self.assertEqual(a.USD(), 0.0)
        self.assertEqual(a.OCEAN(), 0.0)
        self.assertEqual(a._spent_at_tick, 10.0 + 20.0*3.0)
        
        a.takeStep(state)
        self.assertEqual(a._spent_at_tick, 0.0)

        a.receiveUSD(5.0)
        a.takeStep(state)
        self.assertEqual(a._spent_at_tick, 5.0)
        
        a.takeStep(state)
        self.assertEqual(a._spent_at_tick, 0.0)
        
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
        
                         
                         
