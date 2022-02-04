import brownie
from pytest import approx

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT057, BROWNIE_PROJECT080, GOD_ACCOUNT

accounts = brownie.network.accounts
account0, account1, account2, account3 = \
    accounts[0], accounts[1], accounts[2], accounts[3]
address0, address1, address2 = \
    account0.address, account1.address, account2.address
chain = brownie.network.chain

#This code has evolved from sol057:
# -DONE: time is # blocks not unix time
# -TODO: fix 500M issue, exponential vesting, ratchet


def test_basic():
    n_blocks = len(chain)
    beneficiary = address1
    start_block = n_blocks + 1
    num_blocks_duration = 4

    #constructor
    vesting_wallet = BROWNIE_PROJECT080.VestingWallet080.deploy(
        beneficiary, toBase18(start_block), toBase18(num_blocks_duration),
        {"from": account0}
    )

    assert vesting_wallet.beneficiary() == beneficiary
    start_block_measured = int(vesting_wallet.startBlock()/1e18)
    assert start_block_measured in [start_block-1, start_block, start_block+1]
    assert int(vesting_wallet.numBlocksDuration()/1e18) == 4
    assert vesting_wallet.released() == 0

    #time passes
    chain.mine(blocks=15, timedelta=1)
    assert vesting_wallet.released() == 0 #haven't released anything

    #call release
    vesting_wallet.release()
    assert vesting_wallet.released() == 0  # wallet never got funds to release!


def test_ethFunding():
    # ensure each account has exactly 30 ETH
    for account in [account0, account1, account2]:
        account.transfer(GOD_ACCOUNT, account.balance())
        GOD_ACCOUNT.transfer(account, toBase18(30.0))

    # account0 should be able to freely transfer ETH
    account0.transfer(account1, toBase18(1.0))
    account1.transfer(account0, toBase18(1.0))
    assert account0.balance()/1e18 == approx(30.0)
    assert account1.balance()/1e18 == approx(30.0)

    # set up vesting wallet (account). It vests all ETH/tokens that it receives.
    # where beneficiary is account1
    start_block = 4
    num_blocks_duration = 5
    wallet = BROWNIE_PROJECT080.VestingWallet080.deploy(
        address1, toBase18(start_block), toBase18(num_blocks_duration),
        {"from": account0}
    )
    assert wallet.balance() == 0

    # send ETH to the wallet. It has a function:
    #    receive() external payable virtual {}
    # which allows it to receive ETH. It's called for plain ETH transfers,
    # ie every call with empty calldata.
    # https://medium.com/coinmonks/solidity-v0-6-0-is-here-things-you-should-know-7d4ab5bca5f1
    assert account0.transfer(wallet.address, toBase18(30.0))
    assert wallet.balance()/1e18 == approx(30.0)
    assert account0.balance()/1e18 == approx(0.0)
    assert account1.balance()/1e18 == approx(30.0) # unchanged so far
    assert wallet.vestedAmount(toBase18(4)) == 0
    assert wallet.vestedAmount(toBase18(10)) > 0.0
    assert wallet.released() == 0

    # make enough time pass for everything to vest
    chain.mine(blocks=14, timedelta=100)

    assert wallet.vestedAmount(toBase18(1)) == 0
    assert wallet.vestedAmount(toBase18(2)) == 0
    assert wallet.vestedAmount(toBase18(3)) == 0
    assert wallet.vestedAmount(toBase18(4)) == 0
    assert wallet.vestedAmount(toBase18(5))/1e18 == approx(6.0)
    assert wallet.vestedAmount(toBase18(6))/1e18 == approx(12.0)
    assert wallet.vestedAmount(toBase18(7))/1e18 == approx(18.0)
    assert wallet.vestedAmount(toBase18(8))/1e18 == approx(24.0)
    assert wallet.vestedAmount(toBase18(9))/1e18 == approx(30.0)
    assert wallet.vestedAmount(toBase18(10))/1e18 == approx(30.0)
    assert wallet.vestedAmount(toBase18(11))/1e18 == approx(30.0)

    assert wallet.released() == 0
    assert account1.balance()/1e18 == approx(30.0) # not released yet!

    # release the ETH. Anyone can call it
    wallet.release({"from": account2})
    assert wallet.released()/1e18 == approx(30.0) # now it's released!
    assert account1.balance()/1e18 == approx(30.0 + 30.0) # beneficiary richer

    # put some new ETH into wallet. It's immediately vested, but not released
    account2.transfer(wallet.address, toBase18(10.0))
    assert wallet.vestedAmount(toBase18(len(chain))) / 1e18 == approx(30.0+10.0)
    assert wallet.released()/1e18 == approx(30.0+0.0)  # not released yet!

    # release the new ETH
    wallet.release({"from": account3})
    assert wallet.released()/1e18 == approx(30.0+10.0) #new ETH is released!
    assert account1.balance()/1e18 == approx(30.0+30.0+10.0) #+10 eth to ben


