import brownie
from util.constants import BROWNIE_PROJECT057

accounts = brownie.network.accounts


def test_transfer():
    token = _deployToken()
    assert token.totalSupply() == 1e21
    token.transfer(accounts[1], 1e20, {"from": accounts[0]})
    assert token.balanceOf(accounts[1]) == 1e20
    assert token.balanceOf(accounts[0]) == 9e20


def test_approve():
    token = _deployToken()
    token.approve(accounts[1], 1e19, {"from": accounts[0]})
    assert token.allowance(accounts[0], accounts[1]) == 1e19
    assert token.allowance(accounts[0], accounts[2]) == 0

    token.approve(accounts[1], 6e18, {"from": accounts[0]})
    assert token.allowance(accounts[0], accounts[1]) == 6e18


def test_transferFrom():
    token = _deployToken()
    token.approve(accounts[1], 6e18, {"from": accounts[0]})
    token.transferFrom(accounts[0], accounts[2], 5e18, {"from": accounts[1]})

    assert token.balanceOf(accounts[2]) == 5e18
    assert token.balanceOf(accounts[1]) == 0
    assert token.balanceOf(accounts[0]) == 9.95e20
    assert token.allowance(accounts[0], accounts[1]) == 1e18


def _deployToken():
    return BROWNIE_PROJECT057.Simpletoken.deploy(
        "TST", "Test Token", 18, 1e21, {"from": accounts[0]}
    )
