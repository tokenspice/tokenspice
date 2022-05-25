import os
import shutil

from brownie.network import chain  # pylint: disable=no-name-in-module
from enforce_typing import enforce_types

from engine import AgentBase
from engine import SimEngine, SimStateBase, SimStrategyBase, KPIsBase

PATH1 = "/tmp/test_outpath1"

# ==================================================================
# testing stubs
class SimStrategy(SimStrategyBase.SimStrategyBase):
    pass


class KPIs(KPIsBase.KPIsBase):
    def takeStep(self, state):
        pass

    def tick(self):
        pass


class SimpleAgent(AgentBase.AgentBaseNoEvm):
    def takeStep(self, state):
        pass


class SimState(SimStateBase.SimStateBase):
    def __init__(self, time_step: int):
        super().__init__()
        self.ss = SimStrategy()
        self.ss.setTimeStep(time_step)
        self.ss.setLogInterval(time_step * 10)
        self.kpis = KPIs(time_step)


# ==================================================================
# actual tests


@enforce_types
def setUp():
    # possible cleanup from prev run
    if os.path.exists(PATH1):
        shutil.rmtree(PATH1)


@enforce_types
def testRunLonger():
    _testRunLonger(15)


@enforce_types
def _testRunLonger(max_ticks):
    state = SimState(10)
    state.ss.setMaxTicks(max_ticks)
    engine = SimEngine.SimEngine(state, PATH1)
    engine.run()


@enforce_types
def testRunEngine():
    init_time = chain[-1].timestamp

    state = SimState(time_step=10)
    state.ss.setMaxTicks(3)
    engine = SimEngine.SimEngine(state, PATH1)
    engine.run()
    assert os.path.exists(PATH1)
    assert engine.state.numAgents() >= 0
    assert engine.state.tick == 3

    elapsed_time = chain[-1].timestamp - init_time
    assert elapsed_time in [30, 31]  # 3 ticks * 10 s/tick


@enforce_types
def tearDown():
    if os.path.exists(PATH1):
        shutil.rmtree(PATH1)
