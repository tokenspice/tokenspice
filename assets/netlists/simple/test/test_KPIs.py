from enforce_typing import enforce_types
import pytest

from .. import KPIs
from util.constants import S_PER_DAY

def test1():
    kpis = KPIs.KPIs(time_step=12)
    assert kpis.tick() == 0
    kpis.takeStep(state=None)
    kpis.takeStep(state=None)
    assert kpis.tick() == 2
    assert kpis.elapsedTime() == 12*2
    
