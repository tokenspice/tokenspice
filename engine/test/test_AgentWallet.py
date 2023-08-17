from enforce_typing import enforce_types
import pytest
from pytest import approx

from agents.test.conftest import _DT_INIT, _DT_STAKE
from engine.AgentWallet import (
    AgentWalletNoEvm,
    AgentWalletEvm,
    BurnWallet,
    UsdNoEvmWalletMixIn,
    OceanNoEvmWalletMixIn,
)
from util import constants, globaltokens
from util.base18 import fromBase18


@enforce_types
def testUsdNoEvmWalletMixIn():
    m = UsdNoEvmWalletMixIn(USD=3.2)

    assert m._USD == 3.2
    assert m.USD() == 3.2
    assert m._total_USD_in == 3.2
    assert m.totalUSDin() == 3.2

    m.depositUSD(1.1)
    assert m._USD == approx(4.3)
    assert m.USD() == approx(4.3)
    assert m._total_USD_in == approx(4.3)
    assert m.totalUSDin() == approx(4.3)

    m.withdrawUSD(0.1)
    assert m._USD == approx(4.2)
    assert m.USD() == approx(4.2)
    assert m._total_USD_in == approx(4.3)  # don't shrink; it tracks total income
    assert m.totalUSDin() == approx(4.3)  # ""

    w2 = AgentWalletNoEvm()
    m.transferUSD(w2, 0.2)
    assert m._USD == approx(4.0)
    assert m.USD() == approx(4.0)
    assert m._total_USD_in == approx(4.3)  # don't shrink; it tracks total income
    assert m.totalUSDin() == approx(4.3)  # ""


# =======================================================================
@enforce_types
def testOceanNoEvmWalletMixIn():
    m = OceanNoEvmWalletMixIn(OCEAN=3.2)

    assert m._OCEAN == 3.2
    assert m.OCEAN() == 3.2
    assert m._total_OCEAN_in == 3.2
    assert m.totalOCEANin() == 3.2

    m.depositOCEAN(1.1)
    assert m._OCEAN == approx(4.3)
    assert m.OCEAN() == approx(4.3)
    assert m._total_OCEAN_in == approx(4.3)
    assert m.totalOCEANin() == approx(4.3)

    m.withdrawOCEAN(0.1)
    assert m._OCEAN == approx(4.2)
    assert m.OCEAN() == approx(4.2)
    assert m._total_OCEAN_in == approx(4.3)  # don't shrink; it tracks total income
    assert m.totalOCEANin() == approx(4.3)  # ""

    w2 = AgentWalletNoEvm()
    m.transferOCEAN(w2, 0.2)
    assert m._OCEAN == approx(4.0)
    assert m.OCEAN() == approx(4.0)
    assert m._total_OCEAN_in == approx(4.3)  # don't shrink; it tracks total income
    assert m.totalOCEANin() == approx(4.3)  # ""


# =======================================================================
# =======================================================================
# BOTH AgentWalletEvm *and* AgentWalletNoEvm
@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testInitiallyEmpty(_AgentWallet):
    w = _AgentWallet()

    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0


@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testInitiallyFilled(_AgentWallet):
    w = _AgentWallet(USD=1.2, OCEAN=3.4)

    assert w.USD() == 1.2
    assert w.OCEAN() == 3.4


# =======================================================================
# USD-related
@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testUSD(_AgentWallet):
    w = _AgentWallet()

    w.depositUSD(13.25)
    assert w.USD() == 13.25

    w.depositUSD(1.00)
    assert w.USD() == 14.25

    w.withdrawUSD(2.10)
    assert w.USD() == 12.15

    w.depositUSD(0.0)
    w.withdrawUSD(0.0)
    assert w.USD() == 12.15

    assert w.totalUSDin() == (13.25 + 1.0)

    with pytest.raises(AssertionError):
        w.depositUSD(-5.0)

    with pytest.raises(AssertionError):
        w.withdrawUSD(-5.0)

    with pytest.raises(ValueError):
        w.withdrawUSD(1000.0)


@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testFloatingPointRoundoff_USD(_AgentWallet):
    w = _AgentWallet(USD=2.4)
    w.withdrawUSD(2.4000000000000004)  # should not get ValueError
    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0


@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def test_transferUSD(_AgentWallet):
    w1 = _AgentWallet(USD=10.0)
    w2 = _AgentWallet(USD=1.0)

    w1.transferUSD(w2, 2.0)

    assert w1.USD() == 10.0 - 2.0
    assert w2.USD() == 1.0 + 2.0


# =======================================================================
# OCEAN-related
@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testOCEAN(_AgentWallet):
    w = _AgentWallet()

    w.depositOCEAN(13.25)
    assert w.OCEAN() == 13.25

    w.depositOCEAN(1.00)
    assert w.OCEAN() == 14.25

    w.withdrawOCEAN(2.10)
    assert w.OCEAN() == 12.15

    w.depositOCEAN(0.0)
    w.withdrawOCEAN(0.0)
    assert w.OCEAN() == 12.15

    assert w.totalOCEANin() == (13.25 + 1.0)

    with pytest.raises(AssertionError):
        w.depositOCEAN(-5.0)

    with pytest.raises(AssertionError):
        w.withdrawOCEAN(-5.0)

    with pytest.raises(ValueError):
        w.withdrawOCEAN(1000.0)


@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testFloatingPointRoundoff_OCEAN(_AgentWallet):
    w = _AgentWallet(OCEAN=2.4)
    w.withdrawOCEAN(2.4000000000000004)  # should not get ValueError
    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0


@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def test_transferOCEAN(_AgentWallet):
    w1 = _AgentWallet(OCEAN=10.0)
    w2 = _AgentWallet(OCEAN=1.0)

    w1.transferOCEAN(w2, 2.0)

    assert w1.OCEAN() == (10.0 - 2.0)
    assert w2.OCEAN() == (1.0 + 2.0)


