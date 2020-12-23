import os
import shutil

from engine.SimEngine import SimEngine
from engine.SimStrategy import SimStrategy
import engine.SimState as SimState
from util.constants import SAFETY

PATH1 = '/tmp/test_outpath1'

def setUp():        
    #possible cleanup from prev run
    if os.path.exists(PATH1): shutil.rmtree(PATH1)

def testRunLonger():
    _testRunLonger(15)

def _testRunLonger(max_ticks):
    ss = SimStrategy()
    ss.setMaxTicks(max_ticks)
    master = SimEngine(ss, PATH1)
    master.run()        

def testRunEngine():
    ss = SimStrategy()
    ss.setMaxTicks(3)
    master = SimEngine(ss, PATH1)
    master.run()
    assert os.path.exists(PATH1)
    assert master.state.tick == 3
    n_agents = master.state.numAgents()

def tearDown():
    if os.path.exists(PATH1): shutil.rmtree(PATH1)
