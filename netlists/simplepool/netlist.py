from typing import List

from enforce_typing import enforce_types

from agents import PublisherAgent
from engine import KPIsBase, SimStateBase, SimStrategyBase
from util.constants import S_PER_HOUR
from util.plotutil import YParam, arrayToFloatList, LINEAR, MULT1, COUNT, DOLLAR
from util.strutil import prettyBigNum


@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        # ==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(20, "days")

        # ==attributes specific to this netlist

        # publisher
        self.pub_init_OCEAN = 10000.0

        # pool
        self.OCEAN_init = 1000.0
        self.OCEAN_stake = 200.0
        self.DT_init = 100.0
        self.DT_stake = 20.0

        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0
        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0


@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        assert ss is None
        super().__init__(ss)

        # ss is defined in this netlist module
        self.ss = SimStrategy()

        # wire up the circuit
        pub_agent = PublisherAgent.PublisherAgent(
            name="pub1", USD=0.0, OCEAN=self.ss.pub_init_OCEAN
        )
        self.agents[pub_agent.name] = pub_agent

        # kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step)


@enforce_types
class KPIs(KPIsBase.KPIsBase):
    pass


@enforce_types
def netlist_createLogData(state):
    """SimEngine constructor uses this"""
    s = []  # for console logging
    dataheader = []  # for csv logging: list of string
    datarow = []  # for csv logging: list of float

    # SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    # So we log other things...

    publisher = state.getAgent("pub1")
    s += ["; publisher OCEAN=%s" % prettyBigNum(publisher.OCEAN(), False)]
    dataheader += ["publisher_OCEAN"]
    datarow += [publisher.OCEAN()]

    pool_agents = state.agents.filterToPool()
    n_pools = len(pool_agents)
    s += ["; # pools=%d" % n_pools]
    dataheader += ["n_pools"]
    datarow += [n_pools]

    # done
    return s, dataheader, datarow


@enforce_types
def netlist_plotInstructions(header: List[str], values):
    """
    Describe how to plot the information.
    tsp.do_plot() calls this

    :param: header: List[str] holding 'Tick', 'Second', ...
    :param: values: 2d array of float [tick_i, valuetype_i]
    :return: x_label: str -- e.g. "Day", "Month", "Year"
    :return: x: List[float] -- x-axis info on how to plot
    :return: y_params: List[YParam] -- y-axis info on how to plot
    """
    x_label = "Day"
    x = arrayToFloatList(values[:, header.index(x_label)])

    y_params = [
        YParam(
            ["publisher_OCEAN"], ["OCEAN"], "publisher_OCEAN", LINEAR, MULT1, DOLLAR
        ),
        YParam(["n_pools"], ["# pools"], "n_pools", LINEAR, MULT1, COUNT),
    ]

    return (x_label, x, y_params)
