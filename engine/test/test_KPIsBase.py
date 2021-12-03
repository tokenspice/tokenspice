from enforce_typing import enforce_types

from engine.KPIsBase import KPIsBase


@enforce_types
class MyKPIs(KPIsBase):
    pass


@enforce_types
def test1():
    kpis = MyKPIs(time_step=12)
    assert kpis._time_step == 12
    assert kpis.tick() == 0
    assert kpis.elapsedTime() == 0

    state = None
    kpis.takeStep(state)
    kpis.takeStep(state)

    assert kpis._tick == 2
    assert kpis.tick() == 2
    assert kpis.elapsedTime() == 2 * 12
