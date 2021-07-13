from enforce_typing import enforce_types

from .. import SimState

@enforce_types
def test1():
    state = SimState.SimState()

    assert len(state.agents) == 2
    
    assert state.getAgent("pub1").OCEAN() == state.ss.pub_init_OCEAN
    
    assert state.getAgent("pool1").datatoken is not None
    assert state.getAgent("pool1").pool is not None

    state.takeStep()
    state.takeStep()

    

    
