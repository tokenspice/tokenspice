"""Strategies hold 'magic numbers' related to running sim engine"""
import logging
log = logging.getLogger('simstrategy')

from enforce_typing import enforce_types
import typing

from util.constants import *
from util.mathutil import Range
from util.strutil import StrMixin
    
@enforce_types
class SimStrategy(StrMixin):
    
    def __init__(self):
        """    
        @notes
          Costs are always in USD.
          We want a sim to run for months.
          New agents are added randomly over time.
        """
        #seconds per tick
        self.time_step: int = S_PER_HOUR
        
        #number of ticks between saves
        self.save_interval: int = 1

        #govern total sim time
        max_years = 20
        self.max_ticks: int = max_years * S_PER_YEAR / self.time_step + 10

        #initial # mkts
        self.init_n_marketplaces = 1

        #for computing annualGrowthRate() of # marketplaces, revenue/mktplace
        #-total marketplaces' growth = (1+annualGrowthRate)^2 - 1
        #-so, if we want upper bound of total marketplaces' growth of 50%,
        # we need max_growth_rate = 22.5%.
        #-and, if we want lower bound of total growth of -25%,
        # we need growth_rate_if_0_sales = -11.8%
        self.growth_rate_if_0_sales = -0.118
        self.max_growth_rate = 0.225
        self.tau = 0.6
        
        #note: SimState now has many magic numbers, for simplicity

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

    def setMaxTicks(self, n: int):
        self.max_ticks = n

@enforce_types
class Schedule(StrMixin):
    def __init__(self, interval: int, n_actions: int):
        if SAFETY:
            assert interval > 0
            assert n_actions > 0
        
        self.interval: int = interval # time between actions (s)
        self.n_actions: float = n_actions
    
