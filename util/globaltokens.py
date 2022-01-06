import brownie
from enforce_typing import enforce_types

from util.constants import BROWNIE_PROJECT057, BROWNIE_PROJECT080, GOD_ACCOUNT, GOD_ADDRESS
from util.base18 import toBase18

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
        token = _OCEAN_TOKEN = BROWNIE_PROJECT057.Simpletoken.deploy(
            "OCEAN", "OCEAN", 18, toBase18(1e9), {"from": GOD_ACCOUNT}
        )
    return token


@enforce_types
def OCEAN_address() -> str:
    return OCEANtoken().address


@enforce_types
def fundOCEANFromAbove(dst_address: str, amount_base: int):
    OCEANtoken().transfer(dst_address, amount_base, {"from": GOD_ACCOUNT})

# _OCEAN_TOKEN_V4 = None
# @enforce_types
# def OCEANtokenV4():
#     global _OCEAN_TOKEN_V4  # pylint: disable=global-statement
#     try:
#         token = _OCEAN_TOKEN_V4  # may trigger failure
#         if token is not None:
#             x = token.address  # "" # pylint: disable=unused-variable
#     except brownie.exceptions.ContractNotFound:
#         token = None
#     if token is None:
#         token = _OCEAN_TOKEN_V4 = BROWNIE_PROJECT080.MockOcean.deploy(
#             GOD_ADDRESS, {"from": GOD_ACCOUNT}
#         )
#     return token


# @enforce_types
# def OCEAN_addressV4() -> str:
#     return OCEANtokenV4().address


# @enforce_types
# def fundOCEANFromAboveV4(dst_address: str, amount_base: int):
#     OCEANtokenV4().transfer(dst_address, amount_base, {"from": GOD_ACCOUNT})