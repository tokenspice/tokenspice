import pytest

from enforce_typing import enforce_types

from util.constants import S_PER_DAY
from ..KPIs import KPIs


@enforce_types
class DummySS:
    def __init__(self, time_step: int):
        self.time_step: int = time_step

        self._percent_consume_sales_for_network = 0.10

    def networkRevenue(self, consume_sales: float) -> float:
        # NOTE: this dummy SS is simplistic, ignoring swap revenue. That's ok
        # here since it's tested elsewhere
        return consume_sales * self._percent_consume_sales_for_network


@enforce_types
class BaseDummyMarketplacesAgent:
    def numMarketplaces(self) -> float:  # pylint: disable=no-self-use
        return 0.0

    def consumeSalesPerMarketplacePerSecond(  # pylint: disable=no-self-use
        self,
    ) -> float:
        return 0.0


@enforce_types
class BaseDummySimState:
    def __init__(self):
        self._marketplaces1_agent = None

    def takeStep(self) -> None:  # pylint: disable=no-self-use
        pass

    def getAgent(self, name: str):  # pylint: disable=unused-argument
        return self._marketplaces1_agent

    def grantTakersSpentAtTick(self) -> float:  # pylint: disable=no-self-use
        return 0.0

    def OCEANprice(self) -> float:  # pylint: disable=no-self-use
        return 0.0

    def totalOCEANminted(self) -> float:  # pylint: disable=no-self-use
        return 0.0

    def totalOCEANburned(self) -> float:  # pylint: disable=no-self-use
        return 0.0

    def totalOCEANburnedUSD(self) -> float:  # pylint: disable=no-self-use
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
    ss = DummySS(time_step=1)
    kpis = KPIs(ss)
    kpis.grantTakersMonthlyRevenueNow = lambda: monthly_RND
    kpis.monthlyNetworkRevenueNow = lambda: monthly_sales
    assert kpis.mktsRNDToSalesRatio() == target


@enforce_types
def testKPIs_GrantTakersRevenue():
    class DummySimState(BaseDummySimState):
        def __init__(self):
            super().__init__()
            self.ss = DummySS(time_step=S_PER_DAY * 10)  # 1 tick = 10/30 = 0.33 mos
            self._marketplaces1_agent = BaseDummyMarketplacesAgent()

        def grantTakersSpentAtTick(self):
            return 1e3

    state = DummySimState()
    kpis = KPIs(state.ss)

    # tick = 0, months = 0
    assert kpis.grantTakersMonthlyRevenueNow() == 0.0

    # tick = 1, months = 0.33
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3]
    assert (
        pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == 1e3
    )  # NOT 1e3*S_PER_DAY*10

    # tick = 2, months = 0.66
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3, 1e3]
    assert (
        pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == 2e3
    )  # NOT 2e3*S_PER_DAY*10

    # tick = 3, months = 1.00
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3, 1e3, 1e3]
    assert (
        pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == 3e3
    )  # NOT 3e3*S_PER_DAY*10

    # tick = 4, months = 1.33
    kpis.takeStep(state)
    assert kpis._granttakers_revenue_per_tick__per_tick == [1e3, 1e3, 1e3, 1e3]
    assert (
        pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == 3e3
    )  # NOT 4e3. NOT 3e3*S_PER_DAY*10

    # many more steps
    for _ in range(20):
        kpis.takeStep(state)
    assert pytest.approx(kpis.grantTakersMonthlyRevenueNow()) == 3e3


@enforce_types
def testKPIs__mktsConsumeSalesAndValuation():
    class DummyMarketplacesAgent(BaseDummyMarketplacesAgent):
        def numMarketplaces(self) -> float:
            return 5.0

        def consumeSalesPerMarketplacePerSecond(self) -> float:
            return 10.0

    class DummySimState(BaseDummySimState):
        def __init__(self):
            super().__init__()
            self._marketplaces1_agent = DummyMarketplacesAgent()
            self.ss = DummySS(time_step=3)

    state = DummySimState()
    kpis = KPIs(state.ss)

    # base case - no time passed
    assert kpis.onemktMonthlyConsumeSalesNow() == 0.0
    assert kpis.onemktAnnualConsumeSalesNow() == 0.0
    assert kpis.onemktAnnualConsumeSalesOneYearAgo() == 0.0

    assert kpis.allmktsMonthlyConsumeSalesNow() == 0.0
    assert kpis.allmktsAnnualConsumeSalesNow() == 0.0
    assert kpis.allmktsAnnualConsumeSalesOneYearAgo() == 0.0

    assert kpis.monthlyNetworkRevenueNow() == 0.0
    assert kpis.annualNetworkRevenueNow() == 0.0
    assert kpis.oceanAnnualRevenueOneYearAgo() == 0.0

    # let time pass
    for _ in range(8):
        kpis.takeStep(state)

    # key numbers:
    #  sales_per_marketplace_per_s = 10.0
    #  n_marketplaces = 5
    #  marketplace_percent_toll_to_network = 0.10
    #  time_step = 3 (seconds per tick)
    #  num time steps = num elapsed ticks = 8
    #  elapsed time = 8 * 3 = 24
    #
    # therefore, for the elapsed time period
    #  rev one mkt = 10 * 24 = 240
    #  rev all mkts = 10 * 24 * 5 = 1200
    #  rev ocean = 10 * 24 * 5 * 0.10 = 120

    assert kpis.onemktConsumeSalesPerSecond(0) == (10.0)
    assert kpis._onemktConsumeSalesOverInterval(0, 24 - 1) == (240.0)
    assert kpis._onemktConsumeSalesOverInterval(0, 23 - 1) == (230.0)
    assert kpis._onemktConsumeSalesOverInterval(0, 23 - 2) == (220.0)
    assert kpis._onemktConsumeSalesOverInterval(1, 24) == (230.0)
    assert kpis._onemktConsumeSalesOverInterval(2, 24) == (220.0)

    assert kpis.allmktsConsumeSalesPerSecond(0) == (50.0)
    assert kpis._allmktsConsumeSalesOverInterval(0, 24 - 1) == (5 * 240.0)
    assert kpis._allmktsConsumeSalesOverInterval(0, 23 - 1) == (5 * 230.0)
    assert kpis._allmktsConsumeSalesOverInterval(1, 24) == (5 * 230.0)

    assert kpis.networkRevenuePerSecond(0) == (5.0)
    assert kpis._networkRevenueOverInterval(0, 24 - 1) == (5 * 24.0)
    assert kpis._networkRevenueOverInterval(0, 23 - 1) == (5 * 23.0)
    assert kpis._networkRevenueOverInterval(1, 24) == (5 * 23.0)

    assert kpis.onemktMonthlyConsumeSalesNow() == (240.0)
    assert kpis.allmktsMonthlyConsumeSalesNow() == (1200.0)
    assert kpis.monthlyNetworkRevenueNow() == (120.0)


