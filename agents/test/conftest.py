# account0 --> GOD_ACCOUNT, deploys factories, controls OCEAN
# account9 --> alice_info, gets some OCEAN in a pool below
# account2, 3, .., 8 --> not set here, but could use in other tests

import brownie
from enforce_typing import enforce_types
import pytest

from engine import AgentBase
from sol057.contracts.oceanv3 import oceanv3util
from util import globaltokens
from util.base18 import toBase18, fromBase18
from util.constants import GOD_ACCOUNT
from util.tx import txdict

accounts = brownie.network.accounts
account0, account1 = accounts[0], accounts[1]

_OCEAN_INIT = 1000.0
_OCEAN_STAKE = 200.0
_DT_INIT = 100.0
_DT_STAKE = 20.0

_POOL_WEIGHT_DT = 3.0
_POOL_WEIGHT_OCEAN = 7.0


@pytest.fixture
def alice_info():
    return _make_info(account0)


@enforce_types
def _make_info(account):
    assert account.address != GOD_ACCOUNT.address

    OCEAN = globaltokens.OCEANtoken()

    # reset OCEAN balances on-chain, to avoid relying on brownie chain reverts
    # -assumes that DT and BPT in each test are new tokens each time, and
    #  therefore don't need re-setting
    for a in accounts:
        if a.address != GOD_ACCOUNT.address:
            OCEAN.transfer(GOD_ACCOUNT, OCEAN.balanceOf(a), txdict(a))

    class Info:
        def __init__(self):
            self.account = None
            self.agent = None
            self.DT = None
            self.pool = None

    info = Info()
    info.account = account

    class SimpleAgent(AgentBase.AgentBaseEvm):
        def takeStep(self, state):
            pass

    info.agent = SimpleAgent("agent1", USD=0.0, OCEAN=0.0)
    info.agent._wallet._account = account  # force agent to use this account
    info.agent._wallet.resetCachedInfo()  # because account changed wallet

    info.DT = _createDT(account)
    info.agent._wallet.resetCachedInfo()  # because DT was deposited to account
    assert info.DT.balanceOf(account) == toBase18(_DT_INIT)

    globaltokens.fundOCEANFromAbove(account.address, toBase18(_OCEAN_INIT))
    info.agent._wallet.resetCachedInfo()  # because OCEAN was deposited to account

    info.pool = _createPool(info.DT, account)  # create pool, stake DT & OCEAN
    info.agent._wallet.resetCachedInfo()  # because OCEAN & DT was staked

    # postconditions
    w = info.agent._wallet
    OCEAN1 = w.OCEAN()
    assert w._cached_OCEAN_base is not None
    OCEAN2 = fromBase18(int(w._cached_OCEAN_base))
    OCEAN3 = fromBase18(OCEAN.balanceOf(account))
    assert OCEAN1 == OCEAN2 == OCEAN3, (OCEAN1, OCEAN2, OCEAN3)

    return info


@enforce_types
def _createDT(account):
    DT = oceanv3util.newDatatoken("foo", "DT1", "DT1", toBase18(_DT_INIT), account)
    DT.mint(account.address, toBase18(_DT_INIT), txdict(account))
    return DT


@enforce_types
def _createPool(DT, account):
    # Create OCEAN-DT pool
    OCEAN = globaltokens.OCEANtoken()
    pool = oceanv3util.newBPool(account)

    DT.approve(pool.address, toBase18(_DT_STAKE), txdict(account))
    OCEAN.approve(pool.address, toBase18(_OCEAN_STAKE), txdict(account))

    assert OCEAN.balanceOf(account) >= toBase18(_DT_STAKE)
    assert OCEAN.balanceOf(account) >= toBase18(_OCEAN_STAKE)
    pool.bind(
        DT.address, toBase18(_DT_STAKE), toBase18(_POOL_WEIGHT_DT), txdict(account)
    )
    pool.bind(
        OCEAN.address,
        toBase18(_OCEAN_STAKE),
        toBase18(_POOL_WEIGHT_OCEAN),
        txdict(account),
    )

    pool.finalize(txdict(account))

    return pool