# ===================================================================
# str-related
@enforce_types
@pytest.mark.parametrize("_AgentWallet", [AgentWalletNoEvm, AgentWalletEvm])
def testStr(_AgentWallet):
    w = _AgentWallet()
    assert "AgentWallet" in str(w)


# =======================================================================
# =======================================================================
# =======================================================================
# AgentWalletNoEvm
# (ADD TO ME)

# =======================================================================
# =======================================================================
# =======================================================================
# AgentWalletEvm
# __init__ related
@enforce_types
def test_initFromPrivateKey():
    private_key = "0xbbfbee4961061d506ffbb11dfea64eba16355cbf1d9c29613126ba7fec0aed5d"
    target_address = "0x66aB6D9362d4F35596279692F0251Db635165871"

    w = AgentWalletEvm(private_key=private_key)
    assert w.address == target_address
    assert w.account is not None


@enforce_types
def test_initFromRandom():
    w1 = AgentWalletEvm()
    w2 = AgentWalletEvm()
    assert w1.address != w2.address


@enforce_types
def test_gotSomeETHforGas():
    w = AgentWalletEvm()
    assert w.ETH() > 0.0


# ===================================================================
# ETH-related
@enforce_types
def testETH1():
    # super-basic test for ETH
    w = AgentWalletEvm()
    assert isinstance(w.ETH(), float)


# ===================================================================
# ===================================================================
# ===================================================================
# burn-related
@enforce_types
def testBurnWallet():
    w = BurnWallet()
    assert w.address == constants.BURN_ADDRESS


# ===================================================================
# datatoken and pool-related
@enforce_types
def test_DT(alice_info):
    agent_wallet, DT = alice_info.agent._wallet, alice_info.DT
    DT_amt = agent_wallet.DT(DT)
    assert DT_amt == (_DT_INIT - _DT_STAKE)


@enforce_types
def test_BPT(alice_info):
    agent_wallet, pool = alice_info.agent._wallet, alice_info.pool
    assert agent_wallet.BPT(pool) == 100.0


@enforce_types
def test_poolToDTaddress(alice_info):
    DT, pool = alice_info.DT, alice_info.pool
    assert _poolToDTaddress(pool) == DT.address


@enforce_types
def test_sellDT(alice_info):
    agent_wallet, DT, pool = alice_info.agent._wallet, alice_info.DT, alice_info.pool
    assert _poolToDTaddress(pool) == DT.address

    DT_before, OCEAN_before = agent_wallet.DT(DT), agent_wallet.OCEAN()

    DT_sell_amt = 10.0
    agent_wallet.sellDT(pool, DT, DT_sell_amt=DT_sell_amt)

    DT_after, OCEAN_after = agent_wallet.DT(DT), agent_wallet.OCEAN()

    assert OCEAN_after > OCEAN_before
    assert DT_after == (DT_before - DT_sell_amt)


@enforce_types
def test_buyDT(alice_info):
    alice_info.agent._wallet.resetCachedInfo()
    agent_wallet, DT, pool = alice_info.agent._wallet, alice_info.DT, alice_info.pool
    assert _poolToDTaddress(pool) == DT.address

    DT_before = agent_wallet.DT(DT)
    OCEAN_before = agent_wallet.OCEAN()

    DT_buy_amt = 1.0
    agent_wallet.buyDT(pool, DT, DT_buy_amt=DT_buy_amt, max_OCEAN_allow=OCEAN_before)

    DT_after, OCEAN_after = agent_wallet.DT(DT), agent_wallet.OCEAN()

    assert OCEAN_after < OCEAN_before
    assert DT_after == (DT_before + DT_buy_amt)


@enforce_types
def test_stakeOCEAN(alice_info):
    alice_info.agent._wallet.resetCachedInfo()
    agent_wallet, pool = alice_info.agent._wallet, alice_info.pool
    OCEAN = globaltokens.OCEANtoken()

    BPT_before = agent_wallet.BPT(pool)
    OCEAN1 = agent_wallet.OCEAN()
    OCEAN2 = fromBase18(agent_wallet._cached_OCEAN_base)
    OCEAN3 = fromBase18(OCEAN.balanceOf(agent_wallet.address))
    assert OCEAN1 == OCEAN2 == OCEAN3

    agent_wallet.stakeOCEAN(OCEAN_stake=20.0, pool=pool)

    OCEAN_after, BPT_after = agent_wallet.OCEAN(), agent_wallet.BPT(pool)
    assert OCEAN_after == (OCEAN1 - 20.0)
    assert BPT_after > BPT_before


@enforce_types
def test_unstakeOCEAN(alice_info):
    agent_wallet, pool = alice_info.agent._wallet, alice_info.pool

    BPT_before: float = agent_wallet.BPT(pool)  # type:ignore

    agent_wallet.unstakeOCEAN(BPT_unstake=20.0, pool=pool)

    BPT_after = agent_wallet.BPT(pool)
    assert BPT_after == (BPT_before - 20.0)


# ===================================================================
# helps testing


def _poolToDTaddress(pool) -> str:
    """Return the address of the datatoken of this pool.
    Don't make this public because it has strong assumptions:
    assumes 2 tokens; assumes one token is OCEAN; assumes other is DT
    """
    cur_addrs = pool.getCurrentTokens()
    assert len(cur_addrs) == 2, "this method currently assumes 2 tokens"
    OCEAN_addr = globaltokens.OCEAN_address()
    assert OCEAN_addr in cur_addrs, "this method expects one token is OCEAN"
    DT_addr = [addr for addr in cur_addrs if addr != OCEAN_addr][0]
    return DT_addr
