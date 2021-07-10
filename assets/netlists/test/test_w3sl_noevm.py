from assets.netlists.w3sl_noevm import SimStrategy

def testTotalOceanSupply():
    ss = SimStrategy()
    assert 1e6 < ss.TOTAL_OCEAN_SUPPLY < 2e9
    assert isinstance(ss.TOTAL_OCEAN_SUPPLY, float)

