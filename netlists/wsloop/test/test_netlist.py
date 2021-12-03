"""simply test for scope"""
import inspect
from .. import netlist


def test1():
    netlist.SimStrategy()
    netlist.SimState()

    assert inspect.isclass(netlist.SimStrategy)
    assert inspect.isclass(netlist.SimState)
    assert inspect.isclass(netlist.KPIs)
    assert callable(netlist.netlist_createLogData)
    assert callable(netlist.netlist_plotInstructions)
