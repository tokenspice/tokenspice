import brownie
from enforce_typing import enforce_types
import pytest

from contracts.oceanv3 import oceanv3util
from engine import AgentBase
from util import globaltokens
from util.base18 import toBase18, fromBase18
from util.constants import BROWNIE_PROJECT

accounts = brownie.network.accounts
account0, account1 = accounts[0], accounts[1]
address0, address1 = account0.address, account1.address

_OCEAN_INIT = 1000.0
_OCEAN_STAKE = 200.0
_DT_INIT = 100.0
_DT_STAKE = 20.0

_POOL_WEIGHT_DT    = 3.0
_POOL_WEIGHT_OCEAN = 7.0

@pytest.fixture
def alice_info():
    #only use this when there are >1 args into a test function and
    # we need addresses to line up. Otherwise, use a more specific function.
    return _alice_info()

@pytest.fixture
def alice_agent():
    return _alice_info().agent

@pytest.fixture
def alice_DT():
    return _alice_info().DT

@pytest.fixture
def alice_pool():
    return _alice_info().pool

@enforce_types
def _alice_info():
    return _make_info(account1)

@enforce_types
def _make_info(account):
    OCEAN = globaltokens.OCEANtoken()
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
    
    info.agent._wallet.resetCachedInfo() #needed b/c we munged the wallet

    #postconditions
    w = info.agent._wallet
    OCEAN1 = w.OCEAN()
    assert w._cached_OCEAN_base is not None
    OCEAN2 = fromBase18(int(w._cached_OCEAN_base))
    #OCEAN3 = fromBase18(OCEAN.balanceOf(account))
    #assert OCEAN1 == OCEAN2 == OCEAN3, (OCEAN1, OCEAN2, OCEAN3) #FIXME
    
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
