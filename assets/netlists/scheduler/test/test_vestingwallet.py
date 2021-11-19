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

def test_ethFunding(project, accounts, chain):
    #account 0 should start with 100 ETH
    assert accounts[0].balance()/1e18 == approx(100.0)

    #account0 should be able to freely transfer ETH
    accounts[0].transfer(accounts[1], "50 ether")
    assert accounts[0].balance()/1e18 == approx(50.0)
        
    #force vesting upon account0. Now, all ETH & tokens that account0 gets
    # are subject to vesting. 
    beneficiary_address = accounts[1].address
    start_timestamp = chain.time() + 5 #magic number
    duration_seconds = 30 #magic number
    wallet = project.VestingWallet.deploy(
        beneficiary_address, start_timestamp, duration_seconds,
        {'from' : accounts[0]})

    chain.mine(blocks=3, timedelta=100) #more than enough time for all vesting
    
    #if account0 tries to transfer all its ETH, it should fail
    import pdb; pdb.set_trace()
    accounts[0].transfer(accounts[1], "50 ether") #this line should fail
    


