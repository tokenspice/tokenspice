import logging
log = logging.getLogger('wallet')

import enforce
import typing

from util.constants import SAFETY
from util.strutil import asCurrency

@enforce.runtime_validation
class Wallet:
    """Wallets hold balances of USD, etc for Agents"""

    def __init__(self, USD=0.0, OCEAN=0.0):
        #amount held
        self._USD: float = USD #lump in ETH too
        self._OCEAN: float = OCEAN

        #amount 
        self._total_USD_in = 0.0
        self._total_OCEAN_in = 0.0

    #===================================================================
    def USD(self) -> float:
        return self._USD
        
    def depositUSD(self, amount: float) -> None:
        assert amount >= 0.0
        self._USD += amount
        self._total_USD_in += amount

    def withdrawUSD(self, amount: float) -> None:
        assert amount >= 0.0
        if amount > 0.0 and self._USD > 0.0:
            tol = 1e-12
            if (1.0 - tol) <= amount/self._USD <= (1.0 + tol):
                self._USD = amount #avoid floating point roundoff
        if amount > self._USD:
            amount = round(amount, 12)
        if amount > self._USD:
            raise ValueError("USD withdraw amount (%s) exceeds holdings (%s)"
                             % (amount, self._USD))
        self._USD -= amount

    def totalUSDin(self) -> float:
        return self._total_USD_in
        
    #===================================================================
    def OCEAN(self) -> float:
        return self._OCEAN
        
    def depositOCEAN(self, amount: float) -> None:
        assert amount >= 0.0
        self._OCEAN += amount
        self._total_OCEAN_in += amount

    def withdrawOCEAN(self, amount: float) -> None:
        assert amount >= 0.0
        if amount > self._OCEAN:
            amount = round(amount, 14)
        if amount > self._OCEAN:
            raise ValueError("OCEAN withdraw amount (%s) exceeds holdings (%s)"
                             % (amount, self._OCEAN))
        self._OCEAN -= amount

    def totalOCEANin(self) -> float:
        return self._total_OCEAN_in

    def __str__(self) -> str:
        s = []
        s += ["Wallet={\n"]
        s += 'USD=%s' % asCurrency(self._USD)
        s += '; OCEAN=%.6f' % self._OCEAN
        s += '; total_USD_in=%s' % asCurrency(self._total_USD_in)
        s += '; total_OCEAN_in=%.6f' % self._total_OCEAN_in
        s += [" /Wallet}"]
        return "".join(s)
