import brownie
import pytest

from contracts.oceanv3.oceanv3util import newDatatoken

@pytest.fixture
def T1():
    return _dts()[0]

@pytest.fixture
def T2():
    return _dts()[1]

def _dts():
    cap = brownie.Wei('1000 ether')
    account0 = brownie.network.accounts[0]
    return [newDatatoken('blob', f'datatoken{i+1}', f'DT{i+1}', cap, account0)
            for i in range(2)]
