import math
from enforce_typing import enforce_types

from engine import AgentBase
from util.constants import S_PER_YEAR


@enforce_types
class MarketplacesAgent(AgentBase.AgentBaseNoEvm):
    def __init__(
        self,
        name: str,
        USD: float,
        OCEAN: float,
        toll_agent_name: str,
        n_marketplaces: float,
        sales_per_marketplace_per_s: float,
        time_step: int,
    ):  # pylint: disable=too-many-arguments
        super().__init__(name, USD, OCEAN)
        self._toll_agent_name: str = toll_agent_name

        # set initial values. These grow over time.
        self._n_marketplaces: float = n_marketplaces
        self._consume_sales_per_marketplace_per_s: float = sales_per_marketplace_per_s
        self._time_step: int = time_step

    def numMarketplaces(self) -> float:
        return self._n_marketplaces

    def consumeSalesPerMarketplacePerSecond(self) -> float:
        return self._consume_sales_per_marketplace_per_s

    def takeStep(self, state):
        ratio = state.kpis.mktsRNDToSalesRatio()
        mkts_growth_rate_per_year = state.ss.annualMktsGrowthRate(ratio)
        mkts_growth_rate_per_tick = self._growthRatePerTick(mkts_growth_rate_per_year)

        # *grow* the number of marketplaces, and revenue per marketplace
        self._n_marketplaces *= 1.0 + mkts_growth_rate_per_tick
        self._consume_sales_per_marketplace_per_s *= 1.0 + mkts_growth_rate_per_tick

        # compute sales -> toll -> send funds accordingly
        consume_sales = self._consumeSalesPerTick()
        toll = state.ss.networkRevenue(consume_sales)
        toll_agent = state.getAgent(self._toll_agent_name)
        toll_agent.receiveUSD(toll)

        # NOTE: we don't bother modeling marketplace profits or tracking mkt wallet $

    def _consumeSalesPerTick(self) -> float:
        return (
            self._n_marketplaces
            * self._consume_sales_per_marketplace_per_s
            * self._time_step
        )

    def _growthRatePerTick(self, g_per_year: float) -> float:
        """
        @arguments
          g_per_year -- growth rate per year, e.g. 0.05 for 5% annual rate
        """
        ticks_per_year = S_PER_YEAR / float(self._time_step)
        g_per_tick = math.pow(g_per_year + 1, 1.0 / ticks_per_year) - 1.0
        return g_per_tick
