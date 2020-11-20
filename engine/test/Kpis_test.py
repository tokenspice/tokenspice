import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('kpis')

import enforce
import unittest

from engine.Kpis import KPIs
from engine.SimStrategy import SimStrategy
from util.constants import S_PER_DAY
    
@enforce.runtime_validation
class BaseDummyMarketplacesAgent:
    def numMarketplaces(self) -> float:
        return 0.0
    def revenuePerMarketplacePerSecond(self) -> float:
        return 0.0

@enforce.runtime_validation
class BaseDummySimState:
    def __init__(self):
        self._marketplaces1_agent = None
    def takeStep() -> None:
        pass
    def getAgent(self, name: str):
        return self._marketplaces1_agent    
    def marketplacePercentTollToOcean(self) -> float:
        return 0.0
    def grantTakersSpentAtTick(self) -> float:
        return 0.0
    def OCEANprice(self) -> float:
        return 0.0
    def totalOCEANminted(self) -> float:
        return 0.0
    def totalOCEANburned(self) -> float:
        return 0.0
    def totalOCEANburnedUSD(self) -> float:
        return 0.0

@enforce.runtime_validation
class KpisTest(unittest.TestCase):
    
    def testRatio(self):
        #happy path
        self._testRatio(monthly_RND=10.0, monthly_sales=20.0, target=0.5)

        #special case: R&D budget is 0
        self._testRatio(monthly_RND=0.0, monthly_sales=20.0, target=0.0)

        #special case: do *not* rail to <= 1.0?
        self._testRatio(monthly_RND=1000.0, monthly_sales=20.0, target=50.0)

    def _testRatio(self, monthly_RND, monthly_sales, target):
        kpis = KPIs(time_step=1)
        kpis.grantTakersMonthlyRevenueNow = lambda : monthly_RND
        kpis.oceanMonthlyRevenueNow = lambda : monthly_sales
        self.assertEqual(kpis.mktsRNDToSalesRatio(), target)
        
    def testGrantTakersRevenue(self):        
        class DummySimState(BaseDummySimState):
            def __init__(self, ss):
                self.ss = ss
                self._marketplaces1_agent = BaseDummyMarketplacesAgent()
            def grantTakersSpentAtTick(self):
                return 1e3
                
        class DummySS:
            def __init__(self):
                self.time_step = S_PER_DAY*10 #1 tick = 10/30 = 0.33 mos
        
        ss = DummySS()
        state = DummySimState(ss)
        kpis = KPIs(time_step=ss.time_step)

        #tick = 0, months = 0     
        self.assertEqual(kpis.grantTakersMonthlyRevenueNow(), 0.0)
        
        #tick = 1, months = 0.33
        kpis.takeStep(state)
        self.assertEqual(kpis._granttakers_revenue_per_tick__per_tick,
                        [1e3])
        self.assertAlmostEqual(kpis.grantTakersMonthlyRevenueNow(),
                               1e3) #NOT 1e3*S_PER_DAY*10
        
        #tick = 2, months = 0.66
        kpis.takeStep(state)
        self.assertEqual(kpis._granttakers_revenue_per_tick__per_tick,
                         [1e3, 1e3])
        self.assertAlmostEqual(kpis.grantTakersMonthlyRevenueNow(),
                               2e3) #NOT 2e3*S_PER_DAY*10
        
        #tick = 3, months = 1.00
        kpis.takeStep(state)
        self.assertEqual(kpis._granttakers_revenue_per_tick__per_tick,
                         [1e3, 1e3, 1e3])
        self.assertAlmostEqual(kpis.grantTakersMonthlyRevenueNow(),
                               3e3) #NOT 3e3*S_PER_DAY*10
        
        #tick = 4, months = 1.33
        kpis.takeStep(state)
        self.assertEqual(kpis._granttakers_revenue_per_tick__per_tick,
                         [1e3, 1e3, 1e3, 1e3])
        self.assertAlmostEqual(kpis.grantTakersMonthlyRevenueNow(),
                               3e3) #NOT 4e3. NOT 3e3*S_PER_DAY*10

        #many more steps
        for i in range(20):
            kpis.takeStep(state)
        self.assertAlmostEqual(kpis.grantTakersMonthlyRevenueNow(),
                               3e3)

    def test_mktsRevenueAndValuation(self):
        class DummyMarketplacesAgent(BaseDummyMarketplacesAgent):
            def numMarketplaces(self) -> float:
                return 5.0
    
            def revenuePerMarketplacePerSecond(self) -> float:
                return 10.0
        
        class DummySimState(BaseDummySimState):
            def __init__(self):
                self._marketplaces1_agent = DummyMarketplacesAgent()

            def marketplacePercentTollToOcean(self) -> float:
                return 0.10

        state = DummySimState()
        kpis = KPIs(time_step=3)

        #base case - no time passed        
        self.assertEqual(kpis.onemktMonthlyRevenueNow(), 0.0)
        self.assertEqual(kpis.onemktAnnualRevenueNow(), 0.0)
        self.assertEqual(kpis.onemktAnnualRevenueOneYearAgo(), 0.0)
        
        self.assertEqual(kpis.allmktsMonthlyRevenueNow(), 0.0)
        self.assertEqual(kpis.allmktsAnnualRevenueNow(), 0.0)
        self.assertEqual(kpis.allmktsAnnualRevenueOneYearAgo(), 0.0)
        
        self.assertEqual(kpis.oceanMonthlyRevenueNow(), 0.0)
        self.assertEqual(kpis.oceanAnnualRevenueNow(), 0.0)
        self.assertEqual(kpis.oceanAnnualRevenueOneYearAgo(), 0.0)
        
        self.assertEqual(kpis.valuationPS(30.0), 0.0)

        #let time pass
        for i in range(8): 
            kpis.takeStep(state)

        #key numbers:
        #  revenue_per_marketplace_per_s = 10.0 
        #  n_marketplaces = 5
        #  marketplace_percent_toll_to_ocean = 0.10
        #  time_step = 3 (seconds per tick)
        #  num time steps = num elapsed ticks = 8
        #  elapsed time = 8 * 3 = 24
        #
        #therefore, for the elapsed time period
        #  rev one mkt = 10 * 24 = 240
        #  rev all mkts = 10 * 24 * 5 = 1200
        #  rev ocean = 10 * 24 * 5 * 0.10 = 120

        self.assertEqual(kpis.onemktRevenuePerSecond(0), 10.0)
        self.assertEqual(kpis._onemktRevenueOverInterval(0,24-1), 240.0)
        self.assertEqual(kpis._onemktRevenueOverInterval(0,23-1), 230.0)
        self.assertEqual(kpis._onemktRevenueOverInterval(0,23-2), 220.0)
        self.assertEqual(kpis._onemktRevenueOverInterval(1,24), 230.0)
        self.assertEqual(kpis._onemktRevenueOverInterval(2,24), 220.0)
        
        self.assertEqual(kpis.allmktsRevenuePerSecond(0), 50.0)
        self.assertEqual(kpis._allmktsRevenueOverInterval(0,24-1), 5*240.0)
        self.assertEqual(kpis._allmktsRevenueOverInterval(0,23-1), 5*230.0)
        self.assertEqual(kpis._allmktsRevenueOverInterval(1,24), 5*230.0)
        
        self.assertEqual(kpis.oceanRevenuePerSecond(0), 5.0)
        self.assertEqual(kpis._oceanRevenueOverInterval(0,24-1), 5*24.0)
        self.assertEqual(kpis._oceanRevenueOverInterval(0,23-1), 5*23.0)
        self.assertEqual(kpis._oceanRevenueOverInterval(1,24), 5*23.0)
        
        self.assertEqual(kpis.onemktMonthlyRevenueNow(), 240.0) 
        self.assertEqual(kpis.allmktsMonthlyRevenueNow(), 1200.0)
        self.assertEqual(kpis.oceanMonthlyRevenueNow(), 120.0)

        #valuations
        self.assertEqual(kpis.valuationPS(30.0), 120.0 * 30.0)
        
    def test_mintAndBurn(self):
        class DummyMarketplacesAgent(BaseDummyMarketplacesAgent):
            def numMarketplaces(self) -> float:
                return 0.0
    
            def revenuePerMarketplacePerSecond(self) -> float:
                return 0.0
        
        class DummySimState(BaseDummySimState):
            def __init__(self):
                self._marketplaces1_agent = DummyMarketplacesAgent()
                
                self._total_OCEAN_minted = 0.0
                self._total_OCEAN_burned = 0.0
                self._total_OCEAN_burned_USD = 0.0

            def takeStep(self):
                self._total_OCEAN_minted += 2.0
                self._total_OCEAN_burned += 3.0
                self._total_OCEAN_burned_USD += (3.0 * self.OCEANprice())

            def OCEANprice(self):
                return 4.0

            def totalOCEANminted(self) -> float:
                return self._total_OCEAN_minted
            
            def totalOCEANburned(self) -> float:
                return self._total_OCEAN_burned
            
            def totalOCEANburnedUSD(self) -> float:
                return self._total_OCEAN_burned_USD
            
        state = DummySimState()
        kpis = KPIs(time_step=S_PER_DAY*10) #1 tick = 10/30 = 0.33 mos
        self.assertEqual(kpis._ticksOneMonth(), 3)

        #tick = 0, months = 0
        self.assertEqual(kpis.OCEANmintedPrevMonth(), 0.0)
        self.assertEqual(kpis.OCEANburnedPrevMonth(), 0.0)

        state.takeStep(); kpis.takeStep(state) #now, tick = 1, months = 0.33
        self.assertEqual(kpis._total_OCEAN_minted__per_tick, [2.0])
        self.assertEqual(kpis.OCEANmintedPrevMonth(), 2.0)
        self.assertEqual(kpis.OCEANburnedPrevMonth(), 3.0)

        state.takeStep(); kpis.takeStep(state) #now, tick = 2, months = 0.66
        self.assertEqual(kpis._total_OCEAN_minted__per_tick, [2.0,4.0])
        self.assertEqual(kpis.OCEANmintedPrevMonth(), 4.0)
        self.assertEqual(kpis.OCEANburnedPrevMonth(), 6.0)

        state.takeStep(); kpis.takeStep(state) #now, tick = 3, months = 1.0
        self.assertEqual(kpis._total_OCEAN_minted__per_tick, [2.0,4.0,6.0])
        self.assertEqual(kpis.OCEANmintedPrevMonth(), 6.0)
        self.assertEqual(kpis.OCEANburnedPrevMonth(), 9.0)

        state.takeStep(); kpis.takeStep(state) #now, tick = 4, months = 1.33
        self.assertEqual(kpis._total_OCEAN_minted__per_tick, [2.0,4.0,6.0,8.0])
        self.assertEqual(kpis.OCEANmintedPrevMonth(), 6.0) #note: NOT 8.0
        self.assertEqual(kpis.OCEANburnedPrevMonth(), 9.0) #note: NOT 12.0

        state.takeStep(); kpis.takeStep(state) #now, tick = 5 months = 1.66
        self.assertEqual(kpis._total_OCEAN_minted__per_tick,
                         [2.0,4.0,6.0,8.0,10.0])
        self.assertEqual(kpis.OCEANmintedPrevMonth(), 6.0) #note: NOT 8.0
        self.assertEqual(kpis.OCEANburnedPrevMonth(), 9.0) #note: NOT 12.0

        #also test $ versions where OCEAN price is 4.0
        self.assertEqual(kpis.OCEANmintedInUSDPrevMonth(), 6.0 * 4.0)
        self.assertEqual(kpis.OCEANburnedInUSDPrevMonth(), 9.0 * 4.0)
        
        
