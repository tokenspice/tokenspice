from enforce_typing import enforce_types

from agents import PoolAgent


@enforce_types
def test1(alice_info):
    alice_pool, alice_DT = alice_info.pool, alice_info.DT
    alice_pool_agent = PoolAgent.PoolAgent("pool_agent", alice_pool)
    assert alice_pool_agent.pool.address == alice_pool.address
    assert alice_pool_agent.datatoken_address == alice_DT.address

    class MockState:
        pass

    state = MockState()
    alice_pool_agent.takeStep(state)
