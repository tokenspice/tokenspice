from enforce_typing import enforce_types

from ..SimStrategy import SimStrategy

@enforce_types
def test1():
    ss = SimStrategy()

    assert ss.pub_init_OCEAN > 0.0
    assert ss.OCEAN_init > 0.0
    assert ss.OCEAN_stake > 0.0

    assert ss.pub_init_OCEAN >= (ss.OCEAN_init + ss.OCEAN_stake)
    
    assert ss.DT_init > 0.0
    assert ss.DT_stake > 0.0
    assert ss.DT_init >= ss.DT_stake

    assert (ss.pool_weight_DT + ss.pool_weight_OCEAN) == 10.0
