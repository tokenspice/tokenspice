from enforce_typing import enforce_types

from engine.SimStrategyBase import SimStrategyBase

@enforce_types
def test1():
    ss = SimStrategyBase()
    assert ss.time_step > 0
    assert ss.max_ticks > 0

    ss.setTimeStep(7)
    assert ss.time_step == 7

    ss.setMaxTicks(1000)
    assert ss.max_ticks == 12

    assert "SimStrategy" in str(ss)
