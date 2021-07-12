from enforce_typing import enforce_types

from .. import SimState

@enforce_types
def test1():
    state = SimState.SimState()

    assert len(state.agents) == 2
    assert state.getAgent("granter1").OCEAN() == state.ss.granter_init_OCEAN
    assert state.getAgent("taker1").USD() == 0.0

    state.takeStep()
    state.takeStep()

    

    
