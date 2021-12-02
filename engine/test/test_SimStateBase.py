from enforce_typing import enforce_types

from engine import SimStateBase, SimStrategyBase, KPIsBase
from engine import AgentBase

# ==================================================================
# testing stubs

class SimStrategy(SimStrategyBase.SimStrategyBase):
    pass

class KPIs(KPIsBase.KPIsBase):
    def takeStep(self, state):
        pass

    @staticmethod
    def tick():
        pass

class SimpleAgent(AgentBase.AgentBaseEvm):
    def takeStep(self, state):
        pass

class SimState(SimStateBase.SimStateBase):
    def __init__(self):
        super().__init__()
        self.ss = SimStrategy()
        self.kpis = KPIs(time_step=3)

        self.addAgent(SimpleAgent("agent1", 0.0, 0.0))
        self.addAgent(SimpleAgent("agent2", 0.0, 0.0))

# ==================================================================
# actual tests

@enforce_types
def test1():
    state = SimState()
    assert state.tick == 0
    assert state.numAgents() == 2
    assert isinstance(state.kpis, KPIs)

    state.takeStep()

    assert id(state.getAgent("agent1")) == id(state.agents["agent1"])

    assert len(state.allAgents()) == 2
    assert state.numAgents() == 2

    agent3 = SimpleAgent("agent3", 0.0, 0.0)
    state.addAgent(agent3)
    assert state.numAgents() == 3
