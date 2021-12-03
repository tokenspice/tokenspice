from typing import List

import brownie
from enforce_typing import enforce_types

from agents.VestingBeneficiaryAgent import VestingBeneficiaryAgent
from agents.VestingFunderAgent import VestingFunderAgent
from engine import KPIsBase, SimStateBase, SimStrategyBase
from util.constants import S_PER_MONTH, S_PER_YEAR
from util.globaltokens import OCEAN_address
from util.plotutil import YParam, arrayToFloatList, LINEAR, MULT1, DOLLAR

chain = brownie.network.chain


@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        # ==baseline
        self.setTimeStep(S_PER_MONTH)
        self.setMaxTime(10, "years")
        self.setLogInterval(3 * S_PER_MONTH)

        # ==attributes specific to this netlist
        self.OCEAN_funded: float = 5.0
        self.start_timestamp: int = chain[-1].timestamp + S_PER_YEAR
        self.duration_seconds: int = 5 * S_PER_YEAR


@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        assert ss is None
        super().__init__(ss)

        # ss is defined in this netlist module
        self.ss = SimStrategy()

        # wire up the circuit
        agents = []
        agents.append(
            VestingFunderAgent(
                name="funder1",
                USD=0.0,
                OCEAN=self.ss.OCEAN_funded,
                vesting_wallet_agent_name="vw1",
                beneficiary_agent_name="beneficiary1",
                start_timestamp=self.ss.start_timestamp,
                duration_seconds=self.ss.duration_seconds,
            )
        )
        agents.append(
            VestingBeneficiaryAgent(
                name="beneficiary1", USD=0.0, OCEAN=0.0, vesting_wallet_agent_name="vw1"
            )
        )
        self.agents = {agent.name: agent for agent in agents}

        # kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step)


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

    timestamp = chain[-1].timestamp
    s += [f"; timestamp={timestamp}"]
    dataheader += ["timestamp"]
    datarow += [timestamp]

    if "vw1" in state.agents:
        vw = state.getAgent("vw1").vesting_wallet
        OCEAN_vested = vw.vestedAmount(OCEAN_address(), timestamp) / 1e18
        OCEAN_released = vw.released(OCEAN_address()) / 1e18
    else:
        OCEAN_vested = OCEAN_released = 0
    s += [f"; OCEAN_vested={OCEAN_vested}, OCEAN_released={OCEAN_released}"]
    dataheader += ["OCEAN_vested", "OCEAN_released"]
    datarow += [OCEAN_vested, OCEAN_released]

    beneficiary_OCEAN = state.getAgent("beneficiary1").OCEAN()
    s += [f"; beneficiary_OCEAN={beneficiary_OCEAN}"]
    dataheader += ["beneficiary_OCEAN"]
    datarow += [beneficiary_OCEAN]

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
    x_label = "Year"
    x = arrayToFloatList(values[:, header.index(x_label)])

    y_params = [
        YParam(
            ["OCEAN_vested", "OCEAN_released", "beneficiary_OCEAN"],
            ["OCEAN vested", "OCEAN released", "OCEAN to beneficiary"],
            "Vesting over time",
            LINEAR,
            MULT1,
            DOLLAR,
        )
    ]

    return (x_label, x, y_params)
