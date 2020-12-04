import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('minteragents')

import enforce
import unittest

from engine import BaseAgent, SimState, SimStrategy
from engine.MinterAgents import *
from util.constants import BITCOIN_NUM_HALF_LIVES, \
    S_PER_DAY, S_PER_MONTH, S_PER_YEAR

@enforce.runtime_validation
class MinterAgentsTest(unittest.TestCase):

    #comment out some unused agents for now, simply for faster unit tests
    
    # def testOCEANLinearMinterAgent(self):
    #     ss = SimStrategy.SimStrategy()
    #     assert hasattr(ss, 'time_step')
    #     ss.time_step = 2

    #     state = SimState.SimState(ss)
        
    #     class SimpleAgent(BaseAgent):
    #         def takeStep(self, state):
    #             pass
    #     state.agents["a1"] = a1 = SimpleAgent("a1", 0.0, 0.0)

    #     #default
    #     minter = OCEANLinearMinterAgent(
    #         "minter", 
    #         receiving_agent_name="a1",
    #         total_OCEAN_to_mint=20.0,
    #         s_between_mints=4, n_mints=2) 
    #     self.assertEqual(minter.USD(), 0.0)
    #     self.assertEqual(minter.OCEAN(), 0.0)
    #     self.assertEqual(state._total_OCEAN_minted, 0.0)

    #     minter.takeStep(state); state.tick += 1 #tick=1 (2 s elapsed), 1st mint
    #     self.assertEqual(minter.OCEAN(), 0.0)
    #     self.assertEqual(a1.OCEAN(), 10.0)
    #     self.assertEqual(state._total_OCEAN_minted, 10.0)
        
    #     minter.takeStep(state); state.tick += 1 #tick=2 (4 s elapsed), noop
    #     self.assertEqual(minter.OCEAN(), 0.0)
    #     self.assertEqual(a1.OCEAN(), 10.0)
    #     self.assertEqual(state._total_OCEAN_minted, 10.0)
        
    #     minter.takeStep(state); state.tick += 1 #tick=3 (6 s elapsed), 2nd mint
    #     self.assertEqual(minter.OCEAN(), 0.0)
    #     self.assertEqual(a1.OCEAN(), 20.0)
    #     self.assertEqual(state._total_OCEAN_minted, 20.0)
        
    #     minter.takeStep(state); state.tick += 1 #tick=4 (8 s elapsed), noop
    #     self.assertEqual(minter.OCEAN(), 0.0)
    #     self.assertEqual(a1.OCEAN(), 20.0)
    #     self.assertEqual(state._total_OCEAN_minted, 20.0)

    #     for i in range(10):
    #         minter.takeStep(state); state.tick += 1 #tick=14 (28 s elapsed), noop
    #     self.assertEqual(minter.OCEAN(), 0.0)
    #     self.assertEqual(a1.OCEAN(), 20.0)
    #     self.assertEqual(state._total_OCEAN_minted, 20.0)

    # def test_funcMinter_exp(self):
    #     func = ExpFunc(H=4.0)
    #     self._test_funcMinter(func)

    def test_funcMinter_rampedExp(self):
        func = RampedExpFunc(H=4.0,
                             T0=0.0, T1=0.5, T2=1.0, T3=2.0,
                             M1=0.10, M2=0.25, M3=0.50)
        self._test_funcMinter(func)
        
    def _test_funcMinter(self,  func):
        #Simulate with realistic conditions: half-life, OCEAN to mint,
        #  target num half-lives (34, like Bitcoin).
        #Main check is to see whether we hit expected # years passed.
        #Not realistic here: time step and s_between_mints. Both are set higher
        # for unittest speed. They shouldn't affect the main check.
        
        manual_test = False #HACK if True
        do_log_plot = False #if manual_test, linear or log plot?
        max_year = 5 #if manual_test, stop earlier?
        
        ss = SimStrategy.SimStrategy()
        assert hasattr(ss, 'time_step')
        if manual_test:
            ss.time_step = S_PER_DAY
            s_between_mints = S_PER_DAY
        else:
            ss.time_step = 100 * S_PER_DAY
            s_between_mints = S_PER_YEAR

        state = SimState.SimState(ss)
        
        class SimpleAgent(BaseAgent):
            def takeStep(self, state):
                pass
        state.agents["a1"] = a1 = SimpleAgent("a1", 0.0, 0.0)

        #base            
        minter = OCEANFuncMinterAgent(
            "minter", 
            receiving_agent_name="a1",
            total_OCEAN_to_mint=700e6,
            s_between_mints=s_between_mints, 
            func=func)
        
        self.assertEqual(minter.USD(), 0.0)
        self.assertEqual(minter.OCEAN(), 0.0)
        self.assertEqual(minter._receiving_agent_name, "a1")
        self.assertEqual(minter._total_OCEAN_to_mint, 700e6)
        self.assertEqual(minter._tick_previous_mint, None)
        self.assertEqual(minter._OCEAN_left_to_mint, 700e6)
        self.assertEqual(minter._func._H, 4.0)
        
        self.assertEqual(state._total_OCEAN_minted, 0.0)
        
        #run for full length
        years, OCEAN_left, OCEAN_minted = [], [], []
        
        years.append(0.0)
        OCEAN_left.append(minter._OCEAN_left_to_mint)
        OCEAN_minted.append(minter.OCEANminted())

        stopped_bc_inf_loop = False
        while True:
            minter.takeStep(state)
            state.tick += 1

            year = state.tick * ss.time_step / S_PER_YEAR
            
            years.append(year)
            OCEAN_left.append(minter._OCEAN_left_to_mint)
            OCEAN_minted.append(minter.OCEANminted())

            mo = state.tick * ss.time_step / S_PER_MONTH
            if manual_test:
                print(f"tick=%d (mo=%.2f,yr=%.3f), OCEAN_left=%.4g,minted=%.4f"
                      % (state.tick, mo, year, minter._OCEAN_left_to_mint,
                         minter.OCEANminted()))
            
            if minter._OCEAN_left_to_mint == 0.0:
                break
            if manual_test and year > max_year:
                break
            if year > 1000: #avoid infinite loop
                stopped_bc_inf_loop = True
                break
        self.assertFalse(stopped_bc_inf_loop)
        if not (manual_test and year > max_year):
            self.assertEqual(minter._OCEAN_left_to_mint, 0.0)

        #main check: did we hit target # years?
        #HACK self.assertTrue(130.0 <= year <= 140.0) 

        if not manual_test:
            return
    
        #plot
        from matplotlib import pyplot, ticker
        
        fig, ax = pyplot.subplots()
        ax.set_xlabel("Year")
        
        #ax.plot(years, OCEAN_left, label="OCEAN left")
        #ax.set_ylabel("# OCEAN left")
        
        ax.plot(years, OCEAN_minted, label="OCEAN minted")
        ax.set_ylabel("# OCEAN minted")

        if do_log_plot:
            pyplot.yscale('log')       
            ax.get_yaxis().set_major_formatter(ticker.ScalarFormatter()) # turn off exponential notation
            
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2g'))

        pyplot.show() #popup
