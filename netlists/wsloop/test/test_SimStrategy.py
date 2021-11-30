from enforce_typing import enforce_types
from pytest import approx

from ..SimStrategy import SimStrategy


@enforce_types
def testTotalOceanSupply():
    ss = SimStrategy()
    assert 1e6 < ss.TOTAL_OCEAN_SUPPLY < 2e9
    assert isinstance(ss.TOTAL_OCEAN_SUPPLY, float)


@enforce_types
def testFundamentalsValuation():
    ss = SimStrategy()
    assert ss._p_s_ratio == 30.0
    assert ss.fundamentalsValuation(1e3) == (1e3 * 30.0)


@enforce_types
def testBurn():
    ss = SimStrategy()
    assert hasattr(ss, "_percent_burn")
    ss._percent_burn = 0.19

    assert ss.percentToBurn() == 0.19
    assert ss.percentToOceanDao() == 0.81


@enforce_types
def testNetworkRevenue():
    ss = SimStrategy()

    assert hasattr(ss, "_percent_consume_sales_for_network")
    assert hasattr(ss, "_percent_swap_sales_for_network")
    assert hasattr(ss, "_swap_to_consume_sales_ratio")

    ss._percent_consume_sales_for_network = 0.01
    ss._percent_swap_sales_for_network = 0.02
    ss._swap_to_consume_sales_ratio = 10.0

    consume_sales = 2000.0
    target_swap_sales = 10.0 * consume_sales
    assert ss.swapSales(consume_sales) == approx(target_swap_sales)
    assert ss.totalSales(consume_sales) == approx(consume_sales + target_swap_sales)

    assert ss.networkRevenue(consume_sales) == approx(
        0.01 * consume_sales + 0.02 * target_swap_sales
    )


@enforce_types
def testTotalStaked():
    ss = SimStrategy()
    daily_consume_sales = 1000.0
    target_total_staked = ss.totalSales(daily_consume_sales)
    assert ss.totalStaked(daily_consume_sales) == approx(target_total_staked)


@enforce_types
def testAnnualMktsGrowthRate():
    ss = SimStrategy()

    assert hasattr(ss, "growth_rate_if_0_sales")
    assert hasattr(ss, "max_growth_rate")
    assert hasattr(ss, "tau")

    ss.growth_rate_if_0_sales = -0.25
    ss.max_growth_rate = 0.5
    ss.tau = 0.075

    assert ss.annualMktsGrowthRate(0.0) == -0.25
    assert ss.annualMktsGrowthRate(0.0 + 1 * ss.tau) == (-0.25 + 0.75 / 2.0)
    assert ss.annualMktsGrowthRate(0.0 + 2 * ss.tau) == (
        -0.25 + 0.75 / 2.0 + 0.75 / 4.0
    )
    assert ss.annualMktsGrowthRate(1e6) == 0.5
