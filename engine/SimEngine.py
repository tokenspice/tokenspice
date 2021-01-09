import logging
log = logging.getLogger('master')

from enforce_typing import enforce_types # type: ignore[import]
import os

from util import valuation
from util.constants import S_PER_MIN, S_PER_HOUR, S_PER_DAY, S_PER_MONTH, S_PER_YEAR
from util.strutil import prettyBigNum
import engine.SimState as SimState
from engine.SimStrategy import SimStrategy

@enforce_types
class SimEngine(object):
    """
    @description
      Runs a simulation.
      
    @attributes
      ss -- simulation strategy parameters
      output_dir -- directory of where results are stored
      state -- None or SimState -- start from scratch (if None) or 
       from a pre-loaded state (e.g. with SimState.loadSimState).
    """

    def __init__(self, ss: SimStrategy, output_dir: str, state = None):
        self.state = state
        if self.state is None:
            self.state = SimState.SimState(ss)
        self.output_dir = output_dir
        self.output_csv = "data.csv" #magic number

        assert len(self.state.agents) > 0
        
    def run(self):
        """
        @description
          Runs the simulation!  This is the main work routine.
        
        @return
           <<none>> but it continually generates an output csv output_dir
        """
        log.info("Begin.")
        log.info(str(self.state.ss) + "\n")

        while True:
            self.takeStep()
            if self.doStop():
                break
            self.state.tick += 1 #could be e.g. 10 or 100 or ..
        log.info("Done")

    def takeStep(self) -> None:
        """Run one tick, updates self.state"""
        log.debug("=============================================")
        log.debug("Tick=%d: begin" % (self.state.tick))
        
        if (self.elapsedSeconds() % S_PER_DAY) == 0:
            str_data, csv_data = self.createLogData()
            log.info(str_data)
            self.logToCsv(csv_data)
                
        #main work
        self.state.takeStep()
        
        log.debug("=============================================")
        log.debug("Tick=%d: done" % self.state.tick)

    def createLogData(self):
        """Compute this iter's status, and output in forms ready
        for console logging and csv logging."""
        F = False
        state = self.state
        ss = state.ss
        kpis = state.kpis

        s = [] #for console logging
        dataheader = [] # for csv logging: list of string
        datarow = [] #for csv logging: list of float

        s += ["Tick=%d" % (state.tick)]
        dataheader += ["Tick"]
        datarow += [state.tick]

        es = float(self.elapsedSeconds())
        emi, eh, ed, emo, ey = es/S_PER_MIN, es/S_PER_HOUR, es/S_PER_DAY, \
                               es/S_PER_MONTH,es/S_PER_YEAR
        s += [" (%.1f h, %.1f d, %.1f mo)" % \
              (eh, ed, emo)] 
        dataheader += ["Second", "Min", "Hour", "Day", "Month", "Year"]
        datarow += [es, emi, eh, ed, emo, ey]
        
        # am = state.getAgent("marketplaces1")
        # #s += ["; # mkts=%s" % prettyBigNum(am._n_marketplaces,F)]
        # dataheader += ["Num_mkts"]
        # datarow += [am._n_marketplaces]

        onemkt_rev_mo = kpis.onemktMonthlyRevenueNow()
        onemkt_rev_yr = kpis.onemktAnnualRevenueNow()
        #s += ["; 1mkt_rev/mo=$%s,/yr=$%s" %
        #      (prettyBigNum(onemkt_rev_mo,F), prettyBigNum(onemkt_rev_yr,F))]
        dataheader += ["onemkt_rev/mo", "onemkt_rev/yr"]
        datarow += [onemkt_rev_mo, onemkt_rev_yr]

        allmkts_rev_mo = kpis.allmktsMonthlyRevenueNow()
        allmkts_rev_yr = kpis.allmktsAnnualRevenueNow()
        #s += ["; allmkts_rev/mo=$%s,/yr=$%s" %
        #      (prettyBigNum(allmkts_rev_mo,F), prettyBigNum(allmkts_rev_yr,F))]
        dataheader += ["allmkts_rev/mo", "allmkts_rev/yr"]
        datarow += [allmkts_rev_mo, allmkts_rev_yr]        

        ocean_rev_mo = kpis.oceanMonthlyRevenueNow()
        ocean_rev_yr = kpis.oceanAnnualRevenueNow()
        #s += ["; ocean_rev/mo=$%sm,/yr=$%s" %
        #      (prettyBigNum(ocean_rev_mo,F), prettyBigNum(ocean_rev_yr,F))]
        s += ["; ocean_rev/mo=$%sm" % prettyBigNum(ocean_rev_mo,F)]
        dataheader += ["ocean_rev/mo", "ocean_rev/yr"]
        datarow += [ocean_rev_mo, ocean_rev_yr]

        dataheader += ["ocean_rev_growth/mo", "ocean_rev_growth/yr"]
        datarow += [kpis.oceanMonthlyRevenueGrowth(),
                    kpis.oceanAnnualRevenueGrowth()]

        ps30_valuation = kpis.valuationPS(30.0)
        dataheader += ["ps30_valuation"]
        datarow += [ps30_valuation]

        ov = state.overallValuation()
        dataheader += ["overall_valuation", "fundamentals_valuation",
                       "speculation_valuation"]
        s += ["; valn=$%s" % prettyBigNum(ov,F)]
        datarow += [ov, state.fundamentalsValuation(),
                    state.speculationValuation()]

        tot_O_supply = state.OCEANsupply()
        s += ["; #OCEAN=%s" % prettyBigNum(tot_O_supply)]
        dataheader += ["tot_OCEAN_supply","tot_OCEAN_minted","tot_OCEAN_burned"]
        datarow += [tot_O_supply,
                    state.totalOCEANminted(),
                    state.totalOCEANburned()]

        dataheader += ["OCEAN_minted/mo","OCEAN_burned/mo"]
        datarow += [kpis.OCEANmintedPrevMonth(),
                    kpis.OCEANburnedPrevMonth()]

        dataheader += ["OCEAN_minted_USD/mo","OCEAN_burned_USD/mo"]
        datarow += [kpis.OCEANmintedInUSDPrevMonth(),
                    kpis.OCEANburnedInUSDPrevMonth()]

        O_price = state.OCEANprice()
        if O_price <= 10.0:
            s += ["; $OCEAN=$%.3f" % O_price]
        else:
            s += ["; $OCEAN=$%s" % prettyBigNum(O_price,F)]
        dataheader += ["OCEAN_price"]
        datarow += [O_price]

        gt_rev = kpis.grantTakersMonthlyRevenueNow()
        #s += ["; r&d/mo=$%s" % prettyBigNum(gt_rev,F)]
        dataheader += ["RND/mo"]
        datarow += [gt_rev]

        ratio = kpis.mktsRNDToSalesRatio()
        growth = ss.annualMktsGrowthRate(ratio)
        #s += ["; r&d/sales ratio=%.2f, growth(ratio)=%.3f" % (ratio, growth)]
        dataheader += ["rnd_to_sales_ratio", "mkts_annual_growth_rate"]
        datarow += [ratio, growth]
        
        dao = state.getAgent("ocean_dao") #RouterAgent
        dao_USD = dao.monthlyUSDreceived(state)
        dao_OCEAN = dao.monthlyOCEANreceived(state)
        dao_OCEAN_in_USD = dao_OCEAN * O_price
        dao_total_in_USD = dao_USD + dao_OCEAN_in_USD
        #s += ["; dao:[$%s/mo,%s OCEAN/mo ($%s),total=$%s/mo]" %
        #      (prettyBigNum(dao_USD,F), prettyBigNum(dao_OCEAN,F),
        #       prettyBigNum(dao_OCEAN_in_USD,F), prettyBigNum(dao_total_in_USD,F))]
        dataheader += ["dao_USD/mo", "dao_OCEAN/mo", "dao_OCEAN_in_USD/mo",
                       "dao_total_in_USD/mo"]
        datarow += [dao_USD, dao_OCEAN, dao_OCEAN_in_USD, dao_total_in_USD]

        #package results up
        str_data = "".join(s)
        csv_data = (dataheader, datarow)
        return str_data, csv_data

    def logToCsv(self, csv_data) -> None:
        if self.output_dir is None:
            return
                
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
            
        full_filename = os.path.join(self.output_dir, self.output_csv)
        (dataheader, datarow) = csv_data
        
        #if needed, create file and add header
        if not os.path.exists(full_filename):
            with open(full_filename,'w+') as f:
                f.write(", ".join(dataheader) + "\n")
            
        #add in row
        datarow_s = ['%g' % dataval for dataval in datarow]
        with open(full_filename,'a+') as f:
            f.write(", ".join(datarow_s) + "\n")

    def elapsedSeconds(self) -> int:
        return self.state.tick * self.state.ss.time_step

    def doStop(self) -> bool:
        if self.state.tick >= self.state.ss.max_ticks:
            log.info("Stop: tick (%d) >= max" % self.state.tick)
            return True
        
        return False
            
