from enforce_typing import enforce_types # type: ignore[import]
import web3

from util import constants
from web3tools import web3util, web3wallet
from web3engine import datatoken, dtfactory

_MINTERS = {} # symbol : _Minter

@enforce_types
def mintOCEAN(address:str, value_base:int):
    return _minter('OCEAN').mint(address, value_base)

@enforce_types
def OCEAN_address() -> str:
    return OCEANtoken().address

_OCEAN_TOKEN = None
@enforce_types
def OCEANtoken() -> datatoken.Datatoken:
    global _OCEAN_TOKEN
    if _OCEAN_TOKEN is None:
        _OCEAN_TOKEN = _minter('OCEAN').token()
    return _OCEAN_TOKEN

#===================================================================
@enforce_types
def _minter(symbol:str):
    global _MINTERS
    if symbol not in _MINTERS:
        _MINTERS[symbol] = _Minter(symbol)
    return _MINTERS[symbol]

@enforce_types
class _Minter:
    def __init__(self, symbol:str):
        #A random wallet won't have ETH for gas fees. So, use
        # 'TEST_PRIVATE_KEY1' which got funds in ganache startup (see deploy.py)
        network = web3util.get_network()
        key1 = web3util.confFileValue(network, 'TEST_PRIVATE_KEY1')        
        self._web3_wallet = web3wallet.Web3Wallet(key1)
        
        factory = dtfactory.DTFactory()
        token_address = factory.createToken(
            '', symbol, symbol, constants.HUGEINT, self._web3_wallet)
        self._token = datatoken.Datatoken(token_address)

    def mint(self, address:str, value_base:int):
        return self._token.mint(address, value_base, self._web3_wallet)

    def token(self) -> datatoken.Datatoken:
        return self._token

