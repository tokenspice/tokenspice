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
def accounts():
    return brownie.network.accounts

@pytest.fixture
def token():
    t = BROWNIE_PROJECT.Datatoken.deploy(
        "TST", "Test Token", "myblob", 18, 1e21,
        {'from' : brownie.network.accounts[0]})
    return t