def test_tokenFunding():
    # accounts 0, 1, 2 should each start with 100 TOK
    token = BROWNIE_PROJECT057.Simpletoken.deploy(
        "TOK", "Test Token", 18, toBase18(300.0), {"from": account0}
    )
    token.transfer(account1, toBase18(100.0), {"from": account0})
    token.transfer(account2, toBase18(100.0), {"from": account0})
    taddress = token.address

    assert token.balanceOf(account0)/1e18 == approx(100.0)
    assert token.balanceOf(account1)/1e18 == approx(100.0)
    assert token.balanceOf(account2)/1e18 == approx(100.0)

    # account0 should be able to freely transfer TOK
    token.transfer(account1, toBase18(10.0), {"from": account0})
    assert token.balanceOf(account0)/1e18 == approx(90.0)
    assert token.balanceOf(account1)/1e18 == approx(110.0)

    # set up vesting wallet (account). It vests all ETH/tokens that it receives.
    start_block = 4
    num_blocks_duration = 5
    wallet = BROWNIE_PROJECT080.VestingWallet080.deploy(
        address1, toBase18(start_block), toBase18(num_blocks_duration),
        {"from": account0}
    )
    assert token.balanceOf(wallet) == 0

    # send TOK to the wallet
    token.transfer(wallet.address, toBase18(30.0), {"from": account0})
    assert token.balanceOf(wallet)/1e18 == approx(30.0)
    assert token.balanceOf(account0)/1e18 == approx(60.0)
    assert token.balanceOf(account1)/1e18 == approx(110.0)
    assert wallet.vestedAmount(taddress, toBase18(4)) == 0
    assert wallet.vestedAmount(taddress, toBase18(10)) > 0.0
    assert wallet.released(taddress) == 0

    # make enough time pass for everything to vest
    chain.mine(blocks=14, timedelta=100)

    assert wallet.vestedAmount(taddress, toBase18(1)) == 0
    assert wallet.vestedAmount(taddress, toBase18(2)) == 0
    assert wallet.vestedAmount(taddress, toBase18(3)) == 0
    assert wallet.vestedAmount(taddress, toBase18(4)) == 0
    assert wallet.vestedAmount(taddress, toBase18(5))/1e18 == approx(6.0)
    assert wallet.vestedAmount(taddress, toBase18(6))/1e18 == approx(12.0)
    assert wallet.vestedAmount(taddress, toBase18(7))/1e18 == approx(18.0)
    assert wallet.vestedAmount(taddress, toBase18(8))/1e18 == approx(24.0)
    assert wallet.vestedAmount(taddress, toBase18(9))/1e18 == approx(30.0)
    assert wallet.vestedAmount(taddress, toBase18(10))/1e18 == approx(30.0)
    assert wallet.vestedAmount(taddress, toBase18(11))/1e18 == approx(30.0)

    assert wallet.released(taddress) == 0
    assert token.balanceOf(account1)/1e18 == approx(110.0) #not released yet

    # release the TOK. Anyone can call it
    wallet.release(taddress, {"from": account2})
    assert wallet.released(taddress)/1e18 == approx(30.0) #released!
    assert token.balanceOf(account1)/1e18 == approx(110.0+30.0) #beneficiary richer

    # put some new TOK into wallet. It's immediately vested, but not released
    token.transfer(wallet.address, toBase18(10.0), {"from": account2})
    assert wallet.vestedAmount(taddress,toBase18(11))/1e18 == approx(30.0+10.0)
    assert wallet.released(taddress)/1e18 == approx(30.0) #not released yet

    # release the new TOK
    wallet.release(taddress, {"from": account3})
    assert wallet.released(taddress)/1e18 == approx(30.0+10.0) #TOK released!
    assert token.balanceOf(account1)/1e18 == approx(110+30+10.0) #beneficiary richer
