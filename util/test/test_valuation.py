from util.valuation import *


def test_OCEANprice():
    assert OCEANprice(10e9, 1e9) == 10.0
