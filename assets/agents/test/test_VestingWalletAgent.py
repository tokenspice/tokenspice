import brownie
from enforce_typing import enforce_types
from pytest import approx

from assets.agents import VestingWalletAgent
from util.constants import BROWNIE_PROJECT

class MockState:
    pass
    
@enforce_types
def test1(project):
    #deploy contract
    beneficiary_address = brownie.network.accounts[1].address
    start_timestamp = brownie.network.chain.time() + 5 #magic number
    duration_seconds = 30 #magic number
    vw_contract = BROWNIE_PROJECT.VestingWallet.deploy(
        beneficiary_address, start_timestamp, duration_seconds,
        {'from' : brownie.network.accounts[0]})

    #create agent
    vw_agent = VestingWalletAgent.VestingWalletAgent("vw_agent", vw_contract)
    assert vw_agent.vesting_wallet.address == vw_contract.address
    
    state = MockState()
    vw_agent.takeStep(state)

    #fancier tests are in 'scheduler' netlist
