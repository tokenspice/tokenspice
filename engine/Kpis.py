import logging
log = logging.getLogger('kpis')

import enforce

from util import valuation
from util.constants import * 

@enforce.runtime_validation
class KPIs:
    def __init__(self, time_step: int):
        self._time_step = time_step #seconds per tick
        
        #for these, append a new value with each tick
        self._granttakers_revenue_per_tick__per_tick = []
        
        self._revenue_per_marketplace_per_s__per_tick = []
        self._n_marketplaces__per_tick = []
        self._marketplace_percent_toll_to_ocean__per_tick = []
        
        self._total_OCEAN_minted__per_tick = []
        self._total_OCEAN_burned__per_tick = []
        self._total_OCEAN_minted_USD__per_tick = []
        self._total_OCEAN_burned_USD__per_tick = []

    def takeStep(self, state):        
        self._granttakers_revenue_per_tick__per_tick.append(
            state.grantTakersSpentAtTick())
        
        am = state.getAgent("marketplaces1")
        self._revenue_per_marketplace_per_s__per_tick.append(
            am.revenuePerMarketplacePerSecond())
        self._n_marketplaces__per_tick.append(am.numMarketplaces())
        self._marketplace_percent_toll_to_ocean__per_tick.append(
            state.marketplacePercentTollToOcean())

        O_minted = state.totalOCEANminted()
        O_burned = state.totalOCEANburned()
        self._total_OCEAN_minted__per_tick.append(O_minted)
        self._total_OCEAN_burned__per_tick.append(O_burned)

        O_price = state.OCEANprice()
        O_minted_USD = O_minted * O_price
        O_burned_USD = state.totalOCEANburnedUSD()
        self._total_OCEAN_minted_USD__per_tick.append(O_minted_USD)
        self._total_OCEAN_burned_USD__per_tick.append(O_burned_USD)

    def tick(self) -> int:
        """# ticks that have elapsed since the beginning of the run"""
        return len(self._revenue_per_marketplace_per_s__per_tick)

    def elapsedTime(self) -> int:
        """Elapsed time (seconds) since the beginning of the run"""
        return self.tick() * self._time_step
        
    #=======================================================================
    #growth rate
    def mktsRNDToSalesRatio(self) -> float:
        """Return the ratio ($ into ocean R&D) / ($ from ocean sales )
        We average over the last month. This is important
        because the grant takers often only get income monthly.
        """
        monthly_RND = self.grantTakersMonthlyRevenueNow()
        monthly_sales = self.oceanMonthlyRevenueNow()
        if monthly_RND == 0.0:
            ratio = 0.0
        else:
            ratio = monthly_RND / monthly_sales
        return ratio
        
    #=======================================================================
    #revenue numbers: grant takers
    def grantTakersMonthlyRevenueNow(self) -> float:
        ticks_1mo = self._ticksOneMonth()
        rev_per_tick = self._granttakers_revenue_per_tick__per_tick
        return float(sum(rev_per_tick[-ticks_1mo:]))
        
    #=======================================================================
    #revenue numbers: 1 marketplace
    def onemktMonthlyRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_MONTH
        return self._onemktRevenueOverInterval(t1, t2)
    
    def onemktAnnualRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_YEAR
        return self._onemktRevenueOverInterval(t1, t2)
    
    def onemktAnnualRevenueOneYearAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_YEAR
        t1 = t2 - S_PER_YEAR
        return self._onemktRevenueOverInterval(t1, t2)
            
    def _onemktRevenueOverInterval(self, t1: int, t2:int) -> float:
        return self._revenueOverInterval(t1, t2, self.onemktRevenuePerSecond)

    def onemktRevenuePerSecond(self, tick) -> float:
        """Returns onemkt's revenue per second at a given tick"""
        return self._revenue_per_marketplace_per_s__per_tick[tick]

    #=======================================================================
    #revenue numbers: n marketplaces
    def allmktsMonthlyRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_MONTH
        return self._allmktsRevenueOverInterval(t1, t2)
    
    def allmktsAnnualRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_YEAR
        return self._allmktsRevenueOverInterval(t1, t2)
    
    def allmktsAnnualRevenueOneYearAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_YEAR
        t1 = t2 - S_PER_YEAR
        return self._allmktsRevenueOverInterval(t1, t2)

    def allmktsRevenuePerSecond(self, tick) -> float:
        """Returns allmkt's revenue per second at a given tick"""
        return self._revenue_per_marketplace_per_s__per_tick[tick] \
            * self._n_marketplaces__per_tick[tick]
            
    def _allmktsRevenueOverInterval(self, t1: int, t2:int) -> float:
        return self._revenueOverInterval(t1, t2, self.allmktsRevenuePerSecond)
    
    #=======================================================================
    #revenue numbers: ocean community
    def oceanMonthlyRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_MONTH
        return self._oceanRevenueOverInterval(t1, t2)
    
    def oceanAnnualRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_YEAR
        return self._oceanRevenueOverInterval(t1, t2)
    
    def oceanMonthlyRevenueOneMonthAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_MONTH
        t1 = t2 - S_PER_MONTH
        return self._oceanRevenueOverInterval(t1, t2)
    
    def oceanAnnualRevenueOneYearAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_YEAR
        t1 = t2 - S_PER_YEAR
        return self._oceanRevenueOverInterval(t1, t2)
            
    def _oceanRevenueOverInterval(self, t1: int, t2:int) -> float:
        return self._revenueOverInterval(t1, t2, self.oceanRevenuePerSecond)
    
    def oceanRevenuePerSecond(self, tick) -> float:
        """Returns ocean's revenue per second at a given tick"""
        return self._revenue_per_marketplace_per_s__per_tick[tick] \
            * self._n_marketplaces__per_tick[tick] \
            * self._marketplace_percent_toll_to_ocean__per_tick[tick]
    
    #=======================================================================
    def _revenueOverInterval(self, t1: int, t2:int, revenuePerSecondFunc) \
        -> float:
        """
        Helper function for _{onemkt, allmkts, ocean}revenueOverInterval().

        In time from t1 to t2 (both in # seconds since start), 
        how much $ was earned, using the revenuePerSecondFunc.
        """
        assert t2 > t1
        tick1: int = max(0, math.floor(t1 / self._time_step))
        tick2: int = min(self.tick(), math.floor(t2 / self._time_step) + 1) 
        rev = 0.0
        for tick_i in range(tick1, tick2):
            rev_this_s = revenuePerSecondFunc(tick_i)
            
            start_s = max(t1, tick_i * self._time_step)
            end_s = min(t2, (tick_i + 1) * self._time_step - 1)
            n_s = end_s - start_s + 1
            rev_this_tick = rev_this_s * n_s
            
            rev += rev_this_tick
        return rev
        
    #=======================================================================
    #revenue growth numbers: ocean community
    def oceanMonthlyRevenueGrowth(self) -> float:
        rev1 = self.oceanMonthlyRevenueOneMonthAgo()
        rev2 = self.oceanMonthlyRevenueNow()
        if rev1 == 0.0:
            return INF
        g = rev2 / rev1 - 1.0
        return g
    
    def oceanAnnualRevenueGrowth(self) -> float:
        rev1 = self.oceanAnnualRevenueOneYearAgo()
        rev2 = self.oceanAnnualRevenueNow()
        if rev1 == 0.0:
            return INF
        g = rev2 / rev1 - 1.0
        return g
        
    @enforce.runtime_validation
    def valuationPS(self, p_s_ratio: float) -> float:
        """Use Price/Sales ratio to compute valuation."""
        annual_revenue = self.oceanAnnualRevenueNow()
        v = valuation.firmValuationPS(annual_revenue, p_s_ratio)
        return v

    #=======================================================================
    #OCEAN minted & burned per month, as a count (#) and as USD ($)
    def OCEANmintedPrevMonth(self) -> float:
        return self._OCEANchangePrevMonth(self._total_OCEAN_minted__per_tick)
           
    def OCEANburnedPrevMonth(self) -> float:
        return self._OCEANchangePrevMonth(self._total_OCEAN_burned__per_tick)
    
    def OCEANmintedInUSDPrevMonth(self) -> float:
        return self._OCEANchangePrevMonth(self._total_OCEAN_minted_USD__per_tick)
    
    def OCEANburnedInUSDPrevMonth(self) -> float:
        return self._OCEANchangePrevMonth(self._total_OCEAN_burned_USD__per_tick)

    def _OCEANchangePrevMonth(self, O_per_tick) -> float:
        ticks_total = len(O_per_tick)

        if ticks_total == 0:
            return 0.0
        
        ticks_1mo = self._ticksOneMonth()
        if ticks_total <= ticks_1mo:
            return O_per_tick[-1]
        
        return O_per_tick[-1] - O_per_tick[-(ticks_1mo+1)]

    def _ticksOneMonth(self) -> int:
        """Number of ticks in one month"""
        ticks: int = math.ceil(S_PER_MONTH / float(self._time_step))
        return ticks
