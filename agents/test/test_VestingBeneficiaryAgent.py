from enforce_typing import enforce_types

from agents.VestingBeneficiaryAgent import VestingBeneficiaryAgent
from util.base18 import toBase18
from util.globaltokens import fundOCEANFromAbove


@enforce_types
def test1():
    beneficiary_agent = VestingBeneficiaryAgent(
        "beneficiary1", USD=10.0, OCEAN=20.0, vesting_wallet_agent_name="vw1"
    )
    assert beneficiary_agent.USD() == 10.0
    assert beneficiary_agent.OCEAN() == 20.0

    class MockVestingWallet:
        def __init__(self, beneficiary_address: str):
            self._released = False
            self._beneficiary_address = beneficiary_address

        def release(self, token_address, from_dict):  # pylint: disable=unused-argument
            fundOCEANFromAbove(self._beneficiary_address, toBase18(100.0))
            self._released = True

    vw = MockVestingWallet(beneficiary_agent.address)

    class MockVestingWalletAgent:
        def __init__(self, vw):
            self.vesting_wallet = vw

    vw_agent = MockVestingWalletAgent(vw)

    class MockSimState:
        def __init__(self, vw_agent):
            self.vw_agent = vw_agent

        def getAgent(self, name):  # pylint: disable=unused-argument
            return self.vw_agent

    state = MockSimState(vw_agent)

    beneficiary_agent.takeStep(state)
    assert beneficiary_agent.USD() == 10.0
    assert beneficiary_agent.OCEAN() == (20.0 + 100.0)
