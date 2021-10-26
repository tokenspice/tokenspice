from enforce_typing import enforce_types
import math
from typing import List

from engine import KPIsBase
from util import valuation
from util.constants import S_PER_YEAR, S_PER_MONTH, INF
from util.strutil import prettyBigNum
from web3engine import globaltokens# OCEAN_address, OCEANtoken

from assets.agents.PoolAgent import PoolAgent
from engine.AgentBase import AgentBase

@enforce_types
class KPIs(KPIsBase.KPIsBase):
    pass

@enforce_types
def get_OCEAN_in_DTs(state,agent,):
    pool_agents_list = list(state.agents.filterToPool().values())  
    agent_OCEAN_in_DTs = 0

    for pool in pool_agents_list:
        OCEAN_address = globaltokens.OCEAN_address()
        datatoken = pool.datatoken

        # get spot price of datatoken over OCEAN
        datatoken_sp = pool.pool.getSpotPrice_base(OCEAN_address,datatoken.address)/1e18
        agent_OCEAN_in_DTs += agent.DT(datatoken) * datatoken_sp
    
    return agent_OCEAN_in_DTs

@enforce_types
def get_pool_BPTs(state,pool):
    # get all agents list, except pool agents
    publisher_agents_list = list(state.agents.filterToPublisher().values())
    stakerspeculator_agents_list = list(state.agents.filterToStakerspeculator().values())
    consumer_agents_list = list(state.agents.filterToDataconsumer().values())
    speculator_agents_list = list(state.agents.filterToSpeculator().values())

    agents_list = publisher_agents_list+stakerspeculator_agents_list+consumer_agents_list+speculator_agents_list

    _BPTs = 0
    for agent in agents_list:
        _BPTs += agent.BPT(pool)
    return _BPTs

@enforce_types
def get_OCEAN_in_BPTs(state,agent):
    OCEAN_address = globaltokens.OCEAN_address()
    agent_OCEAN_in_BPTs = 0
    
    pool_agents_list = list(state.agents.filterToPool().values())

    # each pool, agent might has some BPT, get fraction of that amount over BPTs hold by all agents
    # multiple by OCEAN of the pool
    # aggerate for all pools
    for pool in pool_agents_list:
        percent_BPT = agent.BPT(pool.pool)/get_pool_BPTs(state,pool.pool)
        agent_OCEAN_in_BPTs += percent_BPT* pool.pool.getBalance_base(OCEAN_address)/1e18
        agent_OCEAN_in_BPTs += percent_BPT*pool.pool.getBalance_base(pool.datatoken.address)/1e18 \
                                * pool.pool.getSpotPrice_base(OCEAN_address,pool.datatoken.address)/1e18
                                 

    return agent_OCEAN_in_BPTs


@enforce_types
def netlist_createLogData(state):
    """SimEngine constructor uses this"""
    s = [] #for console logging
    dataheader = [] # for csv logging: list of string
    datarow = [] #for csv logging: list of float

    #SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    #So we log other things...
    agents_names = ["publisher","consumer","stakerSpeculator","speculator","maliciousPublisher"]

    # tracking OCEAN
    for name in agents_names:
        agent = state.getAgent(name)

        # in wallet
        dataheader += [f"{name}_OCEAN"]
        datarow += [agent.OCEAN()]

        # in DTs
        dataheader += [f"{name}_OCEAN_in_DTs"] 
        datarow += [get_OCEAN_in_DTs(state,agent)]

        # in BPTs
        dataheader += [f"{name}_OCEAN_in_BPTs"]
        datarow += [get_OCEAN_in_BPTs(state,agent)]

        # networth
        dataheader += [f"{name}_OCEAN_networth"]
        datarow +=[agent.OCEAN()+get_OCEAN_in_DTs(state,agent)+get_OCEAN_in_BPTs(state,agent)]
        
    
    pool_agents = state.agents.filterToPool()
    n_pools = len(pool_agents)
    s += ["; # pools=%d" % n_pools]
    dataheader += ["n_pools"]
    datarow += [n_pools]

    rugged_pool = state.ss.rugged_pools
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
    :return: x: List[float] -- x-axis info on how to plot
    :return: y_params: List[YParam] -- y-axis info on how to plot
    """
    from util.plotutil import YParam, arrayToFloatList, \
        LINEAR, MULT1, COUNT, DOLLAR
    
    x = arrayToFloatList(values[:,header.index("Day")])
    
    y_params = [
        YParam(["publisher_OCEAN_networth","consumer_OCEAN_networth","stakerSpeculator_OCEAN_networth","speculator_OCEAN_networth","maliciousPublisher_OCEAN_networth"],
        ["publisher","consumer","stakerSpeculator","speculator","maliciousPublisher"],"Agents OCEAN networth",LINEAR,MULT1,COUNT),
        YParam(["publisher_OCEAN","consumer_OCEAN","stakerSpeculator_OCEAN","speculator_OCEAN","maliciousPublisher_OCEAN"],
        ["publisher","consumer","staker","speculator","maliciousPublisher"],"Agents OCEAN wallet",LINEAR,MULT1,DOLLAR),
        # YParam(["staker_OCEAN"],["OCEAN"],"staker_OCEAN",LINEAR,MULT1,DOLLAR),
        # YParam(["speculator_OCEAN"],["OCEAN"],"speculator_OCEAN",LINEAR,MULT1,DOLLAR),
        YParam(["n_pools"],  ["# pools"],  "n_pools",  LINEAR,MULT1,COUNT)
    ]

    return (x, y_params)