from enforce_typing import enforce_types
import pytest

from agents.PoolAgent import PoolAgent
from agents.PublisherAgent import PublisherAgent, PERCENT_UNSTAKE
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

    def getAgent(self, name):
        return self.agents[name]

@enforce_types
@pytest.mark.parametrize("mal",  [False, True])
def test_doCreatePool(mal):
    agent = PublisherAgent("a", USD=0.0, OCEAN=0.0, is_malicious=mal)
    c = agent._doCreatePool()
    assert c in [False, True]

@enforce_types
def test_constructor_args():
    agent = PublisherAgent(
        "agent1",
        USD=0.0,
        OCEAN=0.0,
        # parameters like regular publisher
        DT_init=1.1,
        DT_stake=2.2,
        pool_weight_DT=3.3,
        pool_weight_OCEAN=4.4,
        s_between_create=50,
        s_between_unstake=60,
        s_between_sellDT=70,
        
        is_malicious=True,
        s_wait_to_rug=80,
        s_rug_time=90,
    )

    assert agent._DT_init == 1.1
    assert agent._DT_stake == 2.2
    assert agent._pool_weight_DT == 3.3
    assert agent._pool_weight_OCEAN == 4.4
    assert agent._s_between_create == 50
    assert agent._s_between_unstake == 60
    assert agent._s_between_sellDT == 70
    
    assert agent._is_malicious
    assert agent._s_wait_to_rug == 80
    assert agent._s_rug_time == 90

    assert agent.pools == []

@enforce_types
@pytest.mark.parametrize("mal", [False, True])
def test_createPoolAgent(mal):
    state = MockState()
    assert len(state.agents) == 0

    pub_agent = PublisherAgent("a", USD=0.0, OCEAN=1000.0, is_malicious=mal)
    state.addAgent(pub_agent)
    assert len(state.agents) == 1
    assert len(state.agents.filterToPool()) == 0

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents) == 2
    assert len(state.agents.filterToPool()) == 1
    pool_agent2 = state.agents[pool_agent.name]
    assert isinstance(pool_agent2, PoolAgent)

@enforce_types
@pytest.mark.parametrize("mal", [False, True])
def test_unstakeOCEANsomewhere(mal):
    state = MockState()
    pub_agent = PublisherAgent("pub1", USD=0.0, OCEAN=1000.0, is_malicious=mal)

    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert not pub_agent._doUnstakeOCEAN(state)

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 1
    assert not pub_agent._doUnstakeOCEAN(state)

    pub_agent._s_since_unstake += pub_agent._s_between_unstake  # force unstake
    pub_agent._s_since_create += pub_agent._s_wait_to_rug  # ""
    assert pub_agent._doUnstakeOCEAN(state)

    BPT_before = pub_agent.BPT(pool_agent.pool)
    pub_agent._unstakeOCEANsomewhere(state)
    BPT_after = pub_agent.BPT(pool_agent.pool)
    assert BPT_after == (1.0 - PERCENT_UNSTAKE) * BPT_before

@enforce_types
@pytest.mark.parametrize("mal", [False, True])
def test_sellDTsomewhere(mal):
    state = MockState()
    pub_agent = PublisherAgent("pub1", USD=0.0, OCEAN=1000.0, is_malicious=mal)

    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert not pub_agent._doSellDT(state)

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(pub_agent._DTsWithNonzeroBalance(state)) == 1
    assert not pub_agent._doSellDT(state)

    pub_agent._s_since_sellDT += pub_agent._s_between_sellDT  # force sell
    pub_agent._s_since_create += pub_agent._s_wait_to_rug  # ""
    assert pub_agent._doSellDT(state)

    DT_before = pub_agent.DT(pool_agent.datatoken)
    perc_sell = 0.01
    pub_agent._sellDTsomewhere(state, perc_sell=perc_sell)
    DT_after = pub_agent.DT(pool_agent.datatoken)
    assert DT_after == (1.0 - perc_sell) * DT_before
