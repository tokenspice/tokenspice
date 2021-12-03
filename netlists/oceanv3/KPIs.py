from typing import List

from enforce_typing import enforce_types

from engine import KPIsBase
from util import globaltokens
from util.base18 import fromBase18
from util.plotutil import YParam, arrayToFloatList, LINEAR, MULT1, COUNT, DOLLAR


@enforce_types
class KPIs(KPIsBase.KPIsBase):
    pass


@enforce_types
def get_OCEAN_in_DTs(state, agent) -> float:
    """Value of DT that this agent staked across all pools, denominated in OCEAN

    Args:
        state: SimState -- SimState, holds all pool agents (& their pools)
        agent:  AgentBase -- agent of interest

    Returns:
        value_held: float -- value staked, denominated in OCEAN
    """
    OCEAN_address = globaltokens.OCEAN_address()
    value_held = 0.0

    for pool_agent in state.agents.filterToPool().values():
        pool = pool_agent._pool
        DT = pool_agent._dt
        price = fromBase18(pool.getSpotPrice(OCEAN_address, DT.address))
        amt_DT = agent.DT(DT)
        value_held += amt_DT * price

    return value_held


@enforce_types
@enforce_types
def get_OCEAN_in_BPTs(state, agent):
    """Value of BPTs that this agent owns across all pools, denominated in OCEAN

    Args:
        state: SimState -- SimState, holds all pool agents (& their pools)
        agent:  AgentBase -- agent of interest

    Returns:
        value_held: float -- value of BPTs, denominated in OCEAN
    """
    OCEAN_address = globaltokens.OCEAN_address()
    value_held = 0

    for pool_agent in state.agents.filterToPool().values():
        pool = pool_agent._pool
        DT = pool_agent._dt

        price = fromBase18(pool.getSpotPrice(OCEAN_address, DT.address))
        pool_value_DT = price * fromBase18(pool.getBalance(DT.address))
        pool_value_OCEAN = fromBase18(pool.getBalance(OCEAN_address))
        pool_value = pool_value_DT + pool_value_OCEAN

        amt_pool_BPTs = pool.totalSupply()  # from BPool, inheriting from BToken
        agent_percent_pool = agent.BPT(pool) / amt_pool_BPTs

        value_held += agent_percent_pool * pool_value

    return value_held


@enforce_types
def netlist_createLogData(state):
    """SimEngine constructor uses this"""
    s = []  # for console logging
    dataheader = []  # for csv logging: list of string
    datarow = []  # for csv logging: list of float

    # SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    # So we log other things...
    agents_names = [
        "publisher",
        "consumer",
        "stakerSpeculator",
        "speculator",
        "maliciousPublisher",
    ]

    # tracking OCEAN
    for name in agents_names:
        agent = state.getAgent(name)

        # in wallet
        dataheader += [f"{name}_OCEAN"]
        datarow += [agent.OCEAN()]

        # in DTs
        dataheader += [f"{name}_OCEAN_in_DTs"]
        datarow += [get_OCEAN_in_DTs(state, agent)]

        # in BPTs
        dataheader += [f"{name}_OCEAN_in_BPTs"]
        datarow += [get_OCEAN_in_BPTs(state, agent)]

        # networth
        dataheader += [f"{name}_OCEAN_networth"]
        datarow += [
            agent.OCEAN()
            + get_OCEAN_in_DTs(state, agent)
            + get_OCEAN_in_BPTs(state, agent)
        ]

    pool_agents = state.agents.filterToPool()
    n_pools = len(pool_agents)
    s += ["; # pools=%d" % n_pools]
    dataheader += ["n_pools"]
    datarow += [n_pools]

    rugged_pool = state.rugged_pools
    n_rugged = len(rugged_pool)
    s += ["; # rugged pools=%d" % n_rugged]
    dataheader += ["n_rugged"]
    datarow += [n_rugged]

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
    x_label = "Year"
    x = arrayToFloatList(values[:, header.index(x_label)])

    y_params = [
        YParam(
            [
                "publisher_OCEAN_networth",
                "consumer_OCEAN_networth",
                "stakerSpeculator_OCEAN_networth",
                "speculator_OCEAN_networth",
                "maliciousPublisher_OCEAN_networth",
            ],
            [
                "publisher",
                "consumer",
                "stakerSpeculator",
                "speculator",
                "maliciousPublisher",
            ],
            "Agents OCEAN networth",
            LINEAR,
            MULT1,
            COUNT,
        ),
        YParam(
            [
                "publisher_OCEAN",
                "consumer_OCEAN",
                "stakerSpeculator_OCEAN",
                "speculator_OCEAN",
                "maliciousPublisher_OCEAN",
            ],
            ["publisher", "consumer", "staker", "speculator", "maliciousPublisher"],
            "Agents OCEAN wallet",
            LINEAR,
            MULT1,
            DOLLAR,
        ),
        YParam(["n_pools"], ["# pools"], "n_pools", LINEAR, MULT1, COUNT),
    ]

    return (x_label, x, y_params)
