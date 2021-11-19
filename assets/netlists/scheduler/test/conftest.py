#!/usr/bin/python3

import brownie
import pytest

#https://eth-brownie.readthedocs.io/en/stable/tests-pytest-intro.html#fixture-scope
@pytest.fixture(scope="module") #scope of "module" means contract is only deployed once
def project():    
    project = brownie.project.load('assets/netlists/scheduler', name="MyProject")
    brownie.network.connect('development')
    return project

@pytest.fixture(scope="module") 
def accounts():
    return brownie.network.accounts
