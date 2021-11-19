#!/usr/bin/python3

import brownie

def test_transfer(project):
    accounts = brownie.network.accounts
    token = project.Datatoken.deploy("TST", "Test Token", "blob", 18, 1e21,
                                     {'from' : accounts[0]})
    assert token.totalSupply() == 1e21
    token.transfer(accounts[1], 1e20, {'from': accounts[0]})
    assert token.balanceOf(accounts[1]) == 1e20
    assert token.balanceOf(accounts[0]) == 9e20
