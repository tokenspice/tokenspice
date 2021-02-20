from enforce_typing import enforce_types

from agents import PoolAgent
from web3engine import bpool, datatoken, globaltokens

class MockState:
    pass
        
@enforce_types
def test_conftest(alice_info):
    #are alice_pool's datatokens the same as alice_DT?
    #Note: we use alice_info here in order to get addresses to line up;
    # if we had two separate args then we'd need to resort to caching
    alice_pool, alice_DT = alice_info.pool, alice_info.DT
    OCEAN_address = globaltokens.OCEAN_address()
    alice_pool_DT_address = [a for a in alice_pool.getFinalTokens()
                             if a != OCEAN_address][0]
    assert alice_pool_DT_address == alice_DT.address
    
@enforce_types
def test1(alice_info):
    alice_pool, alice_DT = alice_info.pool, alice_info.DT
    alice_pool_agent = PoolAgent.PoolAgent("pool_agent", alice_pool)
    assert alice_pool_agent.pool.address == alice_pool.address
    assert alice_pool_agent.datatoken_address == alice_DT.address
    
    state = MockState()
    alice_pool_agent.takeStep(state) 
