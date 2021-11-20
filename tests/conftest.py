#!/usr/bin/python3

import pytest

@pytest.fixture(scope="module")
def token(Simpletoken, accounts):
    return accounts[0].deploy(Simpletoken, "Test Simpletoken", "TST", 18, 1e21)
