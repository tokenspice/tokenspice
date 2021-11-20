import brownie
from enforce_typing import enforce_types
from pytest import approx

from assets.agents import VestingFunderAgent

class MockState:
    pass
    
@enforce_types
def test1():
    accounts = brownie.network.accounts
    
    class MockBeneficiaryAgent:
        def __init__(self, account):
            self.account = account
        @property
        def address(self) -> str:
            return self.acccount.address
    beneficiary_agent = MockBeneficiaryAgent(accounts[1])
    
    class MockState:
        def __init__(self, beneficiary_agent):
            self.beneficiary_agent = beneficiary_agent
            self.vw_agent = None
        def getAgent(self, name):
            if name == "beneficiary1":
                return self.beneficiary_agent
            else:
                raise NotImplementedError()
        def addAgent(self, agent):
            assert agent.name == "vw_agent"
            assert self.vw_agent is None
            self.vw_agent = agent
    state = MockState(beneficiary_agent)
    
    funder_agent = VestingFunderAgent.VestingFunderAgent(
        name = "funder1",
        USD = 0.0,
        OCEAN = 100.0,
        beneficiary_agent_name = "beneficiary1",
        start_timestamp = brownie.network.chain.time(),
        duration_seconds = 30)
    assert not funder_agent._did_funding
    assert funder_agent.OCEAN() == 100.0

    funder_agent.takeStep(state)
    assert funder_agent._did_funding
    assert funder_agent.OCEAN() == 0.0
    assert isinstance(state.vw_agent, VestingWalletAgent)
    assert state.vw_agent.name == "vw_agent"
    OCEAN_address = globaltokens.OCEAN_address()
    vw = state.vw_agent.vesting_wallet
    assert vw.released(OCEAN_address) == approx(Wei(100.0))
    
    #no further actions
    for i in range(10):
        funder_agent.takeStep(state)
