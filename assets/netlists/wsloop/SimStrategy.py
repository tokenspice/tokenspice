import math
from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_HOUR

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        #===initialize self.time_step, max_ticks====
        super().__init__()

        #===set base-class values we want for this netlist====
        self.setTimeStep(24 * S_PER_HOUR)
        self.setMaxTime(10, 'years') #typical runs: 10 years, 20 years, 150 years

        #===new attributes specific to this netlist===
        self._marketplace_percent_toll_to_network = 0.002 #magic number

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

        # (taken from constants.py)
        self.TOTAL_OCEAN_SUPPLY = 1.41e9 
        self.INIT_OCEAN_SUPPLY = 0.49 * self.TOTAL_OCEAN_SUPPLY
        self.UNMINTED_OCEAN_SUPPLY = self.TOTAL_OCEAN_SUPPLY - self.INIT_OCEAN_SUPPLY

        self.OPF_TREASURY_USD = 2e6 #(not the true number)
        self.OPF_TREASURY_OCEAN = 200e6 #(not the true number)
        self.OPF_TREASURY_OCEAN_FOR_OCEAN_DAO = 100e6 #(not the true number)
        self.OPF_TREASURY_OCEAN_FOR_OPF_MGMT = self.OPF_TREASURY_OCEAN - self.OPF_TREASURY_OCEAN_FOR_OCEAN_DAO

        self.BDB_TREASURY_USD = 2e6 #(not the true number)
        self.BDB_TREASURY_OCEAN = 20e6  #(not the true number)

        self.pool_weight_DT    = 3.0
        self.pool_weight_OCEAN = 7.0
        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0

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
