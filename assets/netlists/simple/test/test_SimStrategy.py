from enforce_typing import enforce_types

from ..SimStrategy import SimStrategy

@enforce_types
def test1():
    ss = SimStrategy()
    assert 0.0 <= ss.granter_init_USD <= 1e6
    assert 0.0 <= ss.granter_init_OCEAN <= 1e6
    assert ss.granter_s_between_grants > 0
    assert ss.granter_n_actions > 0
    
