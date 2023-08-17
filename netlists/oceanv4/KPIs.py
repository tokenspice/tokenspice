from typing import List
import brownie

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

    for pool_agent in state.agents.filterToPoolV4().values():
        pool = pool_agent._pool
        DT = pool_agent._dt
        swapFee = pool.getSwapFee()
        price = fromBase18(pool.getSpotPrice(OCEAN_address, DT.address, swapFee))
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

    for pool_agent in state.agents.filterToPoolV4().values():
        pool = pool_agent._pool
        DT = pool_agent._dt

        swapFee = pool.getSwapFee()
        price = fromBase18(pool.getSpotPrice(OCEAN_address, DT.address, swapFee))
        pool_value_DT = price * fromBase18(pool.getBalance(DT.address))
        pool_value_OCEAN = fromBase18(pool.getBalance(OCEAN_address))
        pool_value = pool_value_DT + pool_value_OCEAN

        amt_pool_BPTs = fromBase18(
            pool.totalSupply()
        )  # from BPool, inheriting from BToken
        agent_percent_pool = agent.BPT(pool) / amt_pool_BPTs

        value_held += agent_percent_pool * pool_value
        # import ipdb
        # ipdb.set_trace()

    return value_held


@enforce_types
def netlist_createLogData(state):  # pylint: disable=too-many-statements
    """SimEngine constructor uses this"""
    s = []  # for console logging
    dataheader = []  # for csv logging: list of string
    datarow = []  # for csv logging: list of float

    # SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    # So we log other things...
    agents_names = [
        "publisher",
        # "consumer",
        "stakerSpeculator",
        "speculator",
        # "buySellRobot",
        # "maliciousPublisher"
        # "erc721"
    ]
    # tracking OCEAN
    OCEANtoken = globaltokens.OCEANtoken()
    OCEAN_address = globaltokens.OCEAN_address()
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

        dataheader += [f"DT_{name}"]
        dataheader += [f"BPT_{name}"]

        # Tracking DT and BPT balances of agents
        if any(state.agents.filterToPoolV4().values()):
            poolAgent_0 = list(state.agents.filterToPoolV4().values())[0]
            DT = poolAgent_0._dt
            amt_DT = agent.DT(DT)
            datarow += [amt_DT]
            datarow += [agent.BPT(poolAgent_0._pool)]  # agent.BPT(pool)
        else:
            datarow += [0, 0]

    # Track pool0
    # 1. DT in pool,
    # 2. DT balance of 1ss contract
    # 3. BPT total supply,
    # 4. BPT balance of 1ss contract,
    # 5. DT spot price
    # 6. OCEAN in pool
    dataheader += ["DT_pool"]
    dataheader += ["DT_1ss_contract"]
    dataheader += ["BPT_total"]
    dataheader += ["BPT_1ss_contract"]
    dataheader += ["DT_price"]
    dataheader += ["pool_OCEAN"]
    if any(state.agents.filterToPoolV4().values()):
        poolAgent_0 = list(state.agents.filterToPoolV4().values())[0]
        pool0 = poolAgent_0._pool
        DT = poolAgent_0._dt
        oneSSContractAddress = pool0.getController()

        datarow += [fromBase18(DT.balanceOf(pool0.address))]  # 1
        datarow += [fromBase18(DT.balanceOf(oneSSContractAddress))]  # 2
        datarow += [fromBase18(pool0.totalSupply())]  # 3
        datarow += [fromBase18(pool0.balanceOf(oneSSContractAddress))]  # 4
        swapFee = pool0.getSwapFee()
        datarow += [
            fromBase18(pool0.getSpotPrice(OCEAN_address, DT.address, swapFee))
        ]  # 5
        datarow += [fromBase18(OCEANtoken.balanceOf(pool0.address))]
    else:
        datarow += [0, 0, 0, 0, 0, 0]

    pool_agents = state.agents.filterToPoolV4()
    n_pools = len(pool_agents)
    s += [f"; # pools={n_pools}"]
    dataheader += ["n_pools"]
    datarow += [n_pools]

    rugged_pool = state.rugged_pools
    n_rugged = len(rugged_pool)
    # s += [f"; # rugged pools={n_rugged}"]
    s += [f"; # block height={brownie.chain.height}"]
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
    x_label = "Day"
    x = arrayToFloatList(values[:, header.index(x_label)])

    y_params = [
        YParam(
            [
                "publisher_OCEAN_networth",
                "consumer_OCEAN_networth",
                "stakerSpeculator_OCEAN_networth",
                "speculator_OCEAN_networth",
                # "buySellRobot_OCEAN_networth",
                # "maliciousPublisher_OCEAN_networth"
            ],
            [
                "publisher",
                "consumer",
                "stakerSpeculator",
                "speculator",
                # "buySellRobot",
                # "maliciousPublisher"
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
                # "buySellRobot_OCEAN",
                # "maliciousPublisher_OCEAN"
            ],
            [
                "publisher",
                "consumer",
                "staker",
                "speculator",
                # "buySellRobot",
                # "maliciousPublisher"
            ],
            "Agents OCEAN wallet",
            LINEAR,
            MULT1,
            DOLLAR,
        ),
        YParam(
            [
                "DT_publisher",
                "DT_consumer",
                "DT_stakerSpeculator",
                "DT_speculator",
                "DT_buySellRobot"
                # "DT_maliciousPublisher"
            ],
            [
                "publisher",
                "consumer",
                "staker",
                "speculator",
                "buySellRobot",
                # "maliciousPublisher"
            ],
            "Agents Datatokens",
            LINEAR,
            MULT1,
            DOLLAR,
        ),
        YParam(
            ["DT_pool", "DT_1ss_contract"],
            ["DT in pool", "DT in one-sided staking contract"],
            "DT allocation",
            LINEAR,
            MULT1,
            COUNT,
        ),
        YParam(
            [
                "BPT_publisher",
                "BPT_consumer",
                "BPT_stakerSpeculator",
                "BPT_speculator",
                # "BPT_maliciousPublisher",
                "BPT_1ss_contract",
            ],
            [
                "publisher",
                "consumer",
                "staker",
                "speculator",
                # "maliciousPublisher",
                "one-sided staking contract",
            ],
            "BPT allocation",
            LINEAR,
            MULT1,
            COUNT,
        ),
        YParam(
            ["DT_price"],
            [
                "DT_price",
            ],
            "dt price",
            LINEAR,
            MULT1,
            DOLLAR,
        ),
        YParam(["n_pools"], ["# pools"], "n_pools", LINEAR, MULT1, COUNT),
        YParam(["pool_OCEAN"], ["pool_OCEAN"], "pool_OCEAN", LINEAR, MULT1, DOLLAR),
    ]

    return (x_label, x, y_params)
