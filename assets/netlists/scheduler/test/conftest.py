#!/usr/bin/python3

import brownie
import pytest

BROWNIE_PROJECT = brownie.project.load(
    'assets/netlists/scheduler', name="MyProject")
brownie.network.connect('development')

@pytest.fixture
def project():
    return BROWNIE_PROJECT

@pytest.fixture
def chain():
    return brownie.network.chain

@pytest.fixture
def accounts():
    return brownie.network.accounts

@pytest.fixture
def vesting_wallet():
    #note: eth timestamps are in unix time (seconds since jan 1, 1970)
    beneficiary_address = brownie.network.accounts[1].address
    
    start_timestamp = brownie.network.chain.time() + 5 #magic number
    
    duration_seconds = 30 #magic number
    
    w = BROWNIE_PROJECT.VestingWallet.deploy(
        beneficiary_address, start_timestamp, duration_seconds,
        {'from' : brownie.network.accounts[0]})
    return w

@pytest.fixture
def token():
    t = BROWNIE_PROJECT.Datatoken.deploy(
        "TST", "Test Token", "myblob", 18, 1e21,
        {'from' : brownie.network.accounts[0]})
    return t
