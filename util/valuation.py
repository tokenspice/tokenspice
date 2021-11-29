import logging

log = logging.getLogger("valuation")

from enforce_typing import enforce_types
import typing


def OCEANprice(firm_valuation: float, OCEAN_supply: float) -> float:
    """Return price of OCEAN token, in USD"""
    assert OCEAN_supply > 0
    return firm_valuation / OCEAN_supply
