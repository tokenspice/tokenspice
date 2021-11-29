"""simply test for scope"""
import inspect
from .. import netlist


def test1():
    # example usage
    ss = netlist.SimStrategy()
    ss = netlist.SimState()

    # test that it's all there
    assert inspect.isclass(netlist.SimStrategy)
    assert inspect.isclass(netlist.SimState)
    assert inspect.isclass(netlist.KPIs)
    assert callable(netlist.netlist_createLogData)
    assert callable(netlist.netlist_plotInstructions)
