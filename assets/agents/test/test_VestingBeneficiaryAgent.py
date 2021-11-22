from enforce_typing import enforce_types

from assets.agents.VestingBeneficiaryAgent import VestingBeneficiaryAgent
from web3engine.globaltokens import fundOCEANFromAbove
from web3tools.web3util import toBase18

@enforce_types
def test1():    
    class MockVestingWalletAgent:
        """Simple behavior: vests 100 OCEAN at once"""
        def __init__(self):
            #OCEAN state change unvested -> vested -> released
            self.OCEAN_unvested = 100.0
            self.OCEAN_vested = 0.0
            self.OCEAN_released = 0.0
            self.beneficiary_address = None
            
        def takeStep(self, state):
            if self.OCEAN_unvested > 0.0:
                self.OCEAN_vested += self.OCEAN_unvested
                self.OCEAN_unvested = 0.0

        def releaseOCEAN(self):
            assert self.beneficiary_address is not None, "need a beneficiary"
            if self.OCEAN_vested > 0.0:
                amt_release = self.OCEAN_vested
                fundOCEANFromAbove(
                    self.beneficiary_address, toBase18(amt_release))
                self.OCEAN_released += amt_release
                self.OCEAN_vested = 0.0
    vw_agent = MockVestingWalletAgent()

    beneficiary_agent = VestingBeneficiaryAgent(
        "foo", USD=10.0, OCEAN=20.0,
        vesting_wallet_agent=vw_agent)
    vw_agent.beneficiary_address = beneficiary_agent.address
    assert beneficiary_agent.USD() == 10.0
    assert beneficiary_agent.OCEAN() == 20.0

    class MockSimState:
        def __init__(self, agents):
            self.agents = agents
        def takeStep(self):
            for agent in self.agents:
                agent.takeStep(self)
        def OCEANprice(self) -> float:
            return 3.0
    state = MockSimState([vw_agent, beneficiary_agent])

    state.takeStep()
    assert vw_agent.OCEAN_unvested == 0.0
    assert vw_agent.OCEAN_vested == 0.0
    assert vw_agent.OCEAN_released == 100.0
    assert beneficiary_agent.USD() == 10.0
    assert beneficiary_agent.OCEAN() == (20.0 + 100.0)
    
    
                  
