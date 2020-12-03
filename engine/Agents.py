import logging
log = logging.getLogger('agents')

import enforce
import math

from engine.BaseAgent import BaseAgent
from engine.evm import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools import web3util
from web3tools.web3util import fromBase18, toBase18
from web3tools.web3wallet import Web3Wallet
from util.constants import S_PER_MONTH, S_PER_YEAR
    
@enforce.runtime_validation
class PublisherAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN) 
        self.pools = []
        
    def takeStep(self, state) -> None:
        create_new_pool = False #FIXME: have fancier way to choose
        
        if create_new_pool:
            #create new dt
            amount = toBase18(1000.0) #magic number
            dt_factory = dtfactory.DTFactory()
            dt_address = dt_factory.createToken(
                '', 'DT', 'DT', amount, self.web3_wallet)
            dt = datatoken.Datatoken(dt_address)            

            #new pool
            pool_factory = bfactory.BFactory()
            pool_address = pool_factory.newBPool(from_wallet=self.web3_wallet)
            pool = bpool.BPool(pool_address)

            #bind tokens, add liquidity, etc. 
            # FIXME. How: see test_2tokens_basic

            #
            self.pools.append(pool)
        
@enforce.runtime_validation
class PoolAgent(BaseAgent):
    def __init__(self, name: str, pool:bpool.BPool):
        #FIXME
        pass
    
@enforce.runtime_validation
class RouterAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float,
                 receiving_agents : dict):
        """receiving_agents -- [agent_n_name] : method_for_%_going_to_agent_n
        The dict values are methods, not floats, so that the return value
        can change over time. E.g. percent_burn changes.
        """
        super().__init__(name, USD, OCEAN)
        self._receiving_agents = receiving_agents

        #track amounts over time
        self._USD_per_tick = [] #the next tick will record what's in self
        self._OCEAN_per_tick = [] # ""
        
    def takeStep(self, state) -> None:
        #record what we had up until this point
        self._USD_per_tick.append(self.USD())
        self._OCEAN_per_tick.append(self.OCEAN())
        
        #disburse it all, as soon as agent has it
        if self.USD() > 0:
            self._disburseUSD(state)
        if self.OCEAN() > 0:
            self._disburseOCEAN(state)

    def _disburseUSD(self, state) -> None:
        USD = self.USD()
        for name, computePercent in self._receiving_agents.items():
            self._transferUSD(state.getAgent(name), computePercent() * USD)

    def _disburseOCEAN(self, state) -> None:
        OCEAN = self.OCEAN()
        for name, computePercent in self._receiving_agents.items():
            self._transferOCEAN(state.getAgent(name), computePercent() * OCEAN)

    def monthlyUSDreceived(self, state) -> float:
        """Amount of USD received in the past month. 
        Assumes that it disburses USD as soon as it gets it."""
        tick1 = self._tickOneMonthAgo(state)
        tick2 = state.tick
        return float(sum(self._USD_per_tick[tick1:tick2+1]))
    
    def monthlyOCEANreceived(self, state) -> float:
        """Amount of OCEAN received in the past month. 
        Assumes that it disburses OCEAN as soon as it gets it."""
        tick1 = self._tickOneMonthAgo(state)
        tick2 = state.tick
        return float(sum(self._OCEAN_per_tick[tick1:tick2+1]))

    def _tickOneMonthAgo(self, state) -> int:
        t2 = state.tick * state.ss.time_step
        t1 = t2 - S_PER_MONTH
        if t1 < 0:
            return 0
        tick1 = int(max(0, math.floor(t1 / float(state.ss.time_step))))
        return tick1

@enforce.runtime_validation
class OCEANBurnerAgent(BaseAgent):
    def takeStep(self, state):
        if self.USD() > 0.0:
            #OCEAN price will go up as we buy. Reflect it here.
            nloops = 10
            USD_spend_per_loop = self.USD() / float(nloops)
            for i in range(nloops):
                price = state.OCEANprice() #a func of supply
                OCEAN = USD_spend_per_loop / price
                state._total_OCEAN_burned += OCEAN
                state._total_OCEAN_burned_USD += USD_spend_per_loop

            self._wallet.withdrawUSD(self.USD()) #we've spent the USD!
                    
