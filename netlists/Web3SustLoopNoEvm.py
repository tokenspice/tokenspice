from enforce_typing import enforce_types
from typing import Set

from agents import MinterAgents
from agents.BaseAgent import BaseAgent
from agents.GrantGivingAgent import GrantGivingAgent
from agents.GrantTakingAgent import GrantTakingAgent
from agents.MarketplacesAgent import MarketplacesAgent
from agents.OCEANBurnerAgent import OCEANBurnerAgent
from agents.RouterAgent import RouterAgent

from engine import SimStateBase, Kpis, SimStrategyBase
from util import valuation
from util.constants import * #S_PER_HOUR, etc

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        #===initialize self.time_step, max_ticks====
        super().__init__()

        #===set base-class values we want for this netlist====
        self.setTimeStep(S_PER_HOUR)
        max_days = 10
        self.setMaxTicks(max_days * S_PER_DAY / self.time_step + 1)

        #===new attributes specific to this netlist===

        #initial # mkts
        self.init_n_marketplaces = 1

        #for computing annualGrowthRate() of # marketplaces, revenue/mktplace
        #-total marketplaces' growth = (1+annualGrowthRate)^2 - 1
        #-so, if we want upper bound of total marketplaces' growth of 50%,
        # we need max_growth_rate = 22.5%.
        #-and, if we want lower bound of total growth of -25%,
        # we need growth_rate_if_0_sales = -11.8%
        self.growth_rate_if_0_sales = -0.118
        self.max_growth_rate = 0.415
        self.tau = 0.6

    def annualMktsGrowthRate(self, ratio_RND_to_sales: float) -> float:
        """
        Growth rate for marketplaces. Starts low, and increases as
        the ($ into R&D)/($ from sales) goes up, but w/ diminishing returns.

        Modeled as an exponential decay function. 
        -Input x: ratio_RND_to_sales
        -Output y: growth rate
        -Func params:
          -self.tau: at x=tau, y has increased by 50% of its possible increase
          -          at x=2*tau, y ... 75% ...
          -self.growth_rate_if_0_sales 
          -self.max_growth_rate
        """
        mult = self.max_growth_rate - self.growth_rate_if_0_sales
        growth_rate: float = self.growth_rate_if_0_sales + mult * (1.0 - math.pow(0.5, ratio_RND_to_sales/self.tau))
        return growth_rate
    
@enforce_types
class SimState(SimStateBase.SimStateBase):
    
    def __init__(self):
        #initialize self.tick, ss, agents, kpis
        super().__init__()

        #now, fill in actual values for ss, agents, kpis
        self.ss = SimStrategy()
        ss = self.ss #for convenience as we go forward
                        
        #used to manage names
        self._next_free_marketplace_number = 0

        #used to add agents
        self._marketplace_tick_previous_add = 0
        
        #as ecosystem improves, these parameters may change / improve
        self._marketplace_percent_toll_to_ocean = 0.002 #magic number
        self._percent_burn: float = 0.05 #to burning, vs to DAO #magic number

        self._total_OCEAN_minted: float = 0.0
        self._total_OCEAN_burned: float = 0.0
        self._total_OCEAN_burned_USD: float = 0.0

        self._speculation_valuation = 150e6 #in USD #magic number
        self._percent_increase_speculation_valuation_per_s = 0.10 / S_PER_YEAR # ""

        #Instantiate and connnect agent instances. "Wire up the circuit"
        new_agents: Set[BaseAgent] = set()

        #Note: could replace MarketplacesAgent with DataecosystemAgent, for a
        # higher-fidelity simulation using EVM agents
        new_agents.add(MarketplacesAgent(
            name = "marketplaces1", USD=0.0, OCEAN=0.0,
            toll_agent_name = "opc_address",
            n_marketplaces = float(ss.init_n_marketplaces),
            revenue_per_marketplace_per_s = 20e3 / S_PER_MONTH, #magic number
            time_step = self.ss.time_step,
            ))

        new_agents.add(RouterAgent(
            name = "opc_address", USD=0.0, OCEAN=0.0,
            receiving_agents = {"ocean_dao" : self.percentToOceanDao,
                                "opc_burner" : self.percentToBurn}))

        new_agents.add(OCEANBurnerAgent(
            name = "opc_burner", USD=0.0, OCEAN=0.0))

        #func = MinterAgents.ExpFunc(H=4.0)
        func = MinterAgents.RampedExpFunc(H=4.0,
                                          T0=0.5, T1=1.0, T2=1.4, T3=3.0,
                                          M1=0.10, M2=0.25, M3=0.50)
        new_agents.add(MinterAgents.OCEANFuncMinterAgent(
            name = "ocean_51",
            receiving_agent_name = "ocean_dao",
            total_OCEAN_to_mint = UNMINTED_OCEAN_SUPPLY,
            s_between_mints = S_PER_DAY,
            func = func))
        
        new_agents.add(GrantGivingAgent(
            name = "opf_treasury_for_ocean_dao",
            USD = 0.0, OCEAN = OPF_TREASURY_OCEAN_FOR_OCEAN_DAO, 
            receiving_agent_name = "ocean_dao",
            s_between_grants = S_PER_MONTH, n_actions = 12 * 3))
        
        new_agents.add(GrantGivingAgent(
            name = "opf_treasury_for_opf_mgmt",
            USD = OPF_TREASURY_USD, OCEAN = OPF_TREASURY_OCEAN_FOR_OPF_MGMT,
            receiving_agent_name = "opf_mgmt",
            s_between_grants = S_PER_MONTH, n_actions = 12 * 3))
        
        new_agents.add(GrantGivingAgent(
            name = "bdb_treasury",
            USD = BDB_TREASURY_USD, OCEAN = BDB_TREASURY_OCEAN,
            receiving_agent_name = "bdb_mgmt",
            s_between_grants = S_PER_MONTH, n_actions = 17))
        
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
                    
    def takeStep(self) -> None:
        """This happens once per tick"""
        #update agents
        #update kpis (global state values)
        super().takeStep()
        
        #update global state values: other
        self._speculation_valuation *= (1.0 + self._percent_increase_speculation_valuation_per_s * self.ss.time_step)

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
        return self.kpis.valuationPS(30.0) #based on P/S=30
    
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

