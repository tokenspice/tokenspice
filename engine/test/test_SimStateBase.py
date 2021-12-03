from enforce_typing import enforce_types

from engine import SimStateBase, SimStrategyBase, KPIsBase
from engine import AgentBase

# ==================================================================
# testing stubs

SimStrategy = SimStrategyBase.SimStrategyBase


@enforce_types
class MockKPIs(KPIsBase.KPIsBase):
    def takeStep(self, state):
        pass

    def tick(self):
        pass


@enforce_types
class SimpleAgent(AgentBase.AgentBaseEvm):
    def takeStep(self, state):
        pass


@enforce_types
class MockSimState(SimStateBase.SimStateBase):
    def __init__(self):
        super().__init__()
        self.ss = SimStrategy()
        self.kpis = MockKPIs(time_step=3)

        self.addAgent(SimpleAgent("agent1", 0.0, 0.0))
        self.addAgent(SimpleAgent("agent2", 0.0, 0.0))


# ==================================================================
# actual tests


@enforce_types
def test1():
    state = MockSimState()
    assert state.tick == 0
    assert state.numAgents() == 2
    assert isinstance(state.kpis, MockKPIs)

    state.takeStep()

    assert id(state.getAgent("agent1")) == id(state.agents["agent1"])

    assert len(state.allAgents()) == 2
    assert state.numAgents() == 2

    agent3 = SimpleAgent("agent3", 0.0, 0.0)
    state.addAgent(agent3)
    assert state.numAgents() == 3
