from enforce_typing import enforce_types

from assets.agents.VestingBeneficiaryAgent import VestingBeneficiaryAgent

@enforce_types
def test1():
    #init state
    class MockSimState:
        def __init__(self):
            pass

        def OCEANprice(self) -> float:
            return 3.0
    state = MockSimState()

    #init vesting wallet agent
    class MockVestingWalletAgent:
        """Simple vesting wallet: it releases everything at once"""
        def __init__(self):
            self.OCEAN_locked = 100.0
            self.OCEAN_unlocked = 0.0
            
        def releaseOCEAN(self):
            self.OCEAN_unlocked += self.OCEAN_locked
            self.OCEAN_locked = 0.0
    vesting_wallet_agent = MockVestingWalletAgent()

    #init beneficiary agent
    a = VestingBeneficiaryAgent("foo", USD=10.0, OCEAN=20.0,
                                vesting_wallet_agent=vesting_wallet_agent)
    assert id(a._vesting_wallet_agent) == id(vesting_wallet_agent)

    #take a step
    a.takeStep(state)
    assert a.USD() == 10.0
    assert a.OCEAN() == (20.0 + 100.0)
    
    #from here on, nothing new happens
    a.takeStep(state)
    assert a.USD() == 10.0
    assert a.OCEAN() == (20.0 + 100.0)
                  
