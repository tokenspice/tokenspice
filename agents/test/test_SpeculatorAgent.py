"""Test SpeculatorAgent *and* StakerspeculatorAgent.py"""
from enforce_typing import enforce_types
import pytest

from agents.PoolAgent import PoolAgent
from agents.SpeculatorAgent import SpeculatorAgent, StakerspeculatorAgent
from engine.AgentDict import AgentDict
from util.constants import S_PER_HOUR


class MockSS:
    def __init__(self):
        # seconds per tick
        self.time_step: int = S_PER_HOUR  # type:ignore


class MockState:
    def __init__(self):
        self.ss = MockSS()
        self.agents = AgentDict({})

    def addAgent(self, agent):
        self.agents[agent.name] = agent


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_constructor1(_AgentClass):
    agent = _AgentClass("agent1", 0.1, 0.2)
    assert agent.USD() == 0.1
    assert agent.OCEAN() == 0.2
    assert agent._s_between_speculates > 0


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_constructor2(_AgentClass):
    agent = _AgentClass("agent1", 0.1, 0.2, 3)
    assert agent._s_between_speculates == 3


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_doSpeculateAction(alice_info, _AgentClass):
    alice_pool = alice_info.pool
    state = MockState()

    agent = _AgentClass("agent1", USD=0.0, OCEAN=0.0, s_between_speculates=1000)

    assert agent._s_since_speculate == 0
    assert agent._s_between_speculates == 1000

    assert not agent._doSpeculateAction(state)

    agent._s_since_speculate += agent._s_between_speculates
    assert not state.agents.filterToPool().values()
    assert not agent._doSpeculateAction(state)  # still no, since no pools

    state.agents["pool1"] = PoolAgent("pool1", alice_pool)
    assert state.agents.filterToPool().values()

    assert agent._doSpeculateAction(state)


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_speculateAction_nopools(_AgentClass):
    state = MockState()
    agent = _AgentClass("agent1", USD=0.0, OCEAN=1000.0)
    assert not agent._poolsForSpeculate(state)
    assert not agent._doSpeculateAction(state)
    with pytest.raises(AssertionError):
        agent._speculateAction(state)  # error because no pools


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_speculateAction_with_rugged_pools(alice_info, _AgentClass):
    alice_pool = alice_info.pool
    state = MockState()
    state.agents["pool1"] = PoolAgent("pool1", alice_pool)
    state.rugged_pools = ["pool1"]  # pylint: disable=attribute-defined-outside-init

    agent = _AgentClass("agent1", USD=0.0, OCEAN=500.0)

    assert not agent._poolsForSpeculate(state)
    assert not agent._doSpeculateAction(state)
    with pytest.raises(AssertionError):
        agent._speculateAction(state)  # error because no good pools


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_speculateAction_with_good_pools(alice_info, _AgentClass):
    alice_pool = alice_info.pool
    state = MockState()
    state.agents["pool1"] = PoolAgent("pool1", alice_pool)

    agent = _AgentClass("agent1", USD=0.0, OCEAN=500.0)

    assert agent._poolsForSpeculate(state)

    assert not agent._doSpeculateAction(state)  # not enough time passsed
    agent._s_since_speculate += agent._s_between_speculates  # make time pass
    assert agent._doSpeculateAction(state)  # now, enough time passed

    dt = state.agents["pool1"].datatoken
    assert agent.OCEAN() == 500.0
    if _AgentClass == SpeculatorAgent:
        assert agent.DT(dt) == 0.0
    else:
        assert agent.BPT(alice_pool) == 0.0

    agent._speculateAction(state)
    assert agent.OCEAN() < 500.0
    if _AgentClass == SpeculatorAgent:
        assert agent.DT(dt) > 0.0
    else:
        assert agent.BPT(alice_pool) > 0.0


@enforce_types
@pytest.mark.parametrize("_AgentClass", [SpeculatorAgent, StakerspeculatorAgent])
def test_take_step(alice_info, _AgentClass):
    alice_pool = alice_info.pool
    state = MockState()
    state.agents["pool1"] = PoolAgent("pool1", alice_pool)

    agent = _AgentClass("agent1", USD=0.0, OCEAN=500.0)

    num_speculates = num_loops = 0
    while num_speculates < 5 and num_loops < 10000:
        agent.takeStep(state)
        if num_loops > 0 and agent._s_since_speculate == 0:
            num_speculates += 1
        num_loops += 1

    assert num_speculates > 0, "should have had at least one speculate"
