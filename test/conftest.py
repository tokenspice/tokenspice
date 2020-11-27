import pytest
from web3 import Web3

from web3tools import web3util

_NETWORK = "ganache"

@pytest.fixture
def btoken_address():
    return _contract_addresses()['BToken']

@pytest.fixture
def web3_object():
    return _web3_object

@pytest.fixture
def gas_price():
    return 

@pytest.fixture
def network():
    return _NETWORK

def _web3_object():
    return Web3(web3util.get_web3_provider(_NETWORK))

def _contract_addresses():
    with open(_ADDRESS_FILE) as f:
        addresses = json.load(f)
    return addresses[_NETWORK]
