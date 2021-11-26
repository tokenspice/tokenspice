from enforce_typing import enforce_types
import pytest

from agents.PoolAgent import PoolAgent
from agents.PublisherAgent import PublisherAgent
from engine import AgentDict

class MockSS:
    def __init__(self):
        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0

class MockState:
    def __init__(self):
        self.agents = AgentDict.AgentDict({})
        self.ss = MockSS()
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

@enforce_types
def test_sellDTsomewhere():
    state = MockState()
    pub_agent = PublisherAgent("pub1", USD=0.0, OCEAN=1000.0)
    
    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert pub_agent._doSellDT(state) == False
    
    pool_agent = pub_agent._createPoolAgent(state)
    assert len(pub_agent._DTsWithNonzeroBalance(state)) == 1
    assert pub_agent._doSellDT(state) == False

    pub_agent._s_since_sellDT += pub_agent._s_between_sellDT #force sell
    assert pub_agent._doSellDT(state) == True

    DT_before = pub_agent.DT(pool_agent.datatoken)
    perc_sell = 0.01
    pub_agent._sellDTsomewhere(state, perc_sell=perc_sell)
    DT_after = pub_agent.DT(pool_agent.datatoken)
    assert DT_after == (1.0 - perc_sell) * DT_before