@enforce.runtime_validation
class GrantGivingAgent(BaseAgent):
    """
    Disburses funds at a fixed # evenly-spaced intervals.
    Same amount each time.
    """
    def __init__(self, name: str, USD: float, OCEAN: float,
                 receiving_agent_name: str,
                 s_between_grants: int,  n_actions: int):
        super().__init__(name, USD, OCEAN)
        self._receiving_agent_name: str = receiving_agent_name
        self._s_between_grants: int = s_between_grants
        self._USD_per_grant: float = USD / float(n_actions)
        self._OCEAN_per_grant: float = OCEAN / float(n_actions)
        
        self._tick_last_disburse = None
        
    def takeStep(self, state):
        do_disburse = False
        if self._tick_last_disburse is None:
            do_disburse = True
        else:
            n_ticks_since = state.tick - self._tick_last_disburse
            n_s_since = n_ticks_since * state.ss.time_step
            n_s_thr = self._s_between_grants            
            do_disburse = (n_s_since >= n_s_thr)
        
        if do_disburse:
            self._disburseFunds(state)
            self._tick_last_disburse = state.tick

    def _disburseFunds(self, state):
        #same amount each time
        receiving_agent = state.getAgent(self._receiving_agent_name)
        
        USD = min(self.USD(), self._USD_per_grant)
        self._transferUSD(receiving_agent, USD)
                
        OCEAN = min(self.OCEAN(), self._OCEAN_per_grant)
        self._transferOCEAN(receiving_agent, OCEAN)
        
@enforce.runtime_validation
class GrantTakingAgent(BaseAgent):    
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        self._spent_at_tick = 0.0 #USD and OCEAN (in USD) spent
        
    def takeStep(self, state):
        self._spent_at_tick = self.USD() + self.OCEAN() * state.OCEANprice()
        
        #spend it all, as soon as agent has it
        self._transferUSD(None, self.USD())
        self._transferOCEAN(None, self.OCEAN())

    def spentAtTick(self) -> float:
        return self._spent_at_tick

@enforce.runtime_validation
class MarketplacesAgent(BaseAgent):
    def __init__(self,
                 name: str, USD: float, OCEAN: float,
                 toll_agent_name: str,
                 n_marketplaces: float,
                 revenue_per_marketplace_per_s: float,
                 time_step: int,
                 ):
        super().__init__(name, USD, OCEAN)
        self._toll_agent_name: str = toll_agent_name

        #set initial values. These grow over time.
        self._n_marketplaces: float = n_marketplaces
        self._revenue_per_marketplace_per_s: float = revenue_per_marketplace_per_s
        self._time_step: int = time_step

    def numMarketplaces(self) -> float:
        return self._n_marketplaces
        
    def revenuePerMarketplacePerSecond(self) -> float:
        return self._revenue_per_marketplace_per_s
        
    def takeStep(self, state):
        ratio = state.kpis.mktsRNDToSalesRatio()
        mkts_growth_rate_per_year = state.ss.annualMktsGrowthRate(ratio)
        mkts_growth_rate_per_tick = self._growthRatePerTick(mkts_growth_rate_per_year)
        
        #*grow* the number of marketplaces, and revenue per marketplace
        self._n_marketplaces *= (1.0 + mkts_growth_rate_per_tick)
        self._revenue_per_marketplace_per_s *= (1.0 + mkts_growth_rate_per_tick)

        #compute sales -> toll -> send funds accordingly
        #NOTE: we don't bother modeling marketplace profits or tracking mkt wallet $
        sales = self._salesPerTick()
        toll = sales * state.marketplacePercentTollToOcean()
        toll_agent = state.getAgent(self._toll_agent_name)
        toll_agent.receiveUSD(toll)

    def _salesPerTick(self) -> float:
        return self._n_marketplaces * self._revenue_per_marketplace_per_s \
            * self._time_step

    def _growthRatePerTick(self, g_per_year: float) -> float:
        """
        @arguments 
          g_per_year -- growth rate per year, e.g. 0.05 for 5% annual rate
        """
        ticks_per_year = S_PER_YEAR / float(self._time_step)
        g_per_tick = math.pow(g_per_year + 1, 1.0/ticks_per_year) - 1.0
        return g_per_tick

        
        
