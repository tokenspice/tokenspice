import enforce
import pytest

from agents.AgentDict import AgentDict
from agents.StakerspeculatorAgent import StakerspeculatorAgent

class MockState:
    def __init__(self):
        self.agents = AgentDict({})
    def addAgent(self, agent):
        self.agents[agent.name] = agent
        
@pytest.mark.skip(reason="TODO FIXME")
@enforce.runtime_validation
def test_doSpeculateAction():
    state = MockState()
    
    agent = StakerspeculatorAgent("agent1",USD=0.0,OCEAN=0.0)

    assert agent._s_since_speculate == 0
    assert agent._s_between_speculates > 0
    
    assert not agent._doSpeculateAction(state)

    agent._s_since_speculate += agent._s_between_speculates 
    assert not agent._doSpeculateAction(state) #nope, still no pools!

@pytest.mark.skip(reason="TODO FIXME")
@enforce.runtime_validation
def test_take_step():
    state = MockState()
    
    agent = StakerspeculatorAgent("agent1",USD=0.0,OCEAN=1000.0)

    num_speculates = num_loops = 0
    while num_speculates < 5 and num_loops < 10000:
        agent.takeStep(state)
        if num_loops > 0 and self._s_since_speculate == 0:
            num_speculates += 1
        num_loops += 1

@pytest.mark.skip(reason="TODO FIXME")
@enforce.runtime_validation
def test_speculateAction():
    state = MockState()
    
    agent = StakerspeculatorAgent("agent1",USD=0.0,OCEAN=1000.0)

    agent._speculateAction(state)


    
