import brownie
import pytest

from sol057.contracts.oceanv3.oceanv3util import newDatatoken
from util.base18 import toBase18

account0 = brownie.network.accounts[0]


@pytest.fixture
def T1():
    return _dts()[0]


@pytest.fixture
def T2():
    return _dts()[1]


def _dts():
    """Create datatokens, and mint into account0"""
    cap = toBase18(1e3)
    dts = []
    for i in range(2):
        dt = newDatatoken("blob", f"datatoken{i+1}", f"DT{i+1}", cap, account0)
        dt.mint(account0, toBase18(1e3), {"from": account0})
        dts.append(dt)
    return dts
