from enforce_typing import enforce_types
import pytest

from engine.SimStrategyBase import SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY, S_PER_MONTH, S_PER_YEAR


@enforce_types
def test1():
    ss = SimStrategyBase()
    assert ss.time_step > 0
    assert ss.max_ticks > 0
    assert ss.log_interval > 0

    ss.setTimeStep(7)
    assert ss.time_step == 7

    assert "SimStrategy" in str(ss)

    ss.setMaxTicks(1000)
    assert ss.max_ticks == 1000

    ss.setMaxTime(100, "ticks")
    assert ss.max_ticks == 100

    ss.setMaxTime(10, "hours")
    assert ss.max_ticks == (10 * S_PER_HOUR / ss.time_step + 1)

    ss.setMaxTime(10, "days")
    assert ss.max_ticks == (10 * S_PER_DAY / ss.time_step + 1)

    ss.setMaxTime(10, "months")
    assert ss.max_ticks == (10 * S_PER_MONTH / ss.time_step + 1)

    ss.setMaxTime(10, "years")
    assert ss.max_ticks == (10 * S_PER_YEAR / ss.time_step + 1)

    ss.setLogInterval(32)
    assert ss.log_interval == 32

    with pytest.raises(ValueError):
        ss.setMaxTime(10, "foo_unit")
