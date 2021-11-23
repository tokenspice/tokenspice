import brownie
from brownie import Wei
from enforce_typing import enforce_types

from util.constants import BROWNIE_PROJECT, GOD_ACCOUNT

_OCEAN_TOKEN = GOD_ACCOUNT.deploy(
    BROWNIE_PROJECT.Simpletoken, 'OCEAN', 'OCEAN', 18, Wei('1000000 ether'))
    
@enforce_types
def OCEAN_address() -> str:
    return _OCEAN_TOKEN.address

@enforce_types
def OCEANtoken():
    return _OCEAN_TOKEN

@enforce_types
def fundOCEANFromAbove(dst_address:str, amount_base:int):
    _OCEAN_TOKEN.transfer(dst_address, amount_base, {'from':GOD_ACCOUNT})
