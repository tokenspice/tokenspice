#!/usr/bin/python3

def test1(vesting_wallet, accounts, chain):
    assert vesting_wallet.beneficiary() == accounts[1].address

    recent_block = chain[-1]
    assert vesting_wallet.start() >= (recent_block.timestamp + 5)

    assert vesting_wallet.duration() == 30

    assert vesting_wallet.released() >= 0
