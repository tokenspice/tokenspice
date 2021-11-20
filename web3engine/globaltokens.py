import brownie
from brownie import Wei
from enforce_typing import enforce_types

from util.constants import BROWNIE_PROJECT

_OCEAN_TOKEN = BROWNIE_PROJECT.Simpletoken.deploy(
    'OCEAN', 'OCEAN', 18, Wei('1000000 ether'),
    {'from' : brownie.network.accounts[0]})
    
@enforce_types
def OCEAN_address() -> str:
    return _OCEAN_TOKEN.address

@enforce_types
def OCEANtoken():
    return _OCEAN_TOKEN


