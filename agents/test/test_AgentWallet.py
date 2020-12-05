import enforce
import pytest

from agents.AgentWallet import *

@enforce.runtime_validation
def testStr():
    w = AgentWallet()        
    assert "AgentWallet" in str(w)

@enforce.runtime_validation
def testInitiallyEmpty():
    w = AgentWallet()

    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0

@enforce.runtime_validation
def testInitiallyFilled():
    w = AgentWallet(USD=1.2, OCEAN=3.4)

    assert w.USD() == 1.2
    assert w.OCEAN() == 3.4

@enforce.runtime_validation
def testUSD():
    w = AgentWallet()

    w.depositUSD(13.25)
    assert w.USD() == 13.25

    w.depositUSD(1.00)
    assert w.USD() == 14.25

    w.withdrawUSD(2.10)
    assert w.USD() == 12.15

    w.depositUSD(0.0)
    w.withdrawUSD(0.0)
    assert w.USD() == 12.15

    assert w.totalUSDin() == (13.25+1.0)

    with pytest.raises(AssertionError):
        w.depositUSD(-5.0)

    with pytest.raises(AssertionError):
        w.withdrawUSD(-5.0)

    with pytest.raises(ValueError):
        w.withdrawUSD(1000.0)

@enforce.runtime_validation
def testOCEAN():
    w = AgentWallet()

    w.depositOCEAN(13.25)
    assert w.OCEAN() == 13.25

    w.depositOCEAN(1.00)
    assert w.OCEAN() == 14.25

    w.withdrawOCEAN(2.10)
    assert w.OCEAN() == 12.15

    w.depositOCEAN(0.0)
    w.withdrawOCEAN(0.0)
    assert w.OCEAN() == 12.15

    assert w.totalOCEANin() == (13.25+1.0)

    with pytest.raises(AssertionError):
        w.depositOCEAN(-5.0)

    with pytest.raises(AssertionError):
        w.withdrawOCEAN(-5.0)

    with pytest.raises(ValueError):
        w.withdrawOCEAN(1000.0)

@enforce.runtime_validation
def testFloatingPointRoundoff():
    w = AgentWallet(USD=2.4, OCEAN=2.4)
    w.withdrawUSD(2.4000000000000004) #should not get ValueError
    w.withdrawOCEAN(2.4000000000000004) #
    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0

@enforce.runtime_validation
def test_transferUSD():
    w1 = AgentWallet(USD=10.0)
    w2 = AgentWallet(USD=1.0)

    w1.transferUSD(w2, 2.0)

    assert w1.USD() == 10.0-2.0
    assert w2.USD() == 1.0+2.0

@enforce.runtime_validation
def test_transferOCEAN():
    w1 = AgentWallet(OCEAN=10.0)
    w2 = AgentWallet(OCEAN=1.0)

    w1.transferOCEAN(w2, 2.0)

    assert w1.OCEAN() == (10.0-2.0)
    assert w2.OCEAN() == (1.0+2.0)

