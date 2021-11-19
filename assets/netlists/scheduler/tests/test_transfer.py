#!/usr/bin/python3

def test_transfer(token, accounts):
    assert token.totalSupply() == 1e21
    token.transfer(accounts[1], 1e20, {'from': accounts[0]})
    assert token.balanceOf(accounts[1]) == 1e20
    assert token.balanceOf(accounts[0]) == 9e20
