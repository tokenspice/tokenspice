from brownie import Wei
from pytest import approx

def test_init(vesting_wallet, accounts, chain):
    assert vesting_wallet.beneficiary() == accounts[1].address
    assert vesting_wallet.start() >= (chain.time() + 5)
    assert vesting_wallet.duration() == 30
    assert vesting_wallet.released() == 0

def test_noFunding(vesting_wallet, accounts, chain):
    chain.mine(blocks=3, timedelta=10)
    assert vesting_wallet.released() == 0
    vesting_wallet.release()
    assert vesting_wallet.released() == 0 #wallet never got funds _to_ release!

def test_tokenFunding(project, accounts, chain):
    #account0 gets TST token
    token = project.Datatoken.deploy(
        "TST", "Test Token", "myblob", 18, Wei('1 ether'),
        {'from' : accounts[0]})
    assert token.balanceOf(accounts[0].address) == Wei('1 ether')

    #account0 can freely send TST token.
    token.transfer(accounts[1], Wei('0.1 ether'), {'from': accounts[0]})
    assert token.balanceOf(accounts[0].address) == Wei('0.9 ether')
    assert token.balanceOf(accounts[1].address) == Wei('0.1 ether')

    #let's lock things up, so that all ETH & tokens that account0 holds are
    # now subject vesting. This includes its TST tokens.
    beneficiary_address = accounts[1].address
    start_timestamp = chain.time() + 5 #magic number
    duration_seconds = 30 #magic number
    wallet = project.VestingWallet.deploy(
        beneficiary_address, start_timestamp, duration_seconds,
        {'from' : accounts[0]})

    #if account0 tries to transfer all its TST, it will fail
    #account0 can freely send TST token
    import pdb; pdb.set_trace()
    token.transfer(accounts[1], Wei('0.9 ether'), {'from': accounts[0]})
    assert token.balanceOf(accounts[0].address) > 0, "sending shoulda been blocked"


