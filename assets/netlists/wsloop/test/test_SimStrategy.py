from enforce_typing import enforce_types

from ..SimStrategy import SimStrategy

@enforce_types
def testTotalOceanSupply():
    ss = SimStrategy()
    assert 1e6 < ss.TOTAL_OCEAN_SUPPLY < 2e9
    assert isinstance(ss.TOTAL_OCEAN_SUPPLY, float)
    

@enforce_types
def testAnnualMktsGrowthRate():
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
