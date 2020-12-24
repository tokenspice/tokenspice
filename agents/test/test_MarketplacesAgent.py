from enforce_typing import enforce_types # type: ignore[import]
import math
import pytest

from agents.MarketplacesAgent import MarketplacesAgent
from engine import SimState, SimStrategy
from util.constants import S_PER_DAY, S_PER_YEAR

@enforce_types
def test1_basic():
    a = MarketplacesAgent("mkts", 0.0, 0.0, "toll", 10.0, 0.1, 1)
    assert a.numMarketplaces() == 10.0
    assert a.revenuePerMarketplacePerSecond() == 0.1

@enforce_types
def test2_growthRatePerTick_000():
    a = MarketplacesAgent("mkts", 0.0, 0.0, "toll", 10.0, 0.1, S_PER_YEAR)
    assert a._growthRatePerTick(0.0) == 0.0
    assert a._growthRatePerTick(0.25) == 0.25

@enforce_types
def test3_growthRatePerTick_025():
    a = MarketplacesAgent("mkts", 0.0, 0.0, "toll", 10.0, 0.1, S_PER_DAY)
    assert a._growthRatePerTick(0.0) == 0.0
    assert a._growthRatePerTick(0.25) == _annualToDailyGrowthRate(0.25)

@enforce_types
def test4_takeStep():
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
    g = _annualToDailyGrowthRate(0.25)

    a.takeStep(state)
    assert a._n_marketplaces == (100.0*(1.0+g))
    assert a._revenue_per_marketplace_per_s == (2.0 * (1.0+g))
    assert a._salesPerTick() == \
        (a._n_marketplaces * a._revenue_per_marketplace_per_s * S_PER_DAY)
    expected_toll = 0.05 * a._salesPerTick()
    assert state._toll_agent.USD == (3.0 + expected_toll)

    a.takeStep(state)
    assert a._n_marketplaces == (100.0*(1.0+g)*(1.0+g))
    assert a._revenue_per_marketplace_per_s == (2.0*(1.0+g)*(1.0+g))

    for i in range(10):
        a.takeStep(state)
    assert pytest.approx(a._n_marketplaces) == 100.0*math.pow(1.0+g,1+1+10)
    assert pytest.approx(a._revenue_per_marketplace_per_s) == \
        2.0*math.pow(1.0+g,1+1+10)

@enforce_types
def _annualToDailyGrowthRate(annual_growth_rate: float) -> float:
    return math.pow(1.0 + annual_growth_rate, 1/365.0) - 1.0



