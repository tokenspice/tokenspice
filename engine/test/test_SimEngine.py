from enforce_typing import enforce_types
import os
import shutil

from engine import AgentBase
from engine import SimEngine, SimStateBase, SimStrategyBase, KPIsBase

PATH1 = '/tmp/test_outpath1'


#==================================================================
#testing stubs
class SimStrategy(SimStrategyBase.SimStrategyBase):
    pass

class KPIs(KPIsBase.KPIsBase):
    def takeStep(self, state):
        pass
    def tick(self):
        pass

class SimpleAgent(AgentBase.AgentBase):
    def takeStep(self, state):
        pass

class SimState(SimStateBase.SimStateBase):
    def __init__(self):
        super().__init__()
        self.ss = SimStrategy()
        self.kpis = KPIs(time_step=3)

#==================================================================
#actual tests

@enforce_types
def setUp():
    #possible cleanup from prev run
    if os.path.exists(PATH1): shutil.rmtree(PATH1)

@enforce_types
def testRunLonger():
    _testRunLonger(15)

@enforce_types
def _testRunLonger(max_ticks):
    state = SimState()
    state.ss.setMaxTicks(max_ticks)
    engine = SimEngine.SimEngine(state, PATH1)
    engine.run()

@enforce_types
def testRunEngine():
    state = SimState()
    state.ss.setMaxTicks(3)
    engine = SimEngine.SimEngine(state, PATH1)
    engine.run()
    assert os.path.exists(PATH1)
    assert engine.state.tick == 3
    n_agents = engine.state.numAgents()

@enforce_types
def tearDown():
    if os.path.exists(PATH1): shutil.rmtree(PATH1)
