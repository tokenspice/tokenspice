"""
Main classes in this module:
-AgentWalletAbstract - abstract interface
-AgentWalletNoEvm - no-EVM wallet
-AgentWalletEvm - EVM wallet

Support classes include:
-UsdNoEvmWalletMixIn - no-EVM implement USD deposit/withdraw/..
-OceanNoEvmWalletMixIn - no-EVM implement OCEAN deposit/withdraw/..
-StrMixIn - for __str__()
-BurnWallet - special wallet to burn to
"""

from abc import abstractmethod, ABC
import logging
import typing

import brownie
from brownie.network.account import Account  # pylint: disable=no-name-in-module
from enforce_typing import enforce_types

from util import constants
from util import globaltokens
from util.base18 import toBase18, fromBase18
from util.constants import GOD_ACCOUNT
from util.strutil import asCurrency

log = logging.getLogger("wallet")


@enforce_types
class AgentWalletAbstract(ABC):
    """
    An AgentWallet holds balances of USD and OCEAN for a given Agent.

    This is an abstract class. It has children that (a) do (b) don't use Evm.
    """

    @abstractmethod
    def __init__(self, USD: float = 0.0, OCEAN: float = 0.0, private_key=None):
        pass

    # ===================================================================
    # OCEAN-related
    @abstractmethod
    def OCEAN(self) -> float:
        pass

    @abstractmethod
    def depositOCEAN(self, amt: float) -> None:
        pass

    @abstractmethod
    def withdrawOCEAN(self, amt: float) -> None:
        pass

    @abstractmethod
    def transferOCEAN(self, dst_wallet, amt: float) -> None:
        pass

    @abstractmethod
    def totalOCEANin(self) -> float:
        pass

    # ===================================================================
    # USD-related
    @abstractmethod
    def USD(self) -> float:
        pass

    @abstractmethod
    def depositUSD(self, amt: float) -> None:
        pass

    @abstractmethod
    def withdrawUSD(self, amt: float) -> None:
        pass

    @abstractmethod
    def transferUSD(self, dst_wallet, amt: float) -> None:
        pass

    @abstractmethod
    def totalUSDin(self) -> float:
        pass


@enforce_types
class UsdNoEvmWalletMixIn:
    def __init__(self, USD: float):
        self._USD = USD
        self._total_USD_in: float = USD

    def USD(self) -> float:
        return self._USD

    def depositUSD(self, amt: float) -> None:
        assert amt >= 0.0
        self._USD += amt
        self._total_USD_in += amt

    def withdrawUSD(self, amt: float) -> None:
        assert amt >= 0.0
        if amt > 0.0 and self._USD > 0.0:
            tol = 1e-12
            if (1.0 - tol) <= amt / self._USD <= (1.0 + tol):
                self._USD = amt  # avoid floating point roundoff
        if amt > self._USD:
            amt = round(amt, 12)
        if amt > self._USD:
            raise ValueError(
                "USD withdraw amount (%s) exceeds holdings (%s)" % (amt, self._USD)
            )
        self._USD -= amt

    def transferUSD(self, dst_wallet, amt: float) -> None:
        assert isinstance(dst_wallet, AgentWalletAbstract)

        self.withdrawUSD(amt)
        dst_wallet.depositUSD(amt)

    def totalUSDin(self) -> float:
        return self._total_USD_in


@enforce_types
class OceanNoEvmWalletMixIn:
    def __init__(self, OCEAN: float):
        self._OCEAN = OCEAN
        self._total_OCEAN_in: float = OCEAN

    def OCEAN(self) -> float:
        return self._OCEAN

    def depositOCEAN(self, amt: float) -> None:
        assert amt >= 0.0
        self._OCEAN += amt
        self._total_OCEAN_in += amt

    def withdrawOCEAN(self, amt: float) -> None:
        assert amt >= 0.0
        if amt > 0.0 and self._OCEAN > 0.0:
            tol = 1e-12
            if (1.0 - tol) <= amt / self._OCEAN <= (1.0 + tol):
                self._OCEAN = amt  # avoid floating point roundoff
        if amt > self._OCEAN:
            amt = round(amt, 12)
        if amt > self._OCEAN:
            raise ValueError(
                "OCEAN withdraw amount (%s) exceeds holdings (%s)" % (amt, self._OCEAN)
            )
        self._OCEAN -= amt

    def transferOCEAN(self, dst_wallet, amt: float) -> None:
        assert isinstance(dst_wallet, AgentWalletAbstract)
        self.withdrawOCEAN(amt)
        dst_wallet.depositOCEAN(amt)

    def totalOCEANin(self) -> float:
        return self._total_OCEAN_in


@enforce_types
class StrMixIn:
    def __str__(self) -> str:
        s = []
        s += ["AgentWallet={\n"]
        s += ["USD=%s" % asCurrency(self.USD())]  # type:ignore
        s += ["; OCEAN=%.6f" % self.OCEAN()]  # type:ignore
        s += ["; total_USD_in=%s" % asCurrency(self.totalUSDin())]  # type:ignore
        s += ["; total_OCEAN_in=%.6f" % self.totalOCEANin()]  # type:ignore
        s += [" /AgentWallet}"]
        return "".join(s)


