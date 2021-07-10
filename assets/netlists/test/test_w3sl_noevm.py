from enforce_typing import enforce_types
import pytest

from assets.agents import MinterAgents
from assets.netlists.w3sl_noevm import SimStrategy, SimState, KPIs
from util.constants import S_PER_DAY

#===============================================================
#test SimStrategy
@enforce_types
def testSimStrategy__TotalOceanSupply():
    ss = SimStrategy()
    assert 1e6 < ss.TOTAL_OCEAN_SUPPLY < 2e9
    assert isinstance(ss.TOTAL_OCEAN_SUPPLY, float)
    
@enforce_types
def testSimStrategy__Basic():
    ss = SimStrategy()
    assert ss.max_ticks > 0

@enforce_types
def testSimStrategy__SetMaxTicks():
    ss = SimStrategy()
    ss.setMaxTicks(14)
    assert ss.max_ticks == 14

@enforce_types
def testSimStrategy__Str():
    ss = SimStrategy()
    assert "SimStrategy" in str(ss)

@enforce_types
def testSimStrategy__AnnualMktsGrowthRate():
    ss = SimStrategy()
    assert hasattr(ss, 'growth_rate_if_0_sales')
    assert hasattr(ss, 'max_growth_rate')
    assert hasattr(ss, 'tau')

    ss.growth_rate_if_0_sales = -0.25
    ss.max_growth_rate = 0.5
    ss.tau = 0.075

    assert ss.annualMktsGrowthRate(0.0) == -0.25
    assert ss.annualMktsGrowthRate(0.0+1*ss.tau) == (-0.25 + 0.75/2.0)
    assert ss.annualMktsGrowthRate(0.0+2*ss.tau) == \
        (-0.25 + 0.75/2.0 + 0.75/4.0)
    assert ss.annualMktsGrowthRate(1e6) == 0.5

    
#===============================================================
#test SimState

@enforce_types
def testSimState_BasicInit():
    state = SimState()
    assert isinstance(state.ss, SimStrategy)
    assert state.tick == 0

    assert state.numAgents() > 0

@enforce_types
def testSimState_GetAgent():
    state = SimState()
    assert id(state.getAgent("ocean_dao")) == id(state.agents["ocean_dao"])

@enforce_types
def testSimState_MoneyFlow1():
    state = SimState()
    assert hasattr(state, '_percent_burn')
    state._percent_burn = 0.20

    #opc_address -> (opc_burner, ocean_dao)
    state.getAgent("opc_address").receiveUSD(100.0)
    state.getAgent("opc_address").takeStep(state)
    assert state.getAgent("opc_burner").USD() == (0.20 * 100.0)
    assert state.getAgent("ocean_dao").USD() == (0.80 * 100.0)

    #ocean_dao -> opc_workers
    state.getAgent("ocean_dao").takeStep(state)
    assert state.getAgent("opc_workers").USD() == (0.80 * 100.0)

    #ocean_dao spends
    state.getAgent("opc_workers").takeStep(state)
    assert state.getAgent("opc_workers").USD() == 0.0

@enforce_types
def testSimState_MoneyFlow2():
    state = SimState()
    state.getAgent("ocean_51")._func = MinterAgents.ExpFunc(H=4.0)

    #send from money 51% minter -> ocean_dao
    o51_OCEAN_t0 = state.getAgent("ocean_51").OCEAN()
    dao_OCEAN_t0 = state.getAgent("ocean_dao").OCEAN()

    assert o51_OCEAN_t0 == 0.0
    assert dao_OCEAN_t0 == 0.0
    assert state._total_OCEAN_minted == 0.0

    #ocean_51 should disburse at tick=1
    state.getAgent("ocean_51").takeStep(state); state.tick += 1
    state.getAgent("ocean_51").takeStep(state); state.tick += 1

    o51_OCEAN_t1 = state.getAgent("ocean_51").OCEAN()
    dao_OCEAN_t1 = state.getAgent("ocean_dao").OCEAN()

    assert o51_OCEAN_t1 == 0.0 
    assert dao_OCEAN_t1 > 0.0
    assert state._total_OCEAN_minted > 0.0
    assert state._total_OCEAN_minted == dao_OCEAN_t1



#===============================================================
#test KPIs

@enforce_types
class BaseDummyMarketplacesAgent:
    def numMarketplaces(self) -> float:
        return 0.0
    def revenuePerMarketplacePerSecond(self) -> float:
        return 0.0

@enforce_types
class BaseDummySimState:
    def __init__(self):
        self._marketplaces1_agent = None
    def takeStep(state) -> None:
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

@enforce_types
def testKPIs__Ratio_happypath():
    _testKPIs_Ratio(monthly_RND=10.0, monthly_sales=20.0, target=0.5)

@enforce_types
def testKPIs__Ratio_zero_RND():
    _testKPIs_Ratio(monthly_RND=0.0, monthly_sales=20.0, target=0.0)

@enforce_types
def testKPIs__Ratio_do_not_rail_to_less_than_1():
    _testKPIs_Ratio(monthly_RND=1000.0, monthly_sales=20.0, target=50.0)

@enforce_types
def _testKPIs_Ratio(monthly_RND, monthly_sales, target):
    kpis = KPIs(time_step=1)
    kpis.grantTakersMonthlyRevenueNow = lambda : monthly_RND
    kpis.oceanMonthlyRevenueNow = lambda : monthly_sales
    assert kpis.mktsRNDToSalesRatio() == target

