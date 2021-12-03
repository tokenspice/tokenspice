from typing import List

from enforce_typing import enforce_types

from agents import GrantGivingAgent, GrantTakingAgent
from engine import KPIsBase, SimStateBase, SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY
from util.plotutil import YParam, arrayToFloatList, LINEAR, MULT1, DOLLAR


@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        # ==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(10, "days")

        # ==attributes specific to this netlist
        self.granter_init_OCEAN: float = 1.0
        self.granter_s_between_grants: int = S_PER_DAY * 3
        self.granter_n_actions: int = 4


@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        assert ss is None
        super().__init__(ss)

        # ss is defined in this netlist module
        self.ss = SimStrategy()

        # wire up the circuit
        granter = GrantGivingAgent.GrantGivingAgent(
            name="granter1",
            USD=0.0,
            OCEAN=self.ss.granter_init_OCEAN,
            receiving_agent_name="taker1",
            s_between_grants=self.ss.granter_s_between_grants,
            n_actions=self.ss.granter_n_actions,
        )
        taker = GrantTakingAgent.GrantTakingAgent(name="taker1", USD=0.0, OCEAN=0.0)
        for agent in [granter, taker]:
            self.agents[agent.name] = agent

        # kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step)

    def OCEANprice(self) -> float:  # pylint: disable=no-self-use
        return 1.0  # arbitrary. Need GrantTakingAgent


@enforce_types
class KPIs(KPIsBase.KPIsBase):
    pass


@enforce_types
def netlist_createLogData(state):
    """SimEngine constructor uses this."""

    s = []  # for console logging
    dataheader = []  # for csv logging: list of string
    datarow = []  # for csv logging: list of float

    # SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    # So we log other things...

    g = state.getAgent("granter1")
    s += ["; granter OCEAN=%s, USD=%s" % (g.OCEAN(), g.USD())]
    dataheader += ["granter_OCEAN", "granter_USD"]
    datarow += [g.OCEAN(), g.USD()]

    # done
    return s, dataheader, datarow


@enforce_types
def netlist_plotInstructions(header: List[str], values):
    """
    Describe how to plot the information.
    tsp.do_plot() uses this.

    :param: header: List[str] holding 'Tick', 'Second', ...
    :param: values: 2d array of float [tick_i, valuetype_i]
    :return: x_label: str -- e.g. "Day", "Month", "Year"
    :return: x: List[float] -- x-axis info on how to plot
    :return: y_params: List[YParam] -- y-axis info on how to plot
    """
    x_label = "Day"
    x = arrayToFloatList(values[:, header.index(x_label)])

    y_params = [
        YParam(["granter_OCEAN"], ["OCEAN"], "granter_OCEAN", LINEAR, MULT1, DOLLAR),
        YParam(["granter_USD"], ["USD"], "granter_USD", LINEAR, MULT1, DOLLAR),
    ]

    return (x_label, x, y_params)
