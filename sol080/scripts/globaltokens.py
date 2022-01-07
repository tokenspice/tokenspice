import brownie
from enforce_typing import enforce_types

from .constants import GOD_ACCOUNT, GOD_ADDRESS
from .base18 import toBase18

BROWNIE_PROJECT080 = brownie.project.Project080


_OCEAN_TOKEN = None


@enforce_types
def OCEANtoken():
    global _OCEAN_TOKEN  # pylint: disable=global-statement
    try:
        token = _OCEAN_TOKEN  # may trigger failure
        if token is not None:
            x = token.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        token = None
    if token is None:
        token = _OCEAN_TOKEN = BROWNIE_PROJECT080.MockOcean.deploy(
            GOD_ADDRESS, {"from": GOD_ACCOUNT}
        )
    return token


@enforce_types
def OCEAN_address() -> str:
    return OCEANtoken().address


@enforce_types
def fundOCEANFromAbove(dst_address: str, amount_base: int):
    OCEANtoken().transfer(dst_address, amount_base, {"from": GOD_ACCOUNT})