@enforce_types
def testKPIs_GrantTakersRevenue():        
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
    assert kpis.grantTakersMonthlyRevenueNow() == 0.0

    #tick = 1, months = 0.33
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3]
    assert pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == \
        1e3 #NOT 1e3*S_PER_DAY*10

    #tick = 2, months = 0.66
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3, 1e3]
    assert pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == \
        2e3 #NOT 2e3*S_PER_DAY*10

    #tick = 3, months = 1.00
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3, 1e3, 1e3]
    assert pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == \
        3e3 #NOT 3e3*S_PER_DAY*10

    #tick = 4, months = 1.33
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3, 1e3, 1e3, 1e3]
    assert pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == \
        3e3 #NOT 4e3. NOT 3e3*S_PER_DAY*10

    #many more steps
    for i in range(20):
        kpis.takeStep(state)
    assert pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == 3e3

@enforce_types
def testKPIs__mktsRevenueAndValuation():
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
    assert kpis.onemktMonthlyRevenueNow() == 0.0
    assert kpis.onemktAnnualRevenueNow() == 0.0
    assert kpis.onemktAnnualRevenueOneYearAgo() == 0.0

    assert kpis.allmktsMonthlyRevenueNow() == 0.0
    assert kpis.allmktsAnnualRevenueNow() == 0.0
    assert kpis.allmktsAnnualRevenueOneYearAgo() == 0.0

    assert kpis.oceanMonthlyRevenueNow() == 0.0
    assert kpis.oceanAnnualRevenueNow() == 0.0
    assert kpis.oceanAnnualRevenueOneYearAgo() == 0.0

    assert kpis.valuationPS(30.0) == 0.0

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

    assert kpis.onemktRevenuePerSecond(0) == (10.0)
    assert kpis._onemktRevenueOverInterval(0,24-1) == (240.0)
    assert kpis._onemktRevenueOverInterval(0,23-1) == (230.0)
    assert kpis._onemktRevenueOverInterval(0,23-2) == (220.0)
    assert kpis._onemktRevenueOverInterval(1,24) == (230.0)
    assert kpis._onemktRevenueOverInterval(2,24) == (220.0)

    assert kpis.allmktsRevenuePerSecond(0) == (50.0)
    assert kpis._allmktsRevenueOverInterval(0,24-1) == (5*240.0)
    assert kpis._allmktsRevenueOverInterval(0,23-1) == (5*230.0)
    assert kpis._allmktsRevenueOverInterval(1,24) == (5*230.0)

    assert kpis.oceanRevenuePerSecond(0) == (5.0)
    assert kpis._oceanRevenueOverInterval(0,24-1) == (5*24.0)
    assert kpis._oceanRevenueOverInterval(0,23-1) == (5*23.0)
    assert kpis._oceanRevenueOverInterval(1,24) == (5*23.0)

    assert kpis.onemktMonthlyRevenueNow() == (240.0) 
    assert kpis.allmktsMonthlyRevenueNow() == (1200.0)
    assert kpis.oceanMonthlyRevenueNow() == (120.0)

    #valuations
    assert kpis.valuationPS(30.0) == (120.0 * 30.0)

@enforce_types
def testKPIs__mintAndBurn():
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
    assert kpis._ticksOneMonth() == (3)

    #tick = 0, months = 0
    assert kpis.OCEANmintedPrevMonth() == 0.0
    assert kpis.OCEANburnedPrevMonth() == 0.0

    state.takeStep(); kpis.takeStep(state) #now, tick = 1, months = 0.33
    assert kpis._total_OCEAN_minted__per_tick == [2.0]
    assert kpis.OCEANmintedPrevMonth() == 2.0
    assert kpis.OCEANburnedPrevMonth() == 3.0

    state.takeStep(); kpis.takeStep(state) #now, tick = 2, months = 0.66
    assert kpis._total_OCEAN_minted__per_tick == [2.0,4.0]
    assert kpis.OCEANmintedPrevMonth() == 4.0
    assert kpis.OCEANburnedPrevMonth() == 6.0

    state.takeStep(); kpis.takeStep(state) #now, tick = 3, months = 1.0
    assert kpis._total_OCEAN_minted__per_tick == [2.0,4.0,6.0]
    assert kpis.OCEANmintedPrevMonth() == 6.0
    assert kpis.OCEANburnedPrevMonth() == 9.0

    state.takeStep(); kpis.takeStep(state) #now, tick = 4, months = 1.33
    assert kpis._total_OCEAN_minted__per_tick == [2.0,4.0,6.0,8.0]
    assert kpis.OCEANmintedPrevMonth() == 6.0 #note: NOT 8.0
    assert kpis.OCEANburnedPrevMonth() == 9.0 #note: NOT 12.0

    state.takeStep(); kpis.takeStep(state) #now, tick = 5 months = 1.66
    assert kpis._total_OCEAN_minted__per_tick == [2.0,4.0,6.0,8.0,10.0]
    assert kpis.OCEANmintedPrevMonth() == 6.0 #note: NOT 8.0
    assert kpis.OCEANburnedPrevMonth() == 9.0 #note: NOT 12.0

    #also test $ versions where OCEAN price is 4.0
    assert kpis.OCEANmintedInUSDPrevMonth() == (6.0 * 4.0)
    assert kpis.OCEANburnedInUSDPrevMonth() == (9.0 * 4.0)



