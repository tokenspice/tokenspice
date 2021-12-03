from enforce_typing import enforce_types
import pytest

from engine.AgentBase import AgentBaseEvm, AgentBaseNoEvm
from agents.test.conftest import _DT_INIT, _DT_STAKE


@enforce_types
class MyTestAgentEvm(AgentBaseEvm):
    def takeStep(self, state):
        pass


@enforce_types
class MyTestAgentNoEvm(AgentBaseNoEvm):
    def takeStep(self, state):
        pass


@enforce_types
def _MyTestAgent(use_EVM):
    if use_EVM:
        return MyTestAgentEvm
    return MyTestAgentNoEvm


@enforce_types
def testInitEvm():
    agent = MyTestAgentEvm("agent1", USD=1.1, OCEAN=1.2)
    assert agent.name == "agent1"
    assert agent.USD() == 1.1
    assert agent.OCEAN() == 1.2
    assert "MyTestAgent" in str(agent)
    assert isinstance(agent.address, str)
    assert agent.address == agent._wallet.address
    assert id(agent.account) == id(agent._wallet.account)


@enforce_types
def testInitNoEvm():
    agent = MyTestAgentNoEvm("agent1", USD=1.1, OCEAN=1.2)
    assert agent.name == "agent1"
    assert agent.USD() == 1.1
    assert agent.OCEAN() == 1.2
    assert "MyTestAgent" in str(agent)


@enforce_types
@pytest.mark.parametrize("use_EVM", [True, False])
def testReceiveAndSend(use_EVM):
    # agents are of arbitary classes
    agent = _MyTestAgent(use_EVM)("agent1", USD=0.0, OCEAN=3.30)
    agent2 = _MyTestAgent(use_EVM)("agent2", USD=0.0, OCEAN=3.30)

    # USD
    assert pytest.approx(agent.USD()) == 0.00
    agent.receiveUSD(13.25)
    assert pytest.approx(agent.USD()) == 13.25

    agent._transferUSD(None, 1.10)
    assert pytest.approx(agent.USD()) == 12.15

    assert pytest.approx(agent2.USD()) == 0.00
    agent._transferUSD(agent2, 1.00)
    assert pytest.approx(agent.USD()) == (12.15 - 1.00)
    assert pytest.approx(agent2.USD()) == (0.00 + 1.00)

    # OCEAN
    assert pytest.approx(agent.OCEAN()) == 3.30
    agent.receiveOCEAN(2.01)
    assert pytest.approx(agent.OCEAN()) == 5.31

    agent._transferOCEAN(None, 0.20)
    assert pytest.approx(agent.OCEAN()) == 5.11

    assert pytest.approx(agent2.OCEAN()) == 3.30
    agent._transferOCEAN(agent2, 0.10)
    assert pytest.approx(agent.OCEAN()) == (5.11 - 0.10)
    assert pytest.approx(agent2.OCEAN()) == (3.30 + 0.10)


# ===================================================================
# datatoken and pool-related
@enforce_types
def test_DT(alice_info):
    agent, DT = alice_info.agent, alice_info.DT
    DT_amt = agent._wallet.DT(DT)
    assert DT_amt == (_DT_INIT - _DT_STAKE)


@enforce_types
def test_BPT(alice_info):
    agent, pool = alice_info.agent, alice_info.pool
    assert agent.BPT(pool) == 100.0


@enforce_types
def test_stakeOCEAN(alice_info):
    agent, pool = alice_info.agent, alice_info.pool
    OCEAN_before, BPT_before = agent.OCEAN(), agent.BPT(pool)
    agent.stakeOCEAN(OCEAN_stake=20.0, pool=pool)
    OCEAN_after, BPT_after = agent.OCEAN(), agent.BPT(pool)
    assert OCEAN_after == (OCEAN_before - 20.0)
    assert BPT_after > BPT_before


@enforce_types
def test_unstakeOCEAN(alice_info):
    agent, pool = alice_info.agent, alice_info.pool
    BPT_before = agent.BPT(pool)
    agent.unstakeOCEAN(BPT_unstake=20.0, pool=pool)
    BPT_after = agent.BPT(pool)
    assert BPT_after == (BPT_before - 20.0)
