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
    assert 0.0 <= ss.OCEAN_funded <= 1e9
    assert ss.start_timestamp > 0
    assert ss.duration_seconds > 0


@enforce_types
def test_SimState():
    # import from `netlist` module
    state = netlist.SimState()

    assert len(state.agents) == 2
    assert state.getAgent("funder1").OCEAN() == state.ss.OCEAN_funded
    assert state.getAgent("beneficiary1").OCEAN() == 0.0

    state.takeStep()
    assert len(state.agents) == 3
    assert state.getAgent("vw1") is not None

    state.takeStep()


def test_KPIs():
    # import from `netlist` module
    kpis = netlist.KPIs(time_step=12)
    assert kpis.tick() == 0
    kpis.takeStep(state=None)
    kpis.takeStep(state=None)
    assert kpis.tick() == 2
    assert kpis.elapsedTime() == 12 * 2
