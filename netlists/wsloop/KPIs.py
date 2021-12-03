import math
from typing import List

from enforce_typing import enforce_types

from engine import KPIsBase
from util.constants import S_PER_YEAR, S_PER_MONTH, INF
from util.strutil import prettyBigNum

from util.plotutil import (
    YParam,
    arrayToFloatList,
    LOG,
    BOTH,
    MULT1,
    MULT100,
    DIV1M,
    COUNT,
    DOLLAR,
    PERCENT,
)


@enforce_types
class KPIs(
    KPIsBase.KPIsBase
):  # pylint: disable=too-many-public-methods, too-many-instance-attributes
    def __init__(self, ss):
        super().__init__(ss.time_step)
        self.ss = ss

        # for these, append a new value with each tick
        self._granttakers_revenue_per_tick__per_tick: List[float] = []
        self._consume_sales_per_marketplace_per_s__per_tick: List[float] = []
        self._n_marketplaces__per_tick: List[int] = []
        self._total_OCEAN_minted__per_tick: List[float] = []
        self._total_OCEAN_burned__per_tick: List[float] = []
        self._total_OCEAN_minted_USD__per_tick: List[float] = []
        self._total_OCEAN_burned_USD__per_tick: List[float] = []

    def takeStep(self, state):
        super().takeStep(state)  # parent e.g. increments self._tick

        self._granttakers_revenue_per_tick__per_tick.append(
            state.grantTakersSpentAtTick()
        )

        am = state.getAgent("marketplaces1")
        self._consume_sales_per_marketplace_per_s__per_tick.append(
            am.consumeSalesPerMarketplacePerSecond()
        )
        self._n_marketplaces__per_tick.append(am.numMarketplaces())

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
        """# ticks since start of run"""
        assert len(self._consume_sales_per_marketplace_per_s__per_tick) == self._tick
        return self._tick

    # =======================================================================
    # growth rate
    def mktsRNDToSalesRatio(self) -> float:
        """Return the ratio ($ into ocean R&D) / ($ from ocean sales )
        We average over the last month. This is important
        because the grant takers often only get income monthly.
        """
        monthly_RND = self.grantTakersMonthlyRevenueNow()
        monthly_sales = self.monthlyNetworkRevenueNow()
        if monthly_RND == 0.0:
            ratio = 0.0
        else:
            ratio = monthly_RND / monthly_sales
        return ratio

    # =======================================================================
    # revenue numbers: grant takers
    def grantTakersMonthlyRevenueNow(self) -> float:
        ticks_1mo = self._ticksOneMonth()
        rev_per_tick = self._granttakers_revenue_per_tick__per_tick
        return float(sum(rev_per_tick[-ticks_1mo:]))

    # =======================================================================
    # sales numbers: 1 marketplace
    def onemktMonthlyConsumeSalesNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_MONTH
        return self._onemktConsumeSalesOverInterval(t1, t2)

    def onemktAnnualConsumeSalesNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_YEAR
        return self._onemktConsumeSalesOverInterval(t1, t2)

    def onemktAnnualConsumeSalesOneYearAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_YEAR
        t1 = t2 - S_PER_YEAR
        return self._onemktConsumeSalesOverInterval(t1, t2)

    def _onemktConsumeSalesOverInterval(self, t1: int, t2: int) -> float:
        return self._salesOverInterval(t1, t2, self.onemktConsumeSalesPerSecond)

    def onemktConsumeSalesPerSecond(self, tick) -> float:
        """Returns onemkt's sales per second at a given tick"""
        return self._consume_sales_per_marketplace_per_s__per_tick[tick]

    # =======================================================================
    # sales numbers: n marketplaces
    def allmktsMonthlyConsumeSalesNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_MONTH
        return self._allmktsConsumeSalesOverInterval(t1, t2)

    def allmktsAnnualConsumeSalesNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_YEAR
        return self._allmktsConsumeSalesOverInterval(t1, t2)

    def allmktsAnnualConsumeSalesOneYearAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_YEAR
        t1 = t2 - S_PER_YEAR
        return self._allmktsConsumeSalesOverInterval(t1, t2)

    def allmktsConsumeSalesPerSecond(self, tick) -> float:
        """Returns allmkt's sales per second at a given tick"""
        return (
            self._consume_sales_per_marketplace_per_s__per_tick[tick]
            * self._n_marketplaces__per_tick[tick]
        )

    def _allmktsConsumeSalesOverInterval(self, t1: int, t2: int) -> float:
        return self._salesOverInterval(t1, t2, self.allmktsConsumeSalesPerSecond)

    # =======================================================================
    # revenue numbers: ocean community
    def monthlyNetworkRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_MONTH
        return self._networkRevenueOverInterval(t1, t2)

    def annualNetworkRevenueNow(self) -> float:
        t2 = self.elapsedTime()
        t1 = t2 - S_PER_YEAR
        return self._networkRevenueOverInterval(t1, t2)

    def oceanMonthlyRevenueOneMonthAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_MONTH
        t1 = t2 - S_PER_MONTH
        return self._networkRevenueOverInterval(t1, t2)

    def oceanAnnualRevenueOneYearAgo(self) -> float:
        t2 = self.elapsedTime() - S_PER_YEAR
        t1 = t2 - S_PER_YEAR
        return self._networkRevenueOverInterval(t1, t2)

    def _networkRevenueOverInterval(self, t1: int, t2: int) -> float:
        return self._salesOverInterval(t1, t2, self.networkRevenuePerSecond)

    def networkRevenuePerSecond(self, tick) -> float:
        """Returns Network Revenue per second at a given tick"""
        n = self._n_marketplaces__per_tick[tick]
        consume1 = self._consume_sales_per_marketplace_per_s__per_tick[tick]
        consumeN = n * consume1
        network_revenue = self.ss.networkRevenue(consumeN)
        return network_revenue

    # =======================================================================
    def _salesOverInterval(self, t1: int, t2: int, revenuePerSecondFunc) -> float:
        """
        Helper function for _{onemkt, allmkts, ocean}salesOverInterval().

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

    # =======================================================================
    # revenue growth numbers: ocean community
    def monthlyNetworkRevenueGrowth(self) -> float:
        rev1 = self.oceanMonthlyRevenueOneMonthAgo()
        rev2 = self.monthlyNetworkRevenueNow()
        if rev1 == 0.0:
            return INF
        g = rev2 / rev1 - 1.0
        return g

    def annualNetworkRevenueGrowth(self) -> float:
        rev1 = self.oceanAnnualRevenueOneYearAgo()
        rev2 = self.annualNetworkRevenueNow()
        if rev1 == 0.0:
            return INF
        g = rev2 / rev1 - 1.0
        return g

    # =======================================================================
    # OCEAN minted & burned per month, as a count (#) and as USD ($)
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

        return O_per_tick[-1] - O_per_tick[-(ticks_1mo + 1)]

    def _ticksOneMonth(self) -> int:
        """Number of ticks in one month"""
        ticks: int = math.ceil(S_PER_MONTH / float(self._time_step))
        return ticks


@enforce_types
def netlist_createLogData(
    state,
):  # pylint: disable=too-many-statements, too-many-locals
    """pass this to SimEngine.__init__() as argument `netlist_createLogData`"""
    F = False
    ss = state.ss
    kpis = state.kpis

    s = []  # for console logging
    dataheader = []  # for csv logging: list of string
    datarow = []  # for csv logging: list of float

    # SimEngine already logs: Tick, Second, Min, Hour, Day, Month, Year
    # So we log other things...

    am = state.getAgent("marketplaces1")
    # s += ["; # mkts=%s" % prettyBigNum(am._n_marketplaces,F)]
    dataheader += ["Num_mkts"]
    datarow += [am._n_marketplaces]

    onemkt_cons_sales_mo = kpis.onemktMonthlyConsumeSalesNow()
    onemkt_cons_sales_yr = kpis.onemktAnnualConsumeSalesNow()
    # s += ["; 1mkt_cons_sales/mo=$%s,/yr=$%s" %
    #      (prettyBigNum(onemkt_cons_sales_mo,F), prettyBigNum(onemkt_cons_sales_yr,F))]
    dataheader += ["onemkt_cons_sales/mo", "onemkt_cons_sales/yr"]
    datarow += [onemkt_cons_sales_mo, onemkt_cons_sales_yr]

    allmkts_cons_sales_mo = kpis.allmktsMonthlyConsumeSalesNow()
    allmkts_cons_sales_yr = kpis.allmktsAnnualConsumeSalesNow()
    # s += ["; allmkts_cons_sales/mo=$%s,/yr=$%s" %
    #      (prettyBigNum(allmkts_cons_sales_mo,F), prettyBigNum(allmkts_cons_sales_yr,F))]
    dataheader += ["allmkts_cons_sales/mo", "allmkts_cons_sales/yr"]
    datarow += [allmkts_cons_sales_mo, allmkts_cons_sales_yr]

    allmkts_tot_sales_day = ss.totalSales(allmkts_cons_sales_mo / 30.5)
    allmkts_tot_sales_mo = ss.totalSales(allmkts_cons_sales_mo)
    allmkts_tot_sales_yr = ss.totalSales(allmkts_cons_sales_yr)
    # s += ["; allmkts_tot_sales/mo=$%s,/yr=$%s" %
    #      (prettyBigNum(allmkts_tot_sales_mo,F), prettyBigNum(allmkts_tot_sales_yr,F))]
    dataheader += [
        "allmkts_tot_sales/day",
        "allmkts_tot_sales/mo",
        "allmkts_tot_sales/yr",
    ]
    datarow += [allmkts_tot_sales_day, allmkts_tot_sales_mo, allmkts_tot_sales_yr]

    tot_staked = ss.totalStaked(allmkts_tot_sales_day)
    s += ["; tot_staked=$%s" % prettyBigNum(tot_staked, F)]
    dataheader += ["tot_staked"]
    datarow += [tot_staked]

    network_rev_mo = kpis.monthlyNetworkRevenueNow()
    network_rev_yr = kpis.annualNetworkRevenueNow()
    # s += ["; network_rev/mo=$%sm,/yr=$%s" %
    #      (prettyBigNum(network_rev_mo,F), prettyBigNum(network_rev_yr,F))]
    s += ["; network_rev/mo=$%sm" % prettyBigNum(network_rev_mo, F)]
    dataheader += ["network_rev/mo", "network_rev/yr"]
    datarow += [network_rev_mo, network_rev_yr]

    dataheader += ["network_rev_growth/mo", "network_rev_growth/yr"]
    datarow += [kpis.monthlyNetworkRevenueGrowth(), kpis.annualNetworkRevenueGrowth()]

    overall_valuation = state.overallValuation()
    dataheader += [
        "overall_valuation",
        "fundamentals_valuation",
        "speculation_valuation",
    ]
    s += ["; valn=$%s" % prettyBigNum(overall_valuation, F)]
    datarow += [
        overall_valuation,
        state.fundamentalsValuation(),
        state.speculationValuation(),
    ]

    tot_O_supply = state.OCEANsupply()
    s += ["; #OCEAN=%s" % prettyBigNum(tot_O_supply)]
    dataheader += ["tot_OCEAN_supply", "tot_OCEAN_minted", "tot_OCEAN_burned"]
    datarow += [tot_O_supply, state.totalOCEANminted(), state.totalOCEANburned()]

    dataheader += ["OCEAN_minted/mo", "OCEAN_burned/mo"]
    datarow += [kpis.OCEANmintedPrevMonth(), kpis.OCEANburnedPrevMonth()]

    dataheader += ["OCEAN_minted_USD/mo", "OCEAN_burned_USD/mo"]
    datarow += [kpis.OCEANmintedInUSDPrevMonth(), kpis.OCEANburnedInUSDPrevMonth()]

    O_price = state.OCEANprice()
    if O_price <= 10.0:
        s += ["; $OCEAN=$%.3f" % O_price]
    else:
        s += ["; $OCEAN=$%s" % prettyBigNum(O_price, F)]
    dataheader += ["OCEAN_price"]
    datarow += [O_price]

    gt_rev = kpis.grantTakersMonthlyRevenueNow()
    # s += ["; r&d/mo=$%s" % prettyBigNum(gt_rev,F)]
    dataheader += ["RND/mo"]
    datarow += [gt_rev]

    ratio = kpis.mktsRNDToSalesRatio()
    growth = ss.annualMktsGrowthRate(ratio)
    # s += ["; r&d/sales ratio=%.2f, growth(ratio)=%.3f" % (ratio, growth)]
    dataheader += ["rnd_to_cons_sales_ratio", "mkts_annual_growth_rate"]
    datarow += [ratio, growth]

    dao = state.getAgent("ocean_dao")  # RouterAgent
    dao_USD = dao.monthlyUSDreceived(state)
    dao_OCEAN = dao.monthlyOCEANreceived(state)
    dao_OCEAN_in_USD = dao_OCEAN * O_price
    dao_total_in_USD = dao_USD + dao_OCEAN_in_USD
    # s += ["; dao:[$%s/mo,%s OCEAN/mo ($%s),total=$%s/mo]" %
    #      (prettyBigNum(dao_USD,F), prettyBigNum(dao_OCEAN,F),
    #       prettyBigNum(dao_OCEAN_in_USD,F), prettyBigNum(dao_total_in_USD,F))]
    dataheader += [
        "dao_USD/mo",
        "dao_OCEAN/mo",
        "dao_OCEAN_in_USD/mo",
        "dao_total_in_USD/mo",
    ]
    datarow += [dao_USD, dao_OCEAN, dao_OCEAN_in_USD, dao_total_in_USD]

    # done
    return s, dataheader, datarow


@enforce_types
def netlist_plotInstructions(header: List[str], values):
    """
    Describe how to plot the information.
    tsp.do_plot() calls this

    :param: header: List[str] holding 'Tick', 'Second', ...
    :param: values: 2d array of float [tick_i, valuetype_i]
    :return: x_label: str -- e.g. "Day", "Month", "Year"
    :return: x: List[float] -- x-axis info on how to plot
    :return: y_params: List[YParam] -- y-axis info on how to plot
    """
    x_label = "Year"
    x = arrayToFloatList(values[:, header.index(x_label)])

    y_params = [
        YParam(["OCEAN_price"], [""], "OCEAN Price", LOG, MULT1, DOLLAR),
        # YParam(["network_rev_growth/yr"], [""],
        #        "Annual Network Revenue Growth", BOTH, MULT100, PERCENT),
        YParam(
            ["overall_valuation", "fundamentals_valuation", "speculation_valuation"],
            ["Overall", "Fundamentals (P/S=30)", "Speculation"],
            "Valuation",
            LOG,
            DIV1M,
            DOLLAR,
        ),
        YParam(
            ["dao_USD/mo", "dao_OCEAN_in_USD/mo", "dao_total_in_USD/mo"],
            [
                "Income as USD (ie network revenue)",
                "Income as OCEAN (ie from 51%; priced in USD)",
                "Total Income",
            ],
            "Monthly OceanDAO Income",
            LOG,
            DIV1M,
            DOLLAR,
        ),
        YParam(
            ["network_rev/yr", "allmkts_cons_sales/yr", "allmkts_tot_sales/yr"],
            [
                "Network Revenue",
                "All marketplaces consume sales",
                "All marketplaces total sales",
            ],
            "Annual Revenue or Sales",
            LOG,
            DIV1M,
            DOLLAR,
        ),
        YParam(
            ["tot_staked"],
            ["USD worth of OCEAN"],
            "Total OCEAN Staked (in USD)",
            LOG,
            DIV1M,
            DOLLAR,
        ),
        YParam(
            ["tot_OCEAN_supply", "tot_OCEAN_minted", "tot_OCEAN_burned"],
            ["Total supply", "Tot # Minted", "Tot # Burned"],
            "OCEAN Token Count",
            BOTH,
            DIV1M,
            COUNT,
        ),
        YParam(
            ["OCEAN_minted/mo", "OCEAN_burned/mo"],
            ["# Minted/mo", "# Burned/mo"],
            "Monthly # OCEAN Minted & Burned",
            BOTH,
            DIV1M,
            COUNT,
        ),
        YParam(
            ["rnd_to_cons_sales_ratio", "mkts_annual_growth_rate"],
            ["R&D/consume_sales ratio", "Marketplaces annual growth rate"],
            "R&D/Sales Ratio and Marketplaces Growth Rate",
            BOTH,
            MULT100,
            PERCENT,
        ),
        YParam(["RND/mo"], [""], "Monthly R&D Spend", BOTH, DIV1M, DOLLAR),
        # YParam(["OCEAN_burned_USD/mo", "OCEAN_minted_USD/mo"],
        #       ["$ of OCEAN Burned/mo", "$ of OCEAN Minted/mo"],
        #       "Monthly OCEAN (in USD) Minted & Burned", LOG, DIV1M, DOLLAR),
        # YParam(["OCEAN_burned_USD/mo", "network_rev/mo", "allmkts_total_sales/mo"],
        #       ["$ OCEAN Burned monthly", "Ocean monthly revenue", "Marketplaces monthly sales"],
        #       "Monthly OCEAN Burned and Revenues", LOG, DIV1M, DOLLAR),
    ]

    return (x_label, x, y_params)
