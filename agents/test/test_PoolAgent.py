
from agents import PoolAgent
from web3engine import bpool, datatoken, globaltokens

class MockState:
    pass
        
def test_conftest(alice_pool:bpool.BPool, alice_DT:datatoken.Datatoken):
    #are alice_pool's datatokens the same as alice_DT?
    OCEAN_address = globaltokens.OCEAN_address()
    alice_pool_DT_address = [a for a in alice_pool.getFinalTokens()
                             if a != OCEAN_address][0]
    assert alice_pool_DT_address == alice_DT.address
    
def test1(alice_pool, alice_DT):    
    alice_pool_agent = PoolAgent.PoolAgent("pool_agent", alice_pool)
    assert alice_pool_agent.pool.address == alice_pool.address
    assert alice_pool_agent.datatoken_address == alice_DT.address
    
    state = MockState()
    alice_pool_agent.takeStep(state) 