@enforce_types
class AgentWalletNoEvm(
    UsdNoEvmWalletMixIn,
    OceanNoEvmWalletMixIn,
    StrMixIn,
    AgentWalletAbstract,
):
    """
    In this wallet subclass, USD and OCEAN are stored in pure Python. No Evm.
    """

    def __init__(self, USD: float = 0.0, OCEAN: float = 0.0, private_key=None):
        assert private_key is None, "if no evm, no private key"
        AgentWalletAbstract.__init__(self, USD, OCEAN, private_key)
        UsdNoEvmWalletMixIn.__init__(self, USD)
        OceanNoEvmWalletMixIn.__init__(self, OCEAN)

        # postconditions
        assert self.USD() == USD
        assert self.OCEAN() == OCEAN


@enforce_types
class AgentWalletEvm(
    UsdNoEvmWalletMixIn,
    StrMixIn,
    AgentWalletAbstract,
):
    """
    In this wallet subclass, OCEAN is on Evm. USD is stored in Python.

    It also has functionality for ETH (for gas), DTs, and BPTs / staking.

    It also serves as a thin-layer conversion interface between
    -the top-level system which operates in floats
    -the Evm system which operates in base18-value ints
    """

    def __init__(self, USD: float = 0.0, OCEAN: float = 0.0, private_key=None):
        AgentWalletAbstract.__init__(self, USD, OCEAN, private_key)
        UsdNoEvmWalletMixIn.__init__(self, USD)

        self._account: Account = None

        accounts = brownie.network.accounts
        if private_key is None:
            self._account = accounts.add()
        else:
            self._account = accounts.add(private_key=private_key)

        # Give the new wallet ETH to pay gas fees (but don't track otherwise)
        GOD_ACCOUNT.transfer(self._account, "0.01 ether")

        # OCEAN is tracked in EVM, not here. But we cache here for speed
        self._burnOCEAN_nocache()  # ensure 0 OCEAN (eg >1 unit tests)
        self._cached_OCEAN_base: typing.Union[int, None] = None
        self._total_OCEAN_in: float = OCEAN
        assert self.OCEAN() == 0.0

        globaltokens.fundOCEANFromAbove(self._account.address, toBase18(OCEAN))
        self._cached_OCEAN_base = None

        # postconditions
        assert self.USD() == USD
        assert self.OCEAN() == OCEAN

    @property
    def account(self):
        """Returns self's brownie account"""
        return self._account

    @property
    def address(self) -> str:
        return self._account.address

    def _burnOCEAN_nocache(self):
        """
        If this agent has any OCEAN, burn it.
        Explicitly don't use caching, so __init__ can safely call this
        """
        OCEAN_token = globaltokens.OCEANtoken()
        OCEAN_balance_base = OCEAN_token.balanceOf(self._account)
        if OCEAN_balance_base > 0:
            OCEAN_token.transfer(
                _BURN_WALLET.address, OCEAN_balance_base, {"from": self._account}
            )

    def resetCachedInfo(self):
        self._cached_OCEAN_base = None

    # ===================================================================
    # USD-related
    def _USD_base(self) -> int:
        pass

    # ===================================================================
    # OCEAN-related
    def OCEAN(self) -> float:
        return fromBase18(self._OCEAN_base())

    def _OCEAN_base(self) -> int:
        OCEAN_token = globaltokens.OCEANtoken()
        if self._cached_OCEAN_base is None:
            self._cached_OCEAN_base = OCEAN_token.balanceOf(self.address)

        assert self._cached_OCEAN_base == OCEAN_token.balanceOf(self.address), (
            self._cached_OCEAN_base,
            OCEAN_token.balanceOf(self.address),
            self._account.address,
        )

        return self._cached_OCEAN_base

    def depositOCEAN(self, amt: float) -> None:
        assert amt >= 0.0
        globaltokens.fundOCEANFromAbove(self._account.address, toBase18(amt))
        self._total_OCEAN_in += amt
        self.resetCachedInfo()

    def withdrawOCEAN(self, amt: float) -> None:
        self.transferOCEAN(_BURN_WALLET, amt)

    def transferOCEAN(self, dst_wallet, amt: float) -> None:
        assert isinstance(dst_wallet, (AgentWalletEvm, BurnWallet))
        dst_address = dst_wallet.address

        amt_base = toBase18(amt)
        assert amt_base >= 0
        if amt_base == 0:
            return

        OCEAN_base = self._OCEAN_base()
        if OCEAN_base == 0:
            raise ValueError("no funds to transfer from")

        tol = 1e-12
        if (1.0 - tol) <= amt / fromBase18(OCEAN_base) <= (1.0 + tol):
            amt_base = OCEAN_base

        if amt_base > OCEAN_base:
            raise ValueError(
                "transfer amt (%s) exceeds OCEAN holdings (%s)"
                % (fromBase18(amt_base), fromBase18(OCEAN_base))
            )

        globaltokens.OCEANtoken().transfer(
            dst_address, amt_base, {"from": self._account}
        )

        dst_wallet._total_OCEAN_in += amt
        self.resetCachedInfo()
        dst_wallet.resetCachedInfo()

    def totalOCEANin(self) -> float:
        return self._total_OCEAN_in

    # ===================================================================
    # ETH-related. Not much here because we use it little, just for gas
    def ETH(self) -> float:
        return fromBase18(self._ETH_base())

    def _ETH_base(self) -> int:  # i.e. num wei
        return self._account.balance()

    # ===================================================================
    # datatoken and pool-related
    def DT(self, dt) -> float:
        return fromBase18(self._DT_base(dt))

    def _DT_base(self, dt) -> int:
        return dt.balanceOf(self.address)

    def BPT(self, pool) -> float:
        return fromBase18(self._BPT_base(pool))

    def _BPT_base(self, pool) -> int:
        return pool.balanceOf(self.address)

    def sellDT(self, pool, DT, DT_sell_amt: float, min_OCEAN_amt: float = 0.0):
        """Swap DT for OCEAN. min_OCEAN_amt>0 protects from slippage."""
        DT.approve(pool.address, toBase18(DT_sell_amt), {"from": self._account})

        tokenIn_address = DT.address  # entering pool
        tokenAmountIn_base = toBase18(DT_sell_amt)  # ""
        tokenOut_address = globaltokens.OCEAN_address()  # leaving pool
        minAmountOut_base = toBase18(min_OCEAN_amt)  # ""
        maxPrice_base = 2 ** 255  # limit by min_OCEAN_amt, not price
        pool.swapExactAmountIn(
            tokenIn_address,
            tokenAmountIn_base,
            tokenOut_address,
            minAmountOut_base,
            maxPrice_base,
            {"from": self._account},
        )
        self.resetCachedInfo()

    def buyDT(self, pool, DT, DT_buy_amt: float, max_OCEAN_allow: float):
        """Swap OCEAN for DT"""
        OCEAN = globaltokens.OCEANtoken()
        OCEAN.approve(pool.address, toBase18(max_OCEAN_allow), {"from": self._account})

        tokenIn_address = globaltokens.OCEAN_address()
        maxAmountIn_base = toBase18(max_OCEAN_allow)
        tokenOut_address = DT.address
        tokenAmountOut_base = toBase18(DT_buy_amt)
        maxPrice_base = 2 ** 255
        pool.swapExactAmountOut(
            tokenIn_address,
            maxAmountIn_base,
            tokenOut_address,
            tokenAmountOut_base,
            maxPrice_base,
            {"from": self._account},
        )
        self.resetCachedInfo()

    def stakeOCEAN(self, OCEAN_stake: float, pool):
        """Convert some OCEAN to DT, then add both as liquidity."""
        OCEAN = globaltokens.OCEANtoken()
        OCEAN.approve(pool.address, toBase18(OCEAN_stake), {"from": self._account})
        tokenIn_address = globaltokens.OCEAN_address()
        tokenAmountIn_base = toBase18(OCEAN_stake)
        minPoolAmountOut_base = toBase18(0.0)
        pool.joinswapExternAmountIn(
            tokenIn_address,
            tokenAmountIn_base,
            minPoolAmountOut_base,
            {"from": self._account},
        )
        self.resetCachedInfo()

    def unstakeOCEAN(self, BPT_unstake: float, pool):
        tokenOut_address = globaltokens.OCEAN_address()
        poolAmountIn_base = toBase18(BPT_unstake)
        minAmountOut_base = toBase18(0.0)
        pool.exitswapPoolAmountIn(
            tokenOut_address,
            poolAmountIn_base,
            minAmountOut_base,
            {"from": self._account},
        )
        self.resetCachedInfo()

    def transferDT(self, dst_wallet, DT, amt: float) -> None:
        assert isinstance(dst_wallet, (AgentWalletEvm, BurnWallet))
        dst_address = dst_wallet.address

        amt_base = toBase18(amt)
        assert amt_base >= 0
        if amt_base == 0:
            return

        DT_base = self._DT_base(DT)
        if DT_base == 0:
            raise ValueError("no data tokens to transfer")

        tol = 1e-12
        if (1.0 - tol) <= amt / fromBase18(DT_base) <= (1.0 + tol):
            amt_base = DT_base

        if amt_base > DT_base:
            raise ValueError(
                "transfer amt (%s) exceeds DT holdings (%s)"
                % (fromBase18(amt_base), fromBase18(DT_base))
            )

        DT.transfer(dst_address, amt_base, {"from": self._account})


# ========================================================================
# burn-related
@enforce_types
class BurnWallet:
    """This is a wallet-level interface to send funds-to-burn to.
    This is *not* a burner wallet, that's a completely different concept.
    """

    def __init__(self):
        self.address = constants.BURN_ADDRESS
        self._total_OCEAN_in: float = 0.0

    def resetCachedInfo(self):
        pass


_BURN_WALLET = BurnWallet()
