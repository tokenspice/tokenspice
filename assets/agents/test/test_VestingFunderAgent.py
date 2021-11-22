import brownie
from brownie import Wei
from enforce_typing import enforce_types
from pytest import approx

from assets.agents.VestingFunderAgent import VestingFunderAgent
from assets.agents.VestingWalletAgent import VestingWalletAgent
from web3engine import globaltokens

accounts = brownie.network.accounts
chain = brownie.network.chain
    
@enforce_types
def test1():
    OCEAN_address = globaltokens.OCEAN_address()
    OCEAN_token = globaltokens.OCEANtoken()

    #initialize beneficiary agent
    class MockBeneficiaryAgent:
        def __init__(self, account):
            self.account = account #brownie account
            self.address = account.address
    beneficiary_agent = MockBeneficiaryAgent(accounts[1])

    #initialize state
    class MockState:
        def __init__(self, beneficiary_agent):
            self.agents = {"beneficiary1":beneficiary_agent, "vw1":None}
        def getAgent(self, name):
            return self.agents[name]
        def addAgent(self, agent):
            self.agents[agent.name] = agent
        def takeStep(self):
            for agent in self.agent.values():
                agent.takeStep(self)
    state = MockState(beneficiary_agent)

    #initialize funder agent
    funder_agent = VestingFunderAgent(
        name = "funder1", USD = 0.0, OCEAN = 100.0,
        vesting_wallet_agent_name = "vw1",
        beneficiary_agent_name = "beneficiary1",
        start_timestamp = chain.time(),
        duration_seconds = 30)
    assert not funder_agent._did_funding
    assert funder_agent.OCEAN() == 100.0
    assert state.getAgent("vw1") is None

    #create vw agent and send OCEAN to it
    funder_agent.takeStep(state) 
    assert state.getAgent("vw1") is not None
    vw = state.getAgent("vw1").vesting_wallet
    assert vw.beneficiary() == beneficiary_agent.address
    assert 0 <= vw.vestedAmount(OCEAN_address, chain.time()) < Wei('100 ether')
    assert vw.released(OCEAN_address) == 0
    assert funder_agent._did_funding
    assert funder_agent.OCEAN() == 0.0
    assert OCEAN_token.balanceOf(beneficiary_agent.address) == 0

    #OCEAN vests
    chain.mine(blocks=1, timedelta=60) 
    assert vw.vestedAmount(OCEAN_address, chain.time()) == Wei('100 ether')
    assert vw.released(OCEAN_address) == 0
    assert OCEAN_token.balanceOf(beneficiary_agent.address) == 0

    #release OCEAN
    vw.release(OCEAN_address, {'from':accounts[1]})
    assert vw.released(OCEAN_address) == Wei('100 ether')
    assert OCEAN_token.balanceOf(beneficiary_agent.address) == Wei('100 ether')
    
