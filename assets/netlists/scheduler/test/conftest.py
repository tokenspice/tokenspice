#!/usr/bin/python3

import brownie
import pytest

#https://eth-brownie.readthedocs.io/en/stable/tests-pytest-intro.html#fixture-scope
@pytest.fixture(scope="module") #this scope means contract is only deployed once
def accounts():
    return brownie.network.accounts

@pytest.fixture(scope="module") 
def token():
    my_project = _load_project()
    token = my_project.Datatoken.deploy(
        "TST", "Test Token", "myblob", 18, 1e21,
        {'from' : brownie.network.accounts[0]})
    return token

def _load_project():
    my_project = brownie.project.load(
        'assets/netlists/scheduler', name="MyProject")
    brownie.network.connect('development')
    return my_project
