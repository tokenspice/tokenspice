# account0 --> GOD_ACCOUNT, deploys factories, controls OCEAN
# account9 --> alice_info, gets some OCEAN in a pool below
# account2, 3, .., 8 --> not set here, but could use in other tests

import brownie
from enforce_typing import enforce_types
import pytest

from contracts.oceanv3 import oceanv3util
from engine import AgentBase
from util import globaltokens
from util.base18 import toBase18, fromBase18
from util.constants import BROWNIE_PROJECT, GOD_ACCOUNT

accounts = brownie.network.accounts
account0, account9 = accounts[0], accounts[9]

_OCEAN_INIT = 1000.0
_OCEAN_STAKE = 200.0
_DT_INIT = 100.0
_DT_STAKE = 20.0

_POOL_WEIGHT_DT    = 3.0
_POOL_WEIGHT_OCEAN = 7.0

@pytest.fixture(scope="module", autouse=True)
def alice_info():
    return _make_info(account9)

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@enforce_types
def _make_info(account):
    assert account.address != GOD_ACCOUNT.address
    
    OCEAN = globaltokens.OCEANtoken()
    assert OCEAN.balanceOf(account) == 0
    
    globaltokens.fundOCEANFromAbove(account.address, toBase18(_OCEAN_INIT))
    assert OCEAN.balanceOf(account) == toBase18(_OCEAN_INIT)
    
    class Info:
        pass
    info = Info()

    info.account = account
    
    info.DT = _createDT(account)
    assert info.DT.balanceOf(account) == toBase18(_DT_INIT)
    
    info.pool = _createPool(info.DT, account)

    class SimpleAgent(AgentBase.AgentBaseEvm):
        def takeStep(self, state):
            pass
    info.agent = SimpleAgent("agent1",USD=0.0,OCEAN=0.0)
    info.agent._wallet._account = account
    info.agent._wallet.resetCachedInfo() #needed b/c we munged the wallet

    #postconditions
    w = info.agent._wallet
    OCEAN1 = w.OCEAN()
    assert w._cached_OCEAN_base is not None
    OCEAN2 = fromBase18(int(w._cached_OCEAN_base))
    OCEAN3 = fromBase18(OCEAN.balanceOf(account))
    assert OCEAN1 == OCEAN2 == OCEAN3, (OCEAN1, OCEAN2, OCEAN3) 
    
    return info

@enforce_types
def _createDT(account):
    DT = oceanv3util.newDatatoken(
        'foo', 'DT1', 'DT1', toBase18(_DT_INIT), account)
    DT.mint(account.address, toBase18(_DT_INIT), {'from':account})
    return DT

@enforce_types
def _createPool(DT, account):
    #Create OCEAN-DT pool
    OCEAN = globaltokens.OCEANtoken()
    pool = oceanv3util.newBPool(account)
    
    DT.approve(pool.address, toBase18(_DT_STAKE), {'from':account})
    OCEAN.approve(pool.address, toBase18(_OCEAN_STAKE),{'from':account})

    assert OCEAN.balanceOf(account) >= toBase18(_DT_STAKE)
    assert OCEAN.balanceOf(account) >= toBase18(_OCEAN_STAKE)
    pool.bind(DT.address, toBase18(_DT_STAKE),
              toBase18(_POOL_WEIGHT_DT), {'from':account})
    pool.bind(OCEAN.address, toBase18(_OCEAN_STAKE),
              toBase18(_POOL_WEIGHT_OCEAN), {'from':account})

    pool.finalize({'from':account})
    
    return pool
