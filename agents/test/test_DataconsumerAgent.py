import pytest

from agents.AgentDict import AgentDict
from agents.PoolAgent import PoolAgent
from agents.DataconsumerAgent import DataconsumerAgent
from util.constants import S_PER_HOUR

class MockSS:
    def __init__(self):
        #seconds per tick
        self.time_step: int = S_PER_HOUR

class MockState:
    def __init__(self):
        self.agents = AgentDict({})
        self.ss = MockSS()
    def addAgent(self, agent):
        self.agents[agent.name] = agent
        
@pytest.mark.skip(reason="TODO FIXME")
def test_doBuy(alice_pool):
    state = MockState()
    
    agent = DataconsumerAgent("agent1",USD=0.0,OCEAN=1000.0)

    assert agent._s_since_buy == 0
    assert agent._s_between_buys > 0
    
    assert not agent._doBuy(state)

    agent._s_since_buy += agent._s_between_buys 
    assert not state.agents.filterToPool().values() 
    assert not agent._doBuy(state) #still no, since no pools
    
    state.agents["pool1"] = PoolAgent("pool1", alice_pool)
    assert state.agents.filterToPool().values() #have pools
    assert agent._candPoolAgents(state) #have useful pools
    assert agent._doBuy(state) 
    
@pytest.mark.skip(reason="TODO FIXME")
def test_buy():
    pass
