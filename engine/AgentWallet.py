import logging
log = logging.getLogger('wallet')

from enforce_typing import enforce_types
import typing

from web3engine import bpool, btoken, datatoken, globaltokens
from util import constants 
from util.strutil import asCurrency
from web3tools import web3util, web3wallet
from web3tools.web3util import fromBase18, toBase18

@enforce_types
class AgentWallet:
    """An AgentWallet holds balances of USD, OCEAN, and DTs for a given Agent.
    It also serves as a thin-layer conversion interface between
    -the top-level system which operates in floats
    -the EVM system which operates in base18-value ints

    USD is stored as a variable internally. OCEAN & DTs are on EVM.
    """

    def __init__(self, USD:float=0.0, OCEAN:float=0.0, private_key=None):
        if private_key is None:
            self._web3wallet = web3wallet.randomWeb3Wallet()
        else:
            self._web3wallet = web3wallet.Web3Wallet(private_key)

        #Give the new wallet ETH to pay gas fees (but don't track otherwise)
        self._web3wallet.fundFromAbove(toBase18(0.01)) #magic number
        
        #USD
        self._USD = USD #lump in ETH too

        #OCEAN
        globaltokens.mintOCEAN(address=self._web3wallet.address,
                               value_base=toBase18(OCEAN))
        self._cached_OCEAN_base: typing.Union[int,None] = None #for speed

        #amount 
        self._total_USD_in:float = USD
        self._total_OCEAN_in:float = OCEAN

    def resetCachedInfo(self):
        self._cached_OCEAN_base = None
        
    @property
    def _address(self):
         return self._web3wallet.address
     
    #=================================================================== 
    #USD-related   
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
        assert isinstance(dst_wallet, AgentWallet)
        self.withdrawUSD(amt)
        dst_wallet.depositUSD(amt)

    def totalUSDin(self) -> float:
        return self._total_USD_in

    #===================================================================  
    #OCEAN-related 
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
        self.resetCachedInfo()
        
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
        
        dst_wallet._total_OCEAN_in += amt
        self.resetCachedInfo()
        dst_wallet.resetCachedInfo()        

    def totalOCEANin(self) -> float:
        return self._total_OCEAN_in
        
    #===================================================================
    #ETH-related. Not much here because we use it little, just for gas
    def ETH(self) -> float:
        return fromBase18(self._ETH_base())

    def _ETH_base(self) -> int: #i.e. num wei
        return self._web3wallet.ETH_base()
    
    #===================================================================
    #datatoken and pool-related
    def DT(self, dt:datatoken.Datatoken) -> float:
        return fromBase18(self._DT_base(dt))

    def _DT_base(self, dt:datatoken.Datatoken) -> int: 
        return dt.balanceOf_base(self._address)
    
    def BPT(self, pool:bpool.BPool) -> float:
        return fromBase18(self._BPT_base(pool))
    
    def _BPT_base(self, pool:bpool.BPool) -> int:
        return pool.balanceOf_base(self._address)

    def sellDT(self, pool:bpool.BPool, DT:datatoken.Datatoken,
               DT_sell_amt:float, min_OCEAN_amt:float=0.0):
        """Swap DT for OCEAN. min_OCEAN_amt>0 protects from slippage."""
        DT.approve(pool.address, toBase18(DT_sell_amt),
                   from_wallet=self._web3wallet)

        pool.swapExactAmountIn(
            tokenIn_address=DT.address,  # entering pool
            tokenAmountIn_base=toBase18(DT_sell_amt),  # ""
            tokenOut_address=globaltokens.OCEAN_address(),  # leaving pool
            minAmountOut_base=toBase18(min_OCEAN_amt),  # ""
            maxPrice_base=2 ** 255, #limit by min_OCEAN_amt, not price
            from_wallet=self._web3wallet,
        )
        self.resetCachedInfo()
    
    def buyDT(self, pool:bpool.BPool, DT:datatoken.Datatoken,
              DT_buy_amt:float, max_OCEAN_allow:float):
        """Swap OCEAN for DT """
        OCEAN = globaltokens.OCEANtoken()
        OCEAN.approve(pool.address, toBase18(max_OCEAN_allow),
                      from_wallet=self._web3wallet)

        pool.swapExactAmountOut(
            tokenIn_address=globaltokens.OCEAN_address(),
            maxAmountIn_base=toBase18(max_OCEAN_allow),
            tokenOut_address=DT.address,
            tokenAmountOut_base=toBase18(DT_buy_amt),
            maxPrice_base=2 ** 255,
            from_wallet=self._web3wallet,
        )
        self.resetCachedInfo()
                        
    def stakeOCEAN(self, OCEAN_stake:float, pool:bpool.BPool):
        """Convert some OCEAN to DT, then add both as liquidity."""
        OCEAN = globaltokens.OCEANtoken()
        OCEAN.approve(pool.address, toBase18(OCEAN_stake),
                      from_wallet=self._web3wallet)
        pool.joinswapExternAmountIn(
            tokenIn_address=globaltokens.OCEAN_address(),
            tokenAmountIn_base=toBase18(OCEAN_stake),
            minPoolAmountOut_base=toBase18(0.0),
            from_wallet=self._web3wallet)
        self.resetCachedInfo()
        
    def unstakeOCEAN(self, BPT_unstake:float, pool:bpool.BPool):
        pool.exitswapPoolAmountIn(
            tokenOut_address=globaltokens.OCEAN_address(),
            poolAmountIn_base=toBase18(BPT_unstake),
            minAmountOut_base=toBase18(0.0),
            from_wallet=self._web3wallet)
        self.resetCachedInfo()

    #===================================================================
    def __str__(self) -> str:
        s = []
        s += ["AgentWallet={\n"]
        s += ['USD=%s' % asCurrency(self.USD())]
        s += ['; OCEAN=%.6f' % self.OCEAN()]
        s += ['; DT=(not shown), BPT=(not shown)']
        s += ['; total_USD_in=%s' % asCurrency(self.totalUSDin())]
        s += ['; total_OCEAN_in=%.6f' % self.totalOCEANin()]
        s += [" /AgentWallet}"]
        return "".join(s)

#========================================================================
#burn-related
class BurnWallet:
    """This is a wallet-level interface to send funds-to-burn to.
    This is *not* a burner wallet, that's a completely different concept.
    """
    def __init__(self):
        self._address = constants.BURN_ADDRESS
        self._total_OCEAN_in:float = 0.0
        
    def resetCachedInfo(self):
        pass

_BURN_WALLET = BurnWallet()
