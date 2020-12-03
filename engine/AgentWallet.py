import logging
log = logging.getLogger('wallet')

import enforce
import typing

from engine.evm import globaltokens
from util import constants 
from util.strutil import asCurrency
from web3tools import web3util, web3wallet
from web3tools.web3util import fromBase18, toBase18

@enforce.runtime_validation
class AgentWallet:
    """An AgentWallet holds balances of USD, etc for a given Agent.
    It also serves as a thin-layer conversion interface between
    -the top-level system which operates in floats
    -the EVM system which operates in base18-value ints
    """

    def __init__(self, USD:float=0.0, OCEAN:float=0.0):
        self._web3wallet = web3wallet.randomWeb3Wallet()

        #Give the new wallet ETH to pay gas fees (but don't track otherwise)
        self._web3wallet.fundFromAbove(toBase18(0.01)) #magic number
        
        #amount held
        globaltokens.mintUSD(address=self._web3wallet.address,
                             value_base=toBase18(USD)) #lump in ETH too
        globaltokens.mintOCEAN(address=self._web3wallet.address,
                               value_base=toBase18(OCEAN))
        #self._cached_USD = None #for speed
        #self._cached_OCEAN = None # ""

        #amount 
        self._total_USD_in:float = USD
        self._total_OCEAN_in:float = OCEAN
        
    @property
    def _address(self):
         return self._web3wallet.address

    #===================================================================    
    def USD(self) -> float:
        return fromBase18(self._USD_base())

    def _USD_base(self) -> int:
        return globaltokens.USDtoken().balanceOf_base(self._address)
        
    def depositUSD(self, amount: float) -> None:
        assert amount >= 0.0
        globaltokens.mintUSD(self._address, toBase18(amount))
        self._total_USD_in += amount
        
    def withdrawUSD(self, amt: float) -> None:
        self.transferUSD(_BURN_WALLET, amt)

    def transferUSD(self, dst_wallet, amt: float) -> None:
        assert isinstance(dst_wallet, AgentWallet) or \
            isinstance(dst_wallet, BurnWallet)
        dst_address = dst_wallet._address
        
        amt_base = toBase18(amt)
        assert amt_base >= 0
        if amt_base == 0:
            return
        
        USD_base = self._USD_base()
        if USD_base == 0:
            raise ValueError("no funds to transfer from")

        tol = 1e-12
        if (1.0 - tol) <= amt/fromBase18(USD_base) <= (1.0 + tol):
            amt_base = USD_base

        if amt_base > USD_base:
            raise ValueError("transfer amt (%s) exceeds USD holdings (%s)"
                             % (fromBase18(amt_base), fromBase18(USD_base)))

        globaltokens.USDtoken().transfer(
            dst_address, amt_base, self._web3wallet)

    def totalUSDin(self) -> float:
        return self._total_USD_in

    #===================================================================    
    def OCEAN(self) -> float:
        return fromBase18(self._OCEAN_base())

    def _OCEAN_base(self) -> int:
        return globaltokens.OCEANtoken().balanceOf_base(self._address)
        
    def depositOCEAN(self, amount: float) -> None:
        assert amount >= 0.0
        globaltokens.mintOCEAN(self._address, toBase18(amount))
        self._total_OCEAN_in += amount
        
    def withdrawOCEAN(self, amt: float) -> None:
        self.transferOCEAN(_BURN_WALLET, amt)

    def transferOCEAN(self, dst_wallet, amt: float) -> None:
        assert isinstance(dst_wallet, AgentWallet) or \
            isinstance(dst_wallet, BurnWallet)
        dst_address = dst_wallet._address
        
        amt_base = toBase18(amt)
        assert amt_base >= 0
        if amt_base == 0:
            return
        
        OCEAN_base = self._OCEAN_base()
        if OCEAN_base == 0:
            raise ValueError("no funds to transfer from")

        tol = 1e-12
        if (1.0 - tol) <= amt/fromBase18(OCEAN_base) <= (1.0 + tol):
            amt_base = OCEAN_base

        if amt_base > OCEAN_base:
            raise ValueError("transfer amt (%s) exceeds OCEAN holdings (%s)"
                             % (fromBase18(amt_base), fromBase18(OCEAN_base)))

        globaltokens.OCEANtoken().transfer(
            dst_address, amt_base, self._web3wallet)

    def totalOCEANin(self) -> float:
        return self._total_OCEAN_in
    

    #===================================================================
    def __str__(self) -> str:
        s = []
        s += ["AgentWallet={\n"]
        s += ['USD=%s' % asCurrency(self.USD())]
        s += ['; OCEAN=%.6f' % self.OCEAN()]
        s += ['; total_USD_in=%s' % asCurrency(self.totalUSDin())]
        s += ['; total_OCEAN_in=%.6f' % self.totalOCEANin()]
        s += [" /AgentWallet}"]
        return "".join(s)

class BurnWallet:
    def __init__(self):
        self._address = constants.BURN_ADDRESS
_BURN_WALLET = BurnWallet()
