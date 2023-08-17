from enforce_typing import enforce_types
import pytest

from agents.PoolAgent import PoolAgent
from agents.PublisherAgent import PublisherStrategy, PublisherAgent, PERCENT_UNSTAKE
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
def test_PublisherStrategy():
    pub_ss = PublisherStrategy(
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

    assert pub_ss.DT_init == 1.1
    assert pub_ss.DT_stake == 2.2
    assert pub_ss.pool_weight_DT == 3.3
    assert pub_ss.pool_weight_OCEAN == 4.4
    assert pub_ss.s_between_create == 50
    assert pub_ss.s_between_unstake == 60
    assert pub_ss.s_between_sellDT == 70

    assert pub_ss.is_malicious
    assert pub_ss.s_wait_to_rug == 80
    assert pub_ss.s_rug_time == 90


@enforce_types
@pytest.mark.parametrize("is_malicious", [False, True])
def test_doCreatePool(is_malicious):
    pub_ss = PublisherStrategy(is_malicious=is_malicious)
    agent = PublisherAgent(name="a", USD=0.0, OCEAN=1000.0, pub_ss=pub_ss)
    c = agent._doCreatePool()
    assert c in [False, True]


@enforce_types
def test_constructor():
    pub_ss = PublisherStrategy()
    agent = PublisherAgent("pub1", USD=1.0, OCEAN=2.0, pub_ss=pub_ss)
    assert agent.USD() == 1.0
    assert agent.OCEAN() == 2.0
    assert id(agent.pub_ss) == id(pub_ss)
    assert agent.pub_ss.s_between_create == pub_ss.s_between_create

    assert agent._s_since_create == 0
    assert agent._s_since_unstake == 0
    assert agent._s_since_sellDT == 0

    assert not agent.pools


@enforce_types
@pytest.mark.parametrize("is_malicious", [False, True])
def test_createPoolAgent(is_malicious):
    state = MockState()
    assert len(state.agents) == 0

    pub_ss = PublisherStrategy(is_malicious=is_malicious)
    pub_agent = PublisherAgent(name="a", USD=0.0, OCEAN=1000.0, pub_ss=pub_ss)

    state.addAgent(pub_agent)
    assert len(state.agents) == 1
    assert len(state.agents.filterToPool()) == 0

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents) == 2
    assert len(state.agents.filterToPool()) == 1
    pool_agent2 = state.agents[pool_agent.name]
    assert isinstance(pool_agent2, PoolAgent)


@enforce_types
@pytest.mark.parametrize("is_malicious", [False, True])
def test_unstakeOCEANsomewhere(is_malicious):
    state = MockState()

    pub_ss = PublisherStrategy(is_malicious=is_malicious)
    pub_agent = PublisherAgent(name="a", USD=0.0, OCEAN=1000.0, pub_ss=pub_ss)

    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert not pub_agent._doUnstakeOCEAN(state)

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 1
    assert not pub_agent._doUnstakeOCEAN(state)

    pub_agent._s_since_unstake += pub_agent.pub_ss.s_between_unstake  # force unstake
    pub_agent._s_since_create += pub_agent.pub_ss.s_wait_to_rug  # ""
    assert pub_agent._doUnstakeOCEAN(state)

    BPT_before = pub_agent.BPT(pool_agent.pool)
    pub_agent._unstakeOCEANsomewhere(state)
    BPT_after = pub_agent.BPT(pool_agent.pool)
    assert BPT_after == (1.0 - PERCENT_UNSTAKE) * BPT_before


@enforce_types
@pytest.mark.parametrize("is_malicious", [False, True])
def test_sellDTsomewhere(is_malicious):
    state = MockState()

    pub_ss = PublisherStrategy(is_malicious=is_malicious)
    pub_agent = PublisherAgent(name="a", USD=0.0, OCEAN=1000.0, pub_ss=pub_ss)

    state.addAgent(pub_agent)
    assert len(state.agents.filterByNonzeroStake(pub_agent)) == 0
    assert not pub_agent._doSellDT(state)

    pool_agent = pub_agent._createPoolAgent(state)
    assert len(pub_agent._DTsWithNonzeroBalance(state)) == 1
    assert not pub_agent._doSellDT(state)

    pub_agent._s_since_sellDT += pub_agent.pub_ss.s_between_sellDT  # force sell
    pub_agent._s_since_create += pub_agent.pub_ss.s_wait_to_rug  # ""
    assert pub_agent._doSellDT(state)

    DT_before = pub_agent.DT(pool_agent.datatoken)
    perc_sell = 0.01
    pub_agent._sellDTsomewhere(state, perc_sell=perc_sell)
    DT_after = pub_agent.DT(pool_agent.datatoken)
    assert DT_after == (1.0 - perc_sell) * DT_before
