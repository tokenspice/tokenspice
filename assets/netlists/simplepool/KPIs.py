from enforce_typing import enforce_types
import math
from typing import List

from engine import KPIsBase
from util import valuation
from util.constants import S_PER_YEAR, S_PER_MONTH, INF
from util.strutil import prettyBigNum


@enforce_types
class KPIs(KPIsBase.KPIsBase):
    pass

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

    publisher = state.getAgent("pub1")
    s += ["; publisher OCEAN=%s" % prettyBigNum(publisher.OCEAN(),F)]
    dataheader += ["publisher_OCEAN"]
    datarow += [publisher.OCEAN()]

    pool_agents = state.agents.filterToPool()
    n_pools = len(pool_agents)
    s += ["; # pools=%d" % n_pools]
    dataheader += ["n_pools"]
    datarow += [n_pools]

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
        YParam(["publisher_OCEAN"],["OCEAN"],"publisher_OCEAN",LINEAR,MULT1,DOLLAR),
        YParam(["n_pools"],  ["# pools"],  "n_pools",  LINEAR,MULT1,COUNT)
    ]

    return (x, y_params)
