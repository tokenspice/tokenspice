import logging
log = logging.getLogger('valuation')

from enforce_typing import enforce_types # type: ignore[import]
import typing

from util.strutil import asCurrency 

def firmValuationPS(annual_revenue: float, p_s_ratio: float) -> float:
    """
    Valuation by price-to-sales (P/S) ratio.
    Annual revenue = sales summed up over the last year (eg per quarter);
      it's *not* based on run rate (sales based on this quarter * 4, 
      or projected sales over the next year).
    The market decides P/S based on revenue growth. Higher growth -> higher P/S.
    Most blockchain co's have P/S of 30x-50x, as do startups like Zoom.
    """
    return annual_revenue * p_s_ratio

def firmValuationPE(annual_revenue: float, p_e_ratio: float) -> float:
    """Valuation by price-to-earnings (P/E) ratio. Earnings are
    sales minus costs.
    Some people prefer P/E over P/S as it captures profitability. However, 
    companies plowing extra money into growth will have poor P/E. Eg Amazon.
    """
    return annual_revenue * p_e_ratio

def OCEANprice(firm_valuation: float, OCEAN_supply: float) -> float:
    """Return price of OCEAN token, in USD"""
    assert OCEAN_supply > 0
    return (firm_valuation / OCEAN_supply)
