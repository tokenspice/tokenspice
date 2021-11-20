import brownie
from brownie import Wei
from enforce_typing import enforce_types

from util.constants import BROWNIE_PROJECT, GOD_ACCOUNT

_OCEAN_TOKEN = BROWNIE_PROJECT.Simpletoken.deploy(
    'OCEAN', 'OCEAN', 18, Wei('1000000 ether'), #magic number
    {'from' : GOD_ACCOUNT})
    
@enforce_types
def OCEAN_address() -> str:
    return _OCEAN_TOKEN.address

@enforce_types
def OCEANtoken():
    return _OCEAN_TOKEN

@enforce_types
def fundOCEANFromAbove(dst_address:str, amount_base:int):
    _OCEAN_TOKEN.transfer(dst_address, amount_base, {'from':GOD_ACCOUNT})


