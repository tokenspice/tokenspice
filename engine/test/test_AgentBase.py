from enforce_typing import enforce_types
import pytest

from engine.AgentBase import *
from engine.test.conftest import _DT_INIT, _DT_STAKE 

@enforce_types
class MyTestAgent(AgentBase):
    def takeStep(self, state):
        pass

@enforce_types
def testInit():
    agent = MyTestAgent("agent1", USD=1.1, OCEAN=1.2)
    assert agent.name == "agent1"
    assert agent.USD() == 1.1
    assert agent.OCEAN() == 1.2
    assert "MyTestAgent" in str(agent)
    assert isinstance(agent.address, str)
    assert agent.address == agent._wallet._address

@enforce_types
def testReceiveAndSend():
    #agents are of arbitary classes
    agent = MyTestAgent("agent1", USD=0.0, OCEAN=3.30)
    agent2 = MyTestAgent("agent2", USD=0.0, OCEAN=3.30)

    #USD
    assert pytest.approx(agent.USD()) == 0.00
    agent.receiveUSD(13.25)
    assert pytest.approx(agent.USD()) == 13.25

    agent._transferUSD(None, 1.10)
    assert pytest.approx(agent.USD()) == 12.15

    assert pytest.approx(agent2.USD()) == 0.00
    agent._transferUSD(agent2, 1.00)
    assert pytest.approx(agent.USD()) == (12.15 - 1.00)
    assert pytest.approx(agent2.USD()) == (0.00 + 1.00)

    #OCEAN
    assert pytest.approx(agent.OCEAN()) == 3.30
    agent.receiveOCEAN(2.01)
    assert pytest.approx(agent.OCEAN()) == 5.31

    agent._transferOCEAN(None, 0.20)
    assert pytest.approx(agent.OCEAN()) == 5.11

    assert pytest.approx(agent2.OCEAN()) == 3.30
    agent._transferOCEAN(agent2, 0.10)
    assert pytest.approx(agent.OCEAN()) == (5.11 - 0.10)
    assert pytest.approx(agent2.OCEAN()) == (3.30 + 0.10)
    

#===================================================================
# datatoken and pool-related
@enforce_types
def test_DT(alice_agent: AgentBase, alice_DT: datatoken.Datatoken):    
    alice_DT_amt: float = alice_agent._wallet.DT(alice_DT)
    assert alice_DT_amt == (_DT_INIT - _DT_STAKE)

@enforce_types
def test_BPT(alice_agent: AgentBase, alice_pool: bpool.BPool):    
    assert alice_agent.BPT(alice_pool) == 100.0

@enforce_types
def test_stakeOCEAN(alice_agent: AgentBase, alice_pool):    
    OCEAN_before:float = alice_agent.OCEAN()
    BPT_before:float = alice_agent.BPT(alice_pool)
    
    alice_agent.stakeOCEAN(OCEAN_stake=20.0, pool=alice_pool)
    
    OCEAN_after:float = alice_agent.OCEAN()
    BPT_after:float = alice_agent.BPT(alice_pool)
    assert OCEAN_after == (OCEAN_before - 20.0)
    assert BPT_after > BPT_before

@enforce_types
def test_unstakeOCEAN(alice_agent, alice_pool):
    BPT_before:float = alice_agent.BPT(alice_pool)
    
    alice_agent.unstakeOCEAN(BPT_unstake=20.0, pool=alice_pool)
    
    BPT_after:float = alice_agent.BPT(alice_pool)
    assert BPT_after == (BPT_before - 20.0)
    

