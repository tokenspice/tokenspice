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
    """An AgentWallet holds balances of USD, OCEAN, and DTs for a given Agent.
    It also serves as a thin-layer conversion interface between
    -the top-level system which operates in floats
    -the EVM system which operates in base18-value ints

    USD is stored as a variable internally. OCEAN & DTs are on EVM.
    """

    def __init__(self, USD:float=0.0, OCEAN:float=0.0):
        self._web3wallet = web3wallet.randomWeb3Wallet()

        #Give the new wallet ETH to pay gas fees (but don't track otherwise)
        self._web3wallet.fundFromAbove(toBase18(0.01)) #magic number
        
        #USD
        self._USD = USD #lump in ETH too

        #OCEAN
        globaltokens.mintOCEAN(address=self._web3wallet.address,
                               value_base=toBase18(OCEAN))
        self._cached_OCEAN_base = None #for speed

        #amount 
        self._total_USD_in:float = USD
        self._total_OCEAN_in:float = OCEAN
        
    @property
    def _address(self):
         return self._web3wallet.address

    #===================================================================    
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
            if (1.0 - tol) <= amt/self._USD <= (1.0 + tol):
                self._USD = amt #avoid floating point roundoff
        if amt > self._USD:
            amt = round(amt, 12)
        if amt > self._USD:
            raise ValueError("USD withdraw amount (%s) exceeds holdings (%s)"
                             % (amt, self._USD))
        self._USD -= amt

    def transferUSD(self, dst_wallet, amt: float) -> None:
        assert isinstance(dst_wallet, AgentWallet) or \
            isinstance(dst_wallet, BurnWallet)
        self.withdrawUSD(amt)
        dst_wallet.depositUSD(amt)

    def totalUSDin(self) -> float:
        return self._total_USD_in

    #===================================================================   
    def OCEAN(self) -> float:
        return fromBase18(self._OCEAN_base())

    def _OCEAN_base(self) -> int:
        if self._cached_OCEAN_base is None:
            self._cached_OCEAN_base = globaltokens.OCEANtoken().balanceOf_base(self._address)
        return self._cached_OCEAN_base            
        
    def depositOCEAN(self, amt: float) -> None:
        assert amt >= 0.0
        globaltokens.mintOCEAN(self._address, toBase18(amt))
        self._total_OCEAN_in += amt
        self._cached_OCEAN_base = None #reset due to write action
        
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
        
        if isinstance(dst_wallet, AgentWallet):
            dst_wallet._total_OCEAN_in += amt
        
        self._cached_OCEAN_base = None #reset due to write action
        dst_wallet._cached_OCEAN_base = None #""

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
