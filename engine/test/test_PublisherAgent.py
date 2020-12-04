from engine.PoolAgent import PoolAgent
from engine.PublisherAgent import PublisherAgent

def test_doCreatePool():
    agent = PublisherAgent("agent1", USD=0.0, OCEAN=0.0)
    vals = set()
    for i in range(10000):
        vals.add(agent._doCreatePool())
    assert vals == {True, False}
    
def test_createPoolAgent():
    class MockState:
        def __init__(self):
            self.agents = {}
        def addAgent(self, agent):
            self.agents[agent.name] = agent
        def poolAgents(self):
            return {agent for agent in self.agents
                    if isinstance(agent, PoolAgent)}
    state = MockState()
    
    pub_agent = PublisherAgent("pub1", USD=0.0, OCEAN=10.0)
    state.addAgent(pub_agent)
    
    pool_agent_name = pub_agent._createPoolAgent(state)
    
    assert len(state.agents) == 2
    pool_agent = state.agents[pool_agent_name]
    assert isinstance(pool_agent, PoolAgent)
    

def test_sellStake():
    pass
