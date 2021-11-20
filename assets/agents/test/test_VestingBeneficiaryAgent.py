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
        def __init__(self):
            self.OCEAN_locked = 100.0
            self.OCEAN_unlocked = 0.0
            
        def releaseOCEAN(self):
            self.OCEAN_unlocked += self.OCEAN_locked
            self.OCEAN_locked = 0.0
    vesting_wallet_agent = MockVestingWalletAgent()

    #init beneficiary agent
    a = VestingBeneficiaryAgent("foo", USD=10.0, OCEAN=20.0,
                                vesting_wallet_agent)
    assert a._spent_at_tick == 0.0

    #take a step. This agent will spend everything it can get its hands on
    # In this case, it's getting 10 USD (from init) + 20 OCEAN (from init)
    #   + 100 OCEAN (from vesting wallet agent)
    a.takeStep(state)
    assert a.USD() == 0.0
    assert a.OCEAN() == 0.0
    assert a._spent_at_tick == (10.0 + (20.0 + 100.0)*3.0) 

    #from here on, it behaves just like a GrantTakingAgent
    a.takeStep(state)
    assert a._spent_at_tick == 0.0

    a.receiveUSD(5.0)
    a.takeStep(state)
    assert a._spent_at_tick == 5.0

    a.takeStep(state)
    assert a._spent_at_tick == 0.0

                  
