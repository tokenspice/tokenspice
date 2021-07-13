from enforce_typing import enforce_types
import math
from typing import List

from engine import KPIsBase
from util import valuation
from util.constants import S_PER_YEAR, S_PER_MONTH, INF
from util.strutil import prettyBigNum

@enforce_types
class KPIs(KPIsBase.KPIsBase):

    def __init__(self, time_step: int):
        super().__init__(time_step)
        self._tick = 0

    def takeStep(self, state):
        self._tick += 1
    
    def tick(self) -> int:
        """# ticks that have elapsed since the beginning of the run"""
        return self._tick

@enforce_types
def netlist_createLogData(state):
    """pass this to SimEngine.__init__() as argument `netlist_createLogData`"""
    F = False
    ss = state.ss
    kpis = state.kpis

    s = [] #for console logging
    dataheader = [] # for csv logging: list of string
    datarow = [] #for csv logging: list of float

    #SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    #So we log other things...

    g = state.getAgent("granter1")
    s += ["; granter OCEAN=%s, USD=%s" %
          (prettyBigNum(g.OCEAN(),F), prettyBigNum(g.USD(), F))]
    dataheader += ["granter_OCEAN", "granter_USD"]
    datarow += [g.OCEAN(), g.USD()]

    #done
    return s, dataheader, datarow

@enforce_types
def netlist_plotInstructions(header: List[str], values):
    """
    Describe how to plot the information.
    tsp.do_plot() calls this

    :param: header: List[str] holding 'Tick', 'Second', ...
    :param: values: 2d array of float [tick_i, valuetype_i]
    :return: x: List[float] -- x-axis info on how to plot
    :return: y_params: List[YParam] -- y-axis info on how to plot
    """
    from util.plotutil import YParam, arrayToFloatList, \
        LINEAR, LOG, BOTH, MULT1, MULT100, DIV1M, DIV1B, COUNT, DOLLAR, PERCENT
    
    x = arrayToFloatList(values[:,header.index("Day")])
    
    y_params = [
        YParam(["granter_OCEAN"],["OCEAN"],"granter_OCEAN",LINEAR,MULT1,DOLLAR),
        YParam(["granter_USD"],  ["USD"],  "granter_USD",  LINEAR,MULT1,DOLLAR)
    ]

    return (x, y_params)
