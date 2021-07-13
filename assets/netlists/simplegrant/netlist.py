"""
Netlist for simple grant.
"""

from enforce_typing import enforce_types
from typing import List, Set

from assets.agents import GrantGivingAgent, GrantTakingAgent
from engine import AgentBase, KPIsBase, SimStateBase, SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY
from util.strutil import prettyBigNum

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        #==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(10, 'days')

        #==attributes specific to this netlist
        self.granter_init_USD: float = 0.0
        self.granter_init_OCEAN: float = 1.0
        self.granter_s_between_grants: int = S_PER_DAY*3
        self.granter_n_actions: int = 4

@enforce_types
class SimState(SimStateBase.SimStateBase):
    
    def __init__(self, ss=None):
        #initialize self.tick, ss, agents, kpis
        assert ss is None, "simple SimState will initalize its own ss"
        super().__init__(ss)

        #now, fill in actual values for ss, agents, kpis
        self.ss = SimStrategy()
        ss = self.ss #shorter
                       
        #Instantiate and connect agent instances. "Wire up the circuit"
        new_agents: Set[AgentBase.AgentBase] = set()

        new_agents.add(GrantGivingAgent.GrantGivingAgent(
            name="granter1",
            USD=ss.granter_init_USD,
            OCEAN=ss.granter_init_OCEAN,
            receiving_agent_name="taker1",
            s_between_grants=ss.granter_s_between_grants,
            n_actions=ss.granter_n_actions))

        new_agents.add(GrantTakingAgent.GrantTakingAgent(
            name = "taker1", USD=0.0, OCEAN=0.0))

        #fill in self.agents dict
        for agent in new_agents:
            self.agents[agent.name] = agent

        #track certain metrics over time, so that we don't have to load
        self.kpis = KPIs(self.ss.time_step)
                    
    def takeStep(self) -> None:
        """This happens once per tick"""
        #update agents
        #update kpis (global state values)
        super().takeStep()

    def OCEANprice(self) -> float:
        return 1.0 #arbitrary. Need this func for GrantTakingAgent

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
