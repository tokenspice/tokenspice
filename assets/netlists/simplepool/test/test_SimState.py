from enforce_typing import enforce_types

from .. import SimState
from assets.agents.PoolAgent import PoolAgent

@enforce_types
def test1():
    state = SimState.SimState()

    assert len(state.agents) == 1
    
    assert state.getAgent("pub1").OCEAN() == state.ss.pub_init_OCEAN

    for i in range(1000):
        state.takeStep()
        if len(state.agents) > 1:
            break

    assert len(state.agents) > 1
    found_pool = False
    for agent in state.agents.values():
        found_pool = found_pool or isinstance(agent, PoolAgent)
    assert found_pool
    
