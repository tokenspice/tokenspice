import brownie
from enforce_typing import enforce_types
from typing import List, Set

from assets.agents import GrantGivingAgent, GrantTakingAgent
from engine import KPIsBase, SimStateBase, SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        #==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(10, 'days')

        #==attributes specific to this netlist
        self.OCEAN_funded: float = 1.0
        self.start_timestamp: int = brownie.network.chain.time() + 5
        self.duration_seconds: int = 30

@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        assert ss is None
        super().__init__(ss)

        #ss is defined in this netlist module
        self.ss = SimStrategy()

        #wire up the circuit
        funder = VestingFunderAgent.VestingFunderAgent(
            name = "funder1",
            USD = 0.0,
            OCEAN = self.ss.OCEAN_funded,
            beneficiary_agent_name = "beneficiary1",
            start_timestamp = self.ss.start_timestamp,
            duration_seconds = self.ss.duration_seconds)
        beneficary = VestingBeneficiaryAgent.VestingBeneficiaryAgent(
            name = "beneficiary1", USD=0.0, OCEAN=0.0)
        for agent in [funder, beneficiary]:
            self.agents[agent.name] = agent

        #kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step) 
                
    def OCEANprice(self) -> float:
        return 1.0 #arbitrary. Needed by VestingBeneficiaryAgent

@enforce_types
class KPIs(KPIsBase.KPIsBase):
    pass

@enforce_types
def netlist_createLogData(state):
    """SimEngine constructor uses this."""

    s = [] #for console logging
    dataheader = [] # for csv logging: list of string
    datarow = [] #for csv logging: list of float

    #SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    #So we log other things...

    timestamp = FIXME
    s += [f"; timestamp={timestamp}"]
    dataheader += ["timestamp"]
    datarow += [timestamp]
    
    vw = state.getAgent("vw_agent").vesting_wallet
    OCEAN_vested = vw.vestedAmount(OCEAN_address, timestamp)
    OCEAN_released = vw.released(OCEAN_address)
    s += [f"; OCEAN_vested={OCEAN_vested}, OCEAN_released={OCEAN_released}"]
    dataheader += ["OCEAN_vested", "OCEAN_released"]
    datarow += [OCEAN_vested, OCEAN_released]

    beneficiary_OCEAN = state.getAgent("beneficiary1").OCEANAtTick()
    s += [f"; beneficiary_OCEAN={beneficiary_OCEAN}"]
    dataheader += ["beneficiary_OCEAN"]
    datarow += [beneficiary_OCEAN]
    
    #done
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
    from util.plotutil import YParam, arrayToFloatList, LINEAR, MULT1, DOLLAR
    
    x_label = "Day"
    x = arrayToFloatList(values[:,header.index(x_label)])
    
    y_params = [
        YParam(["OCEAN_vested", "OCEAN_released", "beneficiary_OCEAN"],
               ["OCEAN vested", "OCEAN released", "OCEAN to beneficiary"],
               "Vesting over time", LINEAR, MULT1, DOLLAR)
    ]

    return (x_label, x, y_params)