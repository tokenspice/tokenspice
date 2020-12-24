from enforce_typing import enforce_types # type: ignore[import]

from agents import BaseAgent, GrantTakingAgent
from engine import SimState, SimStrategy

@enforce_types
def test1():
    class DummySimState:
        def __init__(self):
            pass

        def OCEANprice(self) -> float:
            return 3.0
    state = DummySimState()
    a = GrantTakingAgent.GrantTakingAgent("foo", USD=10.0, OCEAN=20.0)
    assert a._spent_at_tick == 0.0

    a.takeStep(state)
    assert a.USD() == 0.0
    assert a.OCEAN() == 0.0
    assert a._spent_at_tick == (10.0 + 20.0*3.0)

    a.takeStep(state)
    assert a._spent_at_tick == 0.0

    a.receiveUSD(5.0)
    a.takeStep(state)
    assert a._spent_at_tick == 5.0

    a.takeStep(state)
    assert a._spent_at_tick == 0.0
                  
        
                         
                         
