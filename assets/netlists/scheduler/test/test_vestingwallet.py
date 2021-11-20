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
    accounts[0].transfer(accounts[1], "10 ether")
    assert accounts[0].balance()/1e18 == approx(90.0)
    assert accounts[1].balance()/1e18 == approx(110.0)
        
    #force vesting upon account0. Now, all ETH & tokens that account0 gets
    # are subject to vesting. 
    beneficiary_address = accounts[1].address
    start_timestamp = chain.time() + 5 #magic number
    duration_seconds = 30 #magic number
    wallet = project.VestingWallet.deploy(
        beneficiary_address, start_timestamp, duration_seconds,
        {'from' : accounts[0]})

    #send money to the wallet. It has a function:
    #    receive() external payable virtual {}
    #which allows it to receive ETH. It's called for plain ETH transfers,
    #ie every call with empty calldata.
    #https://medium.com/coinmonks/solidity-v0-6-0-is-here-things-you-should-know-7d4ab5bca5f1
    accounts[0].transfer(wallet.address, "90 ether")
    assert accounts[0].balance() == 0
    assert accounts[1].balance()/1e18 == approx(110.0)
    assert wallet.vestedAmount(chain.time()) == 0
    assert wallet.released() == 0

    #make enough time pass for everything to vest
    chain.mine(blocks=3, timedelta=100)
    assert wallet.vestedAmount(chain.time())/1e18 == approx(90.0)
    assert wallet.released() == 0
    assert accounts[1].balance()/1e18 == approx(110.0) #not released yet!

    #release the ETH. Anyone can call it
    wallet.release({'from': accounts[2]})
    assert wallet.released()/1e18 == approx(90.0) #now it's released!
    assert accounts[1].balance()/1e18 == approx(200.0) #beneficiary is richer

    #put some new ETH in. It's already immediately vested, but not released
    accounts[2].transfer(wallet.address, "10 ether")
    assert wallet.vestedAmount(chain.time())/1e18 == approx(100.0)
    assert wallet.released()/1e18 == approx(90.0) #not released yet!

    #release the new ETH
    wallet.release({'from': accounts[3]})
    assert wallet.released()/1e18 == approx(100.0) #now new ETH is released!
    assert accounts[1].balance()/1e18 == approx(210.0) #beneficiary got +10 ETH
    
    
    
    


