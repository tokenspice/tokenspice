import brownie

def test_balance(token, accounts):
    assert token.balanceOf(accounts[0]) == 1e21

def test_approval(token, accounts):
    '''Set approval'''
    token.approve(accounts[1], 1e19, {'from': accounts[0]})
    assert token.allowance(accounts[0], accounts[1]) == 1e19
    assert token.allowance(accounts[0], accounts[2]) == 0

    token.approve(accounts[1], 6e18, {'from': accounts[0]})
    assert token.allowance(accounts[0], accounts[1]) == 6e18


def test_transferFrom(token, accounts):
    '''Transfer tokens with transferFrom'''
    token.approve(accounts[1], 6e18, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], 5e18, {'from': accounts[1]})

    assert token.balanceOf(accounts[2]) == 5e18
    assert token.balanceOf(accounts[1]) == 0
    assert token.balanceOf(accounts[0]) == 9.95e20
    assert token.allowance(accounts[0], accounts[1]) == 1e18
