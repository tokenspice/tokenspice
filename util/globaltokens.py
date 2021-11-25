import brownie
from enforce_typing import enforce_types

from util.constants import BROWNIE_PROJECT, GOD_ACCOUNT
from util.base18 import toBase18

_OCEAN_TOKEN = None
    
@enforce_types
def OCEANtoken():
    global _OCEAN_TOKEN
    try:
        token = _OCEAN_TOKEN             #may trigger failure
        x = token.balanceOf(GOD_ACCOUNT) #""
    except brownie.exceptions.ContractNotFound:
        token = None
    if token is None:
        token = _OCEAN_TOKEN = GOD_ACCOUNT.deploy(
            BROWNIE_PROJECT.Simpletoken, 'OCEAN', 'OCEAN', 18, toBase18(1e9))
    return token

@enforce_types
def OCEAN_address() -> str:
    return OCEANtoken().address

@enforce_types
def fundOCEANFromAbove(dst_address:str, amount_base:int):
    OCEANtoken().transfer(dst_address, amount_base, {'from':GOD_ACCOUNT})