@enforce_types
def testKPIs__mintAndBurn():
    class DummyMarketplacesAgent(BaseDummyMarketplacesAgent):
        def numMarketplaces(self) -> float:
            return 0.0

        def consumeSalesPerMarketplacePerSecond(self) -> float:
            return 0.0

    class DummySimState(BaseDummySimState):
        def __init__(self):
            super().__init__()
            self.ss = DummySS(time_step=S_PER_DAY * 10)
            self._marketplaces1_agent = DummyMarketplacesAgent()

            self._total_OCEAN_minted = 0.0
            self._total_OCEAN_burned = 0.0
            self._total_OCEAN_burned_USD = 0.0

        def takeStep(self):
            self._total_OCEAN_minted += 2.0
            self._total_OCEAN_burned += 3.0
            self._total_OCEAN_burned_USD += 3.0 * self.OCEANprice()

        def OCEANprice(self):
            return 4.0

        def totalOCEANminted(self) -> float:
            return self._total_OCEAN_minted

        def totalOCEANburned(self) -> float:
            return self._total_OCEAN_burned

        def totalOCEANburnedUSD(self) -> float:
            return self._total_OCEAN_burned_USD

    state = DummySimState()
    kpis = KPIs(state.ss)
    assert kpis._ticksOneMonth() == (3)

    # tick = 0, months = 0
    assert kpis.OCEANmintedPrevMonth() == 0.0
    assert kpis.OCEANburnedPrevMonth() == 0.0

    state.takeStep()
    kpis.takeStep(state)  # now, tick = 1, months = 0.33
    assert kpis._total_OCEAN_minted__per_tick == [2.0]
    assert kpis.OCEANmintedPrevMonth() == 2.0
    assert kpis.OCEANburnedPrevMonth() == 3.0

    state.takeStep()
    kpis.takeStep(state)  # now, tick = 2, months = 0.66
    assert kpis._total_OCEAN_minted__per_tick == [2.0, 4.0]
    assert kpis.OCEANmintedPrevMonth() == 4.0
    assert kpis.OCEANburnedPrevMonth() == 6.0

    state.takeStep()
    kpis.takeStep(state)  # now, tick = 3, months = 1.0
    assert kpis._total_OCEAN_minted__per_tick == [2.0, 4.0, 6.0]
    assert kpis.OCEANmintedPrevMonth() == 6.0
    assert kpis.OCEANburnedPrevMonth() == 9.0

    state.takeStep()
    kpis.takeStep(state)  # now, tick = 4, months = 1.33
    assert kpis._total_OCEAN_minted__per_tick == [2.0, 4.0, 6.0, 8.0]
    assert kpis.OCEANmintedPrevMonth() == 6.0  # note: NOT 8.0
    assert kpis.OCEANburnedPrevMonth() == 9.0  # note: NOT 12.0

    state.takeStep()
    kpis.takeStep(state)  # now, tick = 5 months = 1.66
    assert kpis._total_OCEAN_minted__per_tick == [2.0, 4.0, 6.0, 8.0, 10.0]
    assert kpis.OCEANmintedPrevMonth() == 6.0  # note: NOT 8.0
    assert kpis.OCEANburnedPrevMonth() == 9.0  # note: NOT 12.0

    # also test $ versions where OCEAN price is 4.0
    assert kpis.OCEANmintedInUSDPrevMonth() == (6.0 * 4.0)
    assert kpis.OCEANburnedInUSDPrevMonth() == (9.0 * 4.0)
