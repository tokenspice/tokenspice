import brownie
from enforce_typing import enforce_types

from util.constants import BROWNIE_PROJECT, GOD_ACCOUNT
from util.base18 import toBase18

_OCEAN_TOKEN = GOD_ACCOUNT.deploy(
    BROWNIE_PROJECT.Simpletoken, 'OCEAN', 'OCEAN', 18, toBase18(1e9))
    
@enforce_types
def OCEAN_address() -> str:
    return _OCEAN_TOKEN.address

@enforce_types
def OCEANtoken():
    return _OCEAN_TOKEN

@enforce_types
def fundOCEANFromAbove(dst_address:str, amount_base:int):
    _OCEAN_TOKEN.transfer(dst_address, amount_base, {'from':GOD_ACCOUNT})
