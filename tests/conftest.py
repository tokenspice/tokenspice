#!/usr/bin/python3

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


@pytest.fixture(scope="module")
def token(Datatoken, accounts):
    return accounts[0].deploy(Datatoken, "Test Datatoken", "TST", "myblob", 18, 1e21)
