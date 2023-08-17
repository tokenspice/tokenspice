from enforce_typing import enforce_types
from pytest import approx

from agents.PoolAgent import PoolAgent
from agents.DataconsumerAgent import DataconsumerAgent
from engine import AgentBase
from engine.AgentDict import AgentDict
from util import constants


class MockSS:
    def __init__(self):
        # seconds per tick
        self.time_step: int = constants.S_PER_HOUR  # type:ignore
        self.pool_weight_DT: float = 1.0  # type:ignore
        self.pool_weight_OCEAN: float = 1.0  # type:ignore


class MockState:
    def __init__(self):
        self.agents = AgentDict({})
        self.ss = MockSS()

    def addAgent(self, agent):
        self.agents[agent.name] = agent


class SimpleAgent(AgentBase.AgentBaseEvm):
    def takeStep(self, state):
        pass


@enforce_types
def test_constructor1():
    agent = DataconsumerAgent("agent1", 0.1, 0.2)
    assert agent.USD() == 0.1
    assert agent.OCEAN() == 0.2
    assert agent._s_between_buys > 0
    assert agent._profit_margin_on_consume > 0.0


@enforce_types
def test_constructor2():
    agent = DataconsumerAgent("agent1", 0.1, 0.2, 3, 0.4)
    assert agent._s_between_buys == 3
    assert agent._profit_margin_on_consume == 0.4


@enforce_types
def test_doBuyAndConsumeDT_happy_path(alice_info):
    alice_pool = alice_info.pool
    state = MockState()

    agent = DataconsumerAgent("agent1", USD=0.0, OCEAN=1000.0)

    assert agent._s_since_buy == 0
    assert agent._s_between_buys > 0

    assert not agent._doBuyAndConsumeDT(state)

    agent._s_since_buy += agent._s_between_buys
    assert not state.agents.filterToPool().values()
    assert not agent._doBuyAndConsumeDT(state)  # still no, since no pools

    state.agents["pool1"] = PoolAgent("pool1", alice_pool)
    assert state.agents.filterToPool().values()  # have pools
    assert agent._candPoolAgents(state)  # have useful pools
    assert agent._doBuyAndConsumeDT(state)


@enforce_types
def test_doBuyAndConsumeDT_have_rugged_pools(alice_info):
    alice_pool = alice_info.pool
    state = MockState()
    agent = DataconsumerAgent("agent1", USD=0.0, OCEAN=1000.0)

    agent._s_since_buy += agent._s_between_buys

    state.agents["pool1"] = PoolAgent("pool1", alice_pool)
    assert agent._candPoolAgents(state)  # have useful pools

    state.rugged_pools = ["pool1"]  # pylint: disable=attribute-defined-outside-init
    assert not agent._candPoolAgents(state)  # do _not_ have useful pools


@enforce_types
def test_buyAndConsumeDT(alice_info):
    state = MockState()

    publisher_agent = SimpleAgent("agent1", USD=0.0, OCEAN=0.0)
    publisher_agent._wallet = alice_info.agent._wallet
    state.addAgent(publisher_agent)

    OCEAN_before = 1000.0
    consumer_agent = DataconsumerAgent("consumer1", USD=0.0, OCEAN=OCEAN_before)
    consumer_agent._s_since_buy += consumer_agent._s_between_buys
    state.addAgent(consumer_agent)

    pool_agent = PoolAgent("pool1", alice_info.pool)
    state.addAgent(pool_agent)

    assert state.agents.filterToPool().values()  # have pools
    assert consumer_agent._candPoolAgents(state)  # have useful pools
    assert consumer_agent._doBuyAndConsumeDT(state)

    # buyAndConsumeDT
    dt = state.agents["pool1"].datatoken

    assert consumer_agent.OCEAN() == OCEAN_before
    assert consumer_agent.DT(dt) == 0.0

    OCEAN_spend = consumer_agent._buyAndConsumeDT(state)

    OCEAN_after = consumer_agent.OCEAN()
    OCEAN_gained = OCEAN_spend * (1.0 + consumer_agent._profit_margin_on_consume)
    assert OCEAN_after == approx(OCEAN_before - OCEAN_spend + OCEAN_gained)

    assert consumer_agent.DT(dt) == 0.0  # bought 1.0, then consumed it

    # consumeDT
    assert state.agents.agentByAddress(pool_agent.controller_address)
