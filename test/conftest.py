import pytest
from web3 import Web3

from web3tools import web3util

@pytest.fixture
def btoken_address():
    return _contract_addresses()['BToken']

@pytest.fixture
def web3_object():
    return _web3_object
