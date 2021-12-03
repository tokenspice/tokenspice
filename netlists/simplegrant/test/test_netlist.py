import inspect

from enforce_typing import enforce_types

from .. import netlist


@enforce_types
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
    assert 0.0 <= ss.granter_init_OCEAN <= 1e6
    assert ss.granter_s_between_grants > 0
    assert ss.granter_n_actions > 0


@enforce_types
def test_SimState():
    # import from `netlist` module
    state = netlist.SimState()

    assert len(state.agents) == 2
    assert state.getAgent("granter1").OCEAN() == state.ss.granter_init_OCEAN
    assert state.getAgent("taker1").OCEAN() == 0.0

    state.takeStep()
    state.takeStep()


def test_KPIs():
    # import from `netlist` module
    kpis = netlist.KPIs(time_step=12)
    assert kpis.tick() == 0
    kpis.takeStep(state=None)
    kpis.takeStep(state=None)
    assert kpis.tick() == 2
    assert kpis.elapsedTime() == 12 * 2
