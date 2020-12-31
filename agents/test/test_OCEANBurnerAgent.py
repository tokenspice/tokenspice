from enforce_typing import enforce_types # type: ignore[import]
import pytest

from agents import BaseAgent, OCEANBurnerAgent
from engine import SimState, SimStrategy

@enforce_types
def test_fixedOCEANprice():
    class DummySimState:
        def __init__(self):
            self._total_OCEAN_burned: float = 0.0
            self._total_OCEAN_burned_USD: float = 0.0

        def OCEANprice(self) -> float:
            return 2.0
    state = DummySimState()
    a = OCEANBurnerAgent.OCEANBurnerAgent("foo", USD=10.0, OCEAN=0.0)

    a.takeStep(state)
    assert a.USD() == 0.0
    assert state._total_OCEAN_burned_USD, 10.0
    assert state._total_OCEAN_burned == 5.0
    assert a.OCEAN() == 0.0

    a.receiveUSD(20.0)
    a.takeStep(state)
    assert a.USD() == 0.0
    assert state._total_OCEAN_burned_USD == 30.0
    assert state._total_OCEAN_burned == 15.0

@enforce_types
def test_changingOCEANprice():
    class DummySimState:
        def __init__(self):
            self._total_OCEAN_burned: float = 0.0
            self._total_OCEAN_burned_USD: float = 0.0
            self._initial_OCEAN: float = 100.0

        def OCEANprice(self) -> float:
            return self.overallValuation() / self.OCEANsupply()

        def overallValuation(self) -> float:
            return 200.0

        def OCEANsupply(self) -> float:
            return self._initial_OCEAN - self._total_OCEAN_burned

    state = DummySimState()
    a = OCEANBurnerAgent.OCEANBurnerAgent("foo", USD=10.0, OCEAN=0.0)
    assert state.OCEANprice() == 2.0 #(val 200)/(supply 100)

    a.takeStep(state)
    assert 0.0 < state.OCEANsupply() < 100.0
    assert state.OCEANprice() > 2.0 
    assert state.OCEANprice() == 200.0 / state.OCEANsupply()
    assert a.USD() == 0.0
    assert pytest.approx(state._total_OCEAN_burned_USD) == 10.0
    assert 4.0 < state._total_OCEAN_burned < 5.0 

    price1 = state.OCEANprice()
    a.receiveUSD(20.0)
    a.takeStep(state)
    assert a.USD() == 0.0
    assert state.OCEANprice() > price1
    assert pytest.approx(state._total_OCEAN_burned_USD) == 30.0
    assert 13.0 < state._total_OCEAN_burned < 15.0
        
                          
                         
                         
