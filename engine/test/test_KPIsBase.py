from enforce_typing import enforce_types

from engine.KPIsBase import KPIsBase

class MyKPIs(KPIsBase):
    def __init__(self, time_step: int):
        super().__init__(time_step)
        self.vals = []

    def takeStep(self, state):
        self.vals.append(31.6) #arbitrary value each tick

    def tick(self):
        """# ticks that have elapsed since the beginning of the run"""
        return len(self.vals)

def test1():
    kpis = MyKPIs(time_step=12)
    assert kpis._time_step == 12
    assert kpis.tick() == 0
    assert kpis.elapsedTime() == 0

    state = None
    kpis.takeStep(state)
    kpis.takeStep(state)

    assert kpis.tick() == 2
    assert kpis.elapsedTime() == 2 * 12
