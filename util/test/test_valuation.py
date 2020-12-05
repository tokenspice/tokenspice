import numpy

from util.valuation import *

def test_ps():
    assert firmValuationPS(1e3, 30.0) == 30e3

def test_pe():
    assert firmValuationPE(1e3, 20.0) == 20e3

def test_OCEANprice():
    assert OCEANprice(10e9, 1e9) == 10.0

