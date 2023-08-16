import brownie
from enforce_typing import enforce_types

from agents.VestingFunderAgent import VestingFunderAgent
from util import globaltokens
from util.base18 import toBase18
from util.tx import txdict

# don't use account0, it's GOD_ACCOUNT. don't use account9, it's conftest pool
account1 = brownie.network.accounts[1]
chain = brownie.network.chain


@enforce_types
def test1():
    OCEAN = globaltokens.OCEANtoken()
    assert OCEAN.balanceOf(account1) == 0

    # initialize beneficiary agent
    class MockBeneficiaryAgent:
        def __init__(self, account):
            self.account = account  # brownie account
            self.address = account.address

    beneficiary_agent = MockBeneficiaryAgent(account1)
    assert OCEAN.balanceOf(beneficiary_agent.address) == 0

    # initialize state
    class MockState:
        def __init__(self, beneficiary_agent):
            self.agents = {"beneficiary1": beneficiary_agent, "vw1": None}

        def getAgent(self, name):
            return self.agents[name]

        def addAgent(self, agent):
            self.agents[agent.name] = agent

        def takeStep(self):
            for agent in self.agents.values():
                agent.takeStep(self)

    state = MockState(beneficiary_agent)

    # initialize funder agent
    funder_agent = VestingFunderAgent(
        name="funder1",
        USD=0.0,
        OCEAN=100.0,
        vesting_wallet_agent_name="vw1",
        beneficiary_agent_name="beneficiary1",
        start_timestamp=chain[-1].timestamp,
        duration_seconds=30,
    )
    assert not funder_agent._did_funding
    assert funder_agent.OCEAN() == 100.0
    assert state.getAgent("vw1") is None

    # create vw agent and send OCEAN to it
    funder_agent.takeStep(state)
    assert state.getAgent("vw1") is not None
    vw = state.getAgent("vw1").vesting_wallet
    assert vw.beneficiary() == beneficiary_agent.address
    assert 0 <= vw.vestedAmount(OCEAN.address, chain[-1].timestamp) < toBase18(100.0)
    assert vw.released(OCEAN.address) == 0
    assert funder_agent._did_funding
    assert funder_agent.OCEAN() == 0.0
    assert OCEAN.balanceOf(beneficiary_agent.address) == 0

    # OCEAN vests
    chain.mine(blocks=1, timedelta=60)
    assert vw.vestedAmount(OCEAN.address, chain[-1].timestamp) == toBase18(100.0)
    assert vw.released(OCEAN.address) == 0
    assert OCEAN.balanceOf(beneficiary_agent.address) == 0

    # release OCEAN
    vw.release(OCEAN.address, txdict(account1))
    assert vw.released(OCEAN.address) == toBase18(100.0)
    assert OCEAN.balanceOf(beneficiary_agent.address) == toBase18(100.0)
