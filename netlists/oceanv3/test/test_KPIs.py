from pytest import approx

from enforce_typing import enforce_types

from agents.PoolAgent import PoolAgent
from util import globaltokens
from util.base18 import fromBase18
from .. import KPIs


@enforce_types
class MockAgentDict(dict):  # subset of engine.AgentDict
    def __init__(self, *arg, **kw):  # pylint: disable=useless-super-delegation
        super().__init__(*arg, **kw)

    def filterToPool(self):
        return self.filterByClass(PoolAgent)

    def filterByClass(self, _class):
        return MockAgentDict(
            {agent.name: agent for agent in self.values() if isinstance(agent, _class)}
        )


@enforce_types
class MockSimState:
    def __init__(self):
        self.agents = MockAgentDict()

    def getAgent(self, name: str):
        return self.agents[name]


@enforce_types
class FooAgent:
    def __init__(self, name: str):
        self.name = name
        self._DT = 3.0  # magic number
        self._BPT = 5.0  # ""

    def DT(self, dt) -> float:  # pylint: disable=unused-argument
        return self._DT

    def BPT(self, pool) -> float:  # pylint: disable=unused-argument
        return self._BPT


@enforce_types
def test_get_OCEAN_in_DTs(alice_info):
    state = MockSimState()

    pool, DT = alice_info.pool, alice_info.DT
    pool_agent = PoolAgent("pool_agent", pool)
    state.agents["agent1"] = pool_agent

    foo_agent = FooAgent("foo_agent")

    OCEAN_address = globaltokens.OCEAN_address()
    price = fromBase18(pool.getSpotPrice(OCEAN_address, DT.address))

    amt_DT = foo_agent.DT("bar")
    assert amt_DT == 3.0

    value_held = KPIs.get_OCEAN_in_DTs(state, foo_agent)
    assert value_held == amt_DT * price


@enforce_types
def test_get_OCEAN_in_BPTs(alice_info):
    state = MockSimState()

    pool, DT = alice_info.pool, alice_info.DT
    pool_agent = PoolAgent("pool_agent", pool)
    state.agents["agent1"] = pool_agent

    foo_agent = FooAgent("foo_agent")

    OCEAN_address = globaltokens.OCEAN_address()
    price = fromBase18(pool.getSpotPrice(OCEAN_address, DT.address))
    pool_value_DT = price * fromBase18(pool.getBalance(DT.address))
    pool_value_OCEAN = fromBase18(pool.getBalance(OCEAN_address))
    pool_value = pool_value_DT + pool_value_OCEAN

    # case: foo_agent no BPTs
    value_held = KPIs.get_OCEAN_in_BPTs(state, foo_agent)
    assert value_held == approx(0.0 * pool_value)

    # case: foo_agent has all BPTs
    foo_agent._BPT = pool.totalSupply()  # make pool think agent has 100% of BPTs
    value_held = KPIs.get_OCEAN_in_BPTs(state, foo_agent)

    assert value_held == 1.0 * pool_value
