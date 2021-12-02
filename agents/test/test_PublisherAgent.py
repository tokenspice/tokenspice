#This module tests both PublisherAgent *and* MaliciousPublisherAgent.py
#If their macro behavior diverges, then expand test_MaliciousPublisherAgent.py
from enforce_typing import enforce_types
import pytest

from agents.PoolAgent import PoolAgent
from agents.PublisherAgent import PublisherAgent
from agents.MaliciousPublisherAgent import MaliciousPublisherAgent, PERCENT_UNSTAKE
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
@pytest.mark.parametrize("_AgentClass",[PublisherAgent,MaliciousPublisherAgent])
def test_doCreatePool(_AgentClass):
    agent = _AgentClass("agent1", USD=0.0, OCEAN=0.0)
    c = agent._doCreatePool()
    assert c in [False, True]

@enforce_types
def test_constructor_args_PublisherAgent():
    agent = PublisherAgent(
        "agent1",
        USD=0.0,
        OCEAN=0.0,
        DT_init=1.1,
        DT_stake=2.2,
        pool_weight_DT=3.3,
        pool_weight_OCEAN=4.4,
        s_between_create=50,
        s_between_unstake=60,
        s_between_sellDT=70,
    )
    assert agent._DT_init == 1.1
    assert agent._DT_stake == 2.2
    assert agent._pool_weight_DT == 3.3
    assert agent._pool_weight_OCEAN == 4.4
    assert agent._s_between_create == 50
    assert agent._s_between_unstake == 60
    assert agent._s_between_sellDT == 70

@enforce_types
def test_constructor_args_MaliciousPublisherAgent():
    agent = MaliciousPublisherAgent(
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
        # parameters new to malicous agent
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

    assert agent._s_wait_to_rug == 80
    assert agent._s_rug_time == 90

    assert agent.pools == []

@enforce_types
@pytest.mark.parametrize("_AgentClass",[PublisherAgent,MaliciousPublisherAgent])
def test_createPoolAgent(_AgentClass):
    state = MockState()
    assert len(state.agents) == 0

    pub_agent = _AgentClass("pub1", USD=0.0, OCEAN=1000.0)
    state.addAgent(pub_agent)
    assert len(state.agents) == 1
    assert len(state.agents.filterToPool()) == 0

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents) == 2
    assert len(state.agents.filterToPool()) == 1
    pool_agent2 = state.agents[pool_agent.name]
    assert isinstance(pool_agent2, PoolAgent)

@enforce_types
@pytest.mark.parametrize("_AgentClass",[PublisherAgent,MaliciousPublisherAgent])
def test_unstakeOCEANsomewhere(_AgentClass):
    state = MockState()
    pub_agent = _AgentClass("pub1", USD=0.0, OCEAN=1000.0)

    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert pub_agent._doUnstakeOCEAN(state) == False

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 1
    assert pub_agent._doUnstakeOCEAN(state) == False

    pub_agent._s_since_unstake += pub_agent._s_between_unstake  # force unstake
    if _AgentClass == MaliciousPublisherAgent:
        pub_agent._s_since_create += pub_agent._s_wait_to_rug  # ""
    assert pub_agent._doUnstakeOCEAN(state) == True

    BPT_before = pub_agent.BPT(pool_agent.pool)
    pub_agent._unstakeOCEANsomewhere(state)
    BPT_after = pub_agent.BPT(pool_agent.pool)
    percent_unstake = 0.10 if _AgentClass == PublisherAgent else PERCENT_UNSTAKE
    assert BPT_after == (1.0 - percent_unstake) * BPT_before

@enforce_types
@pytest.mark.parametrize("_AgentClass",[PublisherAgent,MaliciousPublisherAgent])
def test_sellDTsomewhere(_AgentClass):
    state = MockState()
    pub_agent = _AgentClass("pub1", USD=0.0, OCEAN=1000.0)

    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert pub_agent._doSellDT(state) == False

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(pub_agent._DTsWithNonzeroBalance(state)) == 1
    assert pub_agent._doSellDT(state) == False

    pub_agent._s_since_sellDT += pub_agent._s_between_sellDT  # force sell
    if _AgentClass == MaliciousPublisherAgent:
        pub_agent._s_since_create += pub_agent._s_wait_to_rug  # ""
    assert pub_agent._doSellDT(state) == True

    DT_before = pub_agent.DT(pool_agent.datatoken)
    perc_sell = 0.01
    pub_agent._sellDTsomewhere(state, perc_sell=perc_sell)
    DT_after = pub_agent.DT(pool_agent.datatoken)
    assert DT_after == (1.0 - perc_sell) * DT_before
