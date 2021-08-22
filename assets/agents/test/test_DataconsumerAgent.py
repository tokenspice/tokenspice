import pytest

from assets.agents.PoolAgent import PoolAgent
from assets.agents.DataconsumerAgent import DataconsumerAgent
from assets.agents.PublisherAgent import PublisherAgent
from engine.AgentDict import AgentDict
from util.constants import S_PER_HOUR

class MockSS:
    def __init__(self):
        #seconds per tick
        self.time_step: int = S_PER_HOUR
        self.pool_weight_DT: float = 1.0
        self.pool_weight_OCEAN: float = 1.0

class MockState:
    def __init__(self):
        self.agents = AgentDict({})
        self.ss = MockSS()
    def addAgent(self, agent):
        self.agents[agent.name] = agent

# @pytest.mark.skip(reason="TODO FIXME")
def test_doBuyDT(alice_pool):
    state = MockState()

    agent = DataconsumerAgent("agent1",USD=0.0,OCEAN=1000.0)

    assert agent._s_since_buy == 0
    assert agent._s_between_buys > 0

    assert not agent._doBuyDT(state)

    agent._s_since_buy += agent._s_between_buys
    assert not state.agents.filterToPool().values()
    assert not agent._doBuyDT(state) #still no, since no pools

    state.agents["pool1"] = PoolAgent("pool1", alice_pool)
    assert state.agents.filterToPool().values() #have pools
    assert agent._candPoolAgents(state) #have useful pools
    assert agent._doBuyDT(state)

def test_buyDT(alice_pool, alice_agent):
    state = MockState()
    state.addAgent(alice_agent)
    agent = DataconsumerAgent("con1", USD=0.0, OCEAN=1000.0) 
    state.addAgent(agent)

    agent._s_since_buy += agent._s_between_buys

    state.agents["pool1"] = PoolAgent("pool1", alice_pool)

    assert state.agents.filterToPool().values() #have pools
    assert agent._candPoolAgents(state) #have useful pools
    assert agent._doBuyDT(state)

    agent._buyDT(state)
    dt = state.agents["pool1"].datatoken
    assert agent.DT(dt) == 1.0
