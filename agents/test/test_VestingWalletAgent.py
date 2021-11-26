import brownie
from brownie import Wei
from enforce_typing import enforce_types
import pytest
from pytest import approx

from agents import VestingWalletAgent
from util.constants import BROWNIE_PROJECT
from util import globaltokens

#don't use account0, it's GOD_ACCOUNT. don't use account9, it's conftest pool
accounts = brownie.network.accounts
account1, account2, account3 = accounts[1], accounts[2], accounts[3]
chain = brownie.network.chain

@enforce_types
def test1():
    token = globaltokens.OCEANtoken()
    
    start_timestamp = chain[-1].timestamp + 5
    duration_seconds = 30
    vw_orig = BROWNIE_PROJECT.VestingWallet057.deploy(
        account2.address, start_timestamp, duration_seconds,
        {'from' : account1})

    vw_agent = VestingWalletAgent.VestingWalletAgent("vw_agent", vw_orig)
    vw = vw_agent.vesting_wallet
    assert id(vw) == id(vw_orig)
    globaltokens.fundOCEANFromAbove(vw.address, Wei("5 ether"))
    
    class MockState:
        def takeStep(self):
            chain.mine(blocks=3, timedelta=10)
            
    state = MockState()
    state.takeStep() #pass enough time (10 s) for _some_ vesting
    assert 0 < vw.vestedAmount(token.address, chain[-1].timestamp) < Wei("5 ether")
    
    for i in range(6): #pass enough time for _all_ vesting
        state.takeStep() 
    assert vw.vestedAmount(token.address, chain[-1].timestamp) == Wei("5 ether")
    assert vw.released() == 0
    assert token.balanceOf(account2.address) == 0

    #release the OCEAN. Anyone can call it. Beneficiary receives it
    vw.release(token.address, {'from': account3})
    assert vw.released(token.address)/1e18 == approx(5.0) #now it's released!
    assert token.balanceOf(account2.address) == Wei("5 ether") #beneficiary is richer

    
