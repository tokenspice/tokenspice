import math
from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_DAY, S_PER_YEAR


@enforce_types
class SimStrategy(
    SimStrategyBase.SimStrategyBase
):  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        # ===initialize self.time_step, max_ticks====
        super().__init__()

        # ===set base-class values we want for this netlist====
        self.setTimeStep(S_PER_DAY)
        self.setMaxTime(2, "years")  # typical runs: 10 years, 20 years, 150 years
        self.setLogInterval(10 * S_PER_DAY)

        # ===new attributes specific to this netlist===

        # network revenue
        self._percent_consume_sales_for_network = 0.03  # 0.1% no DF, 3% DF
        self._percent_swap_sales_for_network = 0.001  # 0.1%

        # $ volume in swap : $ volume in consume
        self._swap_to_consume_sales_ratio = 100.0

        # initial # mkts
        self.init_n_marketplaces = 1

        # % network revenue to burn, vs to DAO
        self._percent_burn: float = 0.05

        # valuation
        self._p_s_ratio = 30.0

        self._init_speculation_valuation = 150e6  # in USD
        self._percent_increase_speculation_valuation_per_s = 0.10 / S_PER_YEAR

        # for computing annualGrowthRate() of # marketplaces, revenue/mktplace
        # -total marketplaces' growth = (1+annualGrowthRate)^2 - 1
        # -so, if we want upper bound of total marketplaces' growth of 50%,
        # we need max_growth_rate = 22.5%.
        # -and, if we want lower bound of total growth of -25%,
        # we need growth_rate_if_0_sales = -11.8%
        self.growth_rate_if_0_sales = -0.118
        self.max_growth_rate = 0.415
        self.tau = 0.6

        # (taken from constants.py)
        self.TOTAL_OCEAN_SUPPLY = 1.41e9
        self.INIT_OCEAN_SUPPLY = 0.49 * self.TOTAL_OCEAN_SUPPLY
        self.UNMINTED_OCEAN_SUPPLY = self.TOTAL_OCEAN_SUPPLY - self.INIT_OCEAN_SUPPLY

        self.OPF_TREASURY_USD = 2e6  # (not the true number)
        self.OPF_TREASURY_OCEAN = 200e6  # (not the true number)
        self.OPF_TREASURY_OCEAN_FOR_OCEAN_DAO = 100e6  # (not the true number)
        self.OPF_TREASURY_OCEAN_FOR_OPF_MGMT = (
            self.OPF_TREASURY_OCEAN - self.OPF_TREASURY_OCEAN_FOR_OCEAN_DAO
        )

        self.BDB_TREASURY_USD = 2e6  # (not the true number)
        self.BDB_TREASURY_OCEAN = 20e6  # (not the true number)

        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0
        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0

    def swapSales(self, consume_sales: float) -> float:
        return self._swap_to_consume_sales_ratio * consume_sales

    def totalSales(self, consume_sales: float) -> float:
        """Given marketplace consume sales, return swap + consume sales"""
        swap_sales = self.swapSales(consume_sales)
        return consume_sales + swap_sales

    def networkRevenue(self, consume_sales: float) -> float:
        """Given marketplace consume sales, return network revenue"""
        swap_sales = self.swapSales(consume_sales)
        return (
            self._percent_consume_sales_for_network * consume_sales
            + self._percent_swap_sales_for_network * swap_sales
        )

    def totalStaked(self, daily_consume_sales: float) -> float:
        total_daily_sales = self.totalSales(daily_consume_sales)
        total_staked = total_daily_sales  # simple heuristic for now
        return total_staked

    def percentToBurn(self) -> float:
        return self._percent_burn

    def percentToOceanDao(self) -> float:
        return 1.0 - self._percent_burn

    def fundamentalsValuation(self, annual_revenue: float) -> float:
        """
        Valuation by price-to-sales (P/S) ratio.
        Annual revenue = sales summed up over the last year (eg per quarter);
          it's *not* based on run rate (sales based on this quarter * 4,
          or projected sales over the next year).
        The market decides P/S based on revenue growth. Higher growth -> higher P/S.
        Most blockchain co's have P/S of 30x-50x, as do startups like Zoom.
        """
        return annual_revenue * self._p_s_ratio

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
        growth_rate: float = self.growth_rate_if_0_sales + mult * (
            1.0 - math.pow(0.5, ratio_RND_to_sales / self.tau)
        )
        return growth_rate
