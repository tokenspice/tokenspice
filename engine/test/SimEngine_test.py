import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('master')

import enforce
import os
import shutil
import unittest

from engine.SimEngine import SimEngine
from engine.SimStrategy import SimStrategy
import engine.SimState as SimState
from util.constants import SAFETY

PATH1 = '/tmp/test_outpath1'

@enforce.runtime_validation
class SimEngineTest(unittest.TestCase):

    def setUp(self):        
        #possible cleanup from prev run
        if os.path.exists(PATH1): shutil.rmtree(PATH1)
                
    def testRunLonger(self):
        self._testRunLonger(15)
        
    def _testRunLonger(self, max_ticks):
        ss = SimStrategy()
        ss.setMaxTicks(max_ticks)
        
        master = SimEngine(ss, PATH1)

        master.run()        
        
    def testRunEngine(self):
        ss = SimStrategy()
        ss.setMaxTicks(3)

        master = SimEngine(ss, PATH1)
        
        master.run()
        self.assertTrue(os.path.exists(PATH1))
        self.assertEqual(master.state.tick, 3)
        n_agents = master.state.numAgents()
        
    def profile_run_safe(self):
        assert SAFETY, "should turn on safety to run this"
        self._profile_run(type_check=True)
        
    def profile_run_fast(self):
        assert not SAFETY, "should turn off safety to run this"
        self._profile_run(type_check=False)
        
    def _profile_run(self, type_check):
        enforce.config({'enabled': type_check})
        import cProfile
        filename = "/tmp/profile_run.cprof"

        print("Do actual profile run: begin")
        prof = cProfile.runctx(
            "ret_code = self._testRunLonger(10000)", globals(), locals(), filename)
        print("Do actual profile run: done. Profile data is in %s" % filename)
        
    def profile_analyze(self):
        filename = "/tmp/profile_run.cprof"
        
        print("Analyze profile data:")
        import pstats
        p = pstats.Stats(filename)
        p.strip_dirs() #remove extraneous path from all module names

        print("")
        print("=======================================================")
        print("Sort by cumulative time in a function (and children)")
        p.sort_stats('cumtime').print_stats(30)
        print("")

        print("")
        print("=======================================================")
        print("Sort by time in a function (no recursion)")
        p.sort_stats('time').print_stats(30)

        print("Analyze profile data: done")

        print("Done overall")
        
    def tearDown(self):
        if os.path.exists(PATH1): shutil.rmtree(PATH1)
