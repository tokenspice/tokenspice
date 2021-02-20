import logging
log = logging.getLogger('simstate')

from enforce_typing import enforce_types
from typing import Set

from agents import MinterAgents
from agents.BaseAgent import BaseAgent
from agents.AgentDict import AgentDict
from agents.GrantGivingAgent import GrantGivingAgent
from agents.GrantTakingAgent import GrantTakingAgent
from agents.MarketplacesAgent import MarketplacesAgent
from agents.OCEANBurnerAgent import OCEANBurnerAgent
from agents.RouterAgent import RouterAgent
from engine import Kpis, SimStrategy
from util import mathutil, valuation
from util.mathutil import Range
from util.constants import *

@enforce_types
class SimState(object):
    
    def __init__(self, ss: SimStrategy.SimStrategy):
        log.debug("init:begin")
        
        #main
        self.ss = ss
        self.tick = 0

        #used to manage names
        self._next_free_marketplace_number = 0

        #used to add agents
        self._marketplace_tick_previous_add = 0
            
        #main storage of agents. Fill this below
        self.agents = AgentDict() #agent_name : Agent instance

        #<<Note many magic numbers below, for simplicity>>
        #note: KPIs class also has some magic number

        #as ecosystem improves, these parameters may change / improve
        self._marketplace_percent_toll_to_ocean = 0.002 #magic number
        self._percent_burn: float = 0.05 #to burning, vs to DAO #magic number

        self._total_OCEAN_minted: float = 0.0
        self._total_OCEAN_burned: float = 0.0
        self._total_OCEAN_burned_USD: float = 0.0

        self._speculation_valuation = 5e6 #in USD #magic number
        self._percent_increase_speculation_valuation_per_s = 0.10 / S_PER_YEAR # ""

        #Instantiate and connnect agent instances. "Wire up the circuit"
        new_agents: Set[BaseAgent] = set()

        #FIXME: replace MarketplacesAgent with DataecosystemAgent, when ready
        new_agents.add(MarketplacesAgent(
            name = "marketplaces1", USD=0.0, OCEAN=0.0,
            toll_agent_name = "opc_address",
            n_marketplaces = float(ss.init_n_marketplaces),
            revenue_per_marketplace_per_s = 2e3 / S_PER_MONTH, #magic number
            time_step = self.ss.time_step,
            ))

        new_agents.add(RouterAgent(
            name = "opc_address", USD=0.0, OCEAN=0.0,
            receiving_agents = {"ocean_dao" : self.percentToOceanDao,
                                "opc_burner" : self.percentToBurn}))

        new_agents.add(OCEANBurnerAgent(
            name = "opc_burner", USD=0.0, OCEAN=0.0))

        #func = MinterAgents.ExpFunc(H=4.0)
        func = MinterAgents.RampedExpFunc(H=4.0,                                 #magic number
                                          T0=0.5, T1=1.0, T2=1.4, T3=3.0,        #""
                                          M1=0.10, M2=0.25, M3=0.50)             #""
        new_agents.add(MinterAgents.OCEANFuncMinterAgent(
            name = "ocean_51",
            receiving_agent_name = "ocean_dao",
            total_OCEAN_to_mint = UNMINTED_OCEAN_SUPPLY,
            s_between_mints = S_PER_DAY,
            func = func))
        
        new_agents.add(GrantGivingAgent(
            name = "opf_treasury_for_ocean_dao",
            USD = 0.0, OCEAN = OPF_TREASURY_OCEAN_FOR_OCEAN_DAO,                 #magic number
            receiving_agent_name = "ocean_dao",
            s_between_grants = S_PER_MONTH, n_actions = 12 * 3))                 #""
        
        new_agents.add(GrantGivingAgent(
            name = "opf_treasury_for_opf_mgmt",
            USD = OPF_TREASURY_USD, OCEAN = OPF_TREASURY_OCEAN_FOR_OPF_MGMT,     #magic number
            receiving_agent_name = "opf_mgmt",
            s_between_grants = S_PER_MONTH, n_actions = 12 * 3))                 #""
        
        new_agents.add(GrantGivingAgent(
            name = "bdb_treasury",
            USD = BDB_TREASURY_USD, OCEAN = BDB_TREASURY_OCEAN,                  #magic number
            receiving_agent_name = "bdb_mgmt",
            s_between_grants = S_PER_MONTH, n_actions = 17))                     #""
        
        new_agents.add(RouterAgent(
            name = "ocean_dao",
            receiving_agents = {"opc_workers" : funcOne},
            USD=0.0, OCEAN=0.0))
        
        new_agents.add(RouterAgent(
            name = "opf_mgmt",
            receiving_agents = {"opc_workers" : funcOne},
            USD=0.0, OCEAN=0.0))
                       
        new_agents.add(RouterAgent(
            name = "bdb_mgmt",
            receiving_agents = {"bdb_workers" : funcOne},
            USD=0.0, OCEAN=0.0))

        new_agents.add(GrantTakingAgent(
            name = "opc_workers", USD=0.0, OCEAN=0.0))

        new_agents.add(GrantTakingAgent(
            name = "bdb_workers", USD=0.0, OCEAN=0.0))

        for agent in new_agents:
            self.agents[agent.name] = agent

        #track certain metrics over time, so that we don't have to load
        self.kpis = Kpis.KPIs(self.ss.time_step)
        
        log.debug("init: end")
            
    def takeStep(self) -> None:
        """This happens once per tick"""
        #update agents
        for agent in self.agents.values():
            agent.takeStep(self)

        #update global state values: revenue, valuation
        self.kpis.takeStep(self)

        #update global state values: other
        self._speculation_valuation *= (1.0 + self._percent_increase_speculation_valuation_per_s * self.ss.time_step)

    #==============================================================   
    def getAgent(self, name: str):
        return self.agents[name]
        
    def allAgents(self):
        return set(self.agents.values())

    def numAgents(self) -> int:
        return len(self.agents)

    def addAgent(self, agent):
        assert agent.name not in self.agents, "have an agent with this name" 
        self.agents[agent.name] = self.agents

    #==============================================================      
    def marketplacePercentTollToOcean(self) -> float:
        return self._marketplace_percent_toll_to_ocean
    
    def percentToBurn(self) -> float:
        return self._percent_burn

    def percentToOceanDao(self) -> float:
        return 1.0 - self._percent_burn
    
    #==============================================================
    def grantTakersSpentAtTick(self) -> float:
        return sum(
            agent.spentAtTick()
            for agent in self.agents.values()
            if isinstance(agent, GrantTakingAgent))

    #==============================================================
    def OCEANprice(self) -> float:
        """Estimated price of $OCEAN token, in USD"""
        price = valuation.OCEANprice(self.overallValuation(),
                                     self.OCEANsupply())
        assert price > 0.0
        return price
    
    #==============================================================
    def overallValuation(self) -> float: #in USD
        v = self.fundamentalsValuation() + \
            self.speculationValuation()
        assert v > 0.0
        return v
    
    def fundamentalsValuation(self) -> float: #in USD
        return self.kpis.valuationPS(30.0) #based on P/S=30                     #magic number
    
    def speculationValuation(self) -> float: #in USD
        return self._speculation_valuation
        
    #==============================================================
    def OCEANsupply(self) -> float:
        """Current OCEAN token supply"""
        return self.initialOCEAN() \
            + self.totalOCEANminted() \
            - self.totalOCEANburned()
        
    def initialOCEAN(self) -> float:
        return INIT_OCEAN_SUPPLY
        
    def totalOCEANminted(self) -> float:
        return self._total_OCEAN_minted
        
    def totalOCEANburned(self) -> float:
        return self._total_OCEAN_burned
        
    def totalOCEANburnedUSD(self) -> float:
        return self._total_OCEAN_burned_USD
    
    
def funcOne():
    return 1.0

