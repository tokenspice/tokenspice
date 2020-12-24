from enforce_typing import enforce_types # type: ignore[import]
import pytest

from agents.PoolAgent import PoolAgent
from agents.PublisherAgent import PublisherAgent
from agents.AgentDict import AgentDict

class MockState:
    def __init__(self):
        self.agents = AgentDict({})
    def addAgent(self, agent):
        self.agents[agent.name] = agent

@enforce_types
def test_doCreatePool():
    agent = PublisherAgent("agent1", USD=0.0, OCEAN=0.0)
    c = agent._doCreatePool()
    assert c in [False, True]
    
@enforce_types
def test_createPoolAgent():
    state = MockState()
    assert len(state.agents) == 0
    
    pub_agent = PublisherAgent("pub1", USD=0.0, OCEAN=1000.0) 
    state.addAgent(pub_agent)
    assert len(state.agents) == 1
    assert len(state.agents.filterToPool()) == 0
    
    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents) == 2
    assert len(state.agents.filterToPool()) == 1
    pool_agent2 = state.agents[pool_agent.name]
    assert isinstance(pool_agent2, PoolAgent)
    
@enforce_types
def test_unstakeOCEANsomewhere():
    state = MockState()
    pub_agent = PublisherAgent("pub1", USD=0.0, OCEAN=1000.0)
    
    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert pub_agent._doUnstakeOCEAN(state) == False
    
    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 1
    assert pub_agent._doUnstakeOCEAN(state) == False

    pub_agent._s_since_unstake += pub_agent._s_between_unstake #force unstake
    assert pub_agent._doUnstakeOCEAN(state) == True

    BPT_before = pub_agent.BPT(pool_agent.pool)
    pub_agent._unstakeOCEANsomewhere(state)
    BPT_after = pub_agent.BPT(pool_agent.pool)
    assert BPT_after == (1.0 - 0.10) * BPT_before 
    
    
