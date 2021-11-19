#!/usr/bin/python3

def test1(vesting_wallet, accounts, chain):
    assert vesting_wallet.beneficiary() == accounts[1].address
    assert vesting_wallet.start() >= (chain.time() + 5)
    assert vesting_wallet.duration() == 30
    assert vesting_wallet.released() == 0

    chain.mine(blocks=3, timedelta=10) # advance to chain.time + timedelta
    assert vesting_wallet.released() == 0
    vesting_wallet.release()
    assert vesting_wallet.released() == 0 #it should be 0, wallet never got any ETH or tokens _to_ release!

