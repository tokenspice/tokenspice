import logging
log = logging.getLogger('agents')

from enforce_typing import enforce_types # type: ignore[import]
import math

from agents.BaseAgent import BaseAgent
from util.constants import S_PER_YEAR
    

@enforce_types
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

        
        
