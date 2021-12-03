import inspect

from enforce_typing import enforce_types

from .. import netlist


def test_scope():
    netlist.SimStrategy()
    netlist.SimState()

    assert inspect.isclass(netlist.SimStrategy)
    assert inspect.isclass(netlist.SimState)
    assert inspect.isclass(netlist.KPIs)
    assert callable(netlist.netlist_createLogData)
    assert callable(netlist.netlist_plotInstructions)


@enforce_types
def test_SimStrategy():
    # import from `netlist` module, not a `SimState` module. Netlist has it all:)
    ss = netlist.SimStrategy()

    assert ss.pub_init_OCEAN > 0.0
    assert ss.OCEAN_init > 0.0
    assert ss.OCEAN_stake > 0.0

    assert ss.pub_init_OCEAN >= (ss.OCEAN_init + ss.OCEAN_stake)

    assert ss.DT_init > 0.0
    assert ss.DT_stake > 0.0
    assert ss.DT_init >= ss.DT_stake

    assert (ss.pool_weight_DT + ss.pool_weight_OCEAN) == 10.0


@enforce_types
def test_SimState():
    # import from `netlist` module
    state = netlist.SimState()

    assert len(state.agents) == 1

    assert state.getAgent("pub1").OCEAN() == state.ss.pub_init_OCEAN

    for _ in range(1000):
        state.takeStep()
        if len(state.agents) > 1:
            break

    assert len(state.agents) > 1
    pool_agents = state.agents.filterToPool()
    assert len(pool_agents) > 0


@enforce_types
def test_KPIs():
    # import from `netlist` module
    kpis = netlist.KPIs(time_step=12)

    assert kpis.tick() == 0
    kpis.takeStep(state=None)
    kpis.takeStep(state=None)
    assert kpis.tick() == 2
    assert kpis.elapsedTime() == 12 * 2
