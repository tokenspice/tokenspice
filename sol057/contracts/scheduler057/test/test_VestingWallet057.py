import brownie
from pytest import approx

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT057, GOD_ACCOUNT

accounts = brownie.network.accounts
chain = brownie.network.chain


def test_init():
    vesting_wallet = _vesting_wallet()
    assert vesting_wallet.beneficiary() == accounts[1].address
    assert vesting_wallet.start() > chain[-1].timestamp
    assert vesting_wallet.duration() == 30
    assert vesting_wallet.released() == 0


def test_noFunding():
    vesting_wallet = _vesting_wallet()
    chain.mine(blocks=3, timedelta=10)
    assert vesting_wallet.released() == 0
    vesting_wallet.release()
    assert vesting_wallet.released() == 0  # wallet never got funds _to_ release!


def test_ethFunding():
    # ensure each account has exactly 30 ETH
    for i in range(3):
        accounts[i].transfer(GOD_ACCOUNT, accounts[i].balance())
        GOD_ACCOUNT.transfer(accounts[i], toBase18(30.0))

    # account0 should be able to freely transfer ETH
    accounts[0].transfer(accounts[1], "1 ether")
    accounts[1].transfer(accounts[0], "1 ether")
    assert accounts[0].balance() / 1e18 == approx(30.0)
    assert accounts[1].balance() / 1e18 == approx(30.0)

    # set up vesting wallet (account). It vests all ETH/tokens that it receives.
    # where beneficiary is accounts[1]
    start_timestamp = chain[-1].timestamp + 5  # magic number
    duration_seconds = 30  # magic number
    wallet = BROWNIE_PROJECT057.VestingWallet057.deploy(
        accounts[1].address, start_timestamp, duration_seconds, {"from": accounts[0]}
    )

    # send ETH to the wallet. It has a function:
    #    receive() external payable virtual {}
    # which allows it to receive ETH. It's called for plain ETH transfers,
    # ie every call with empty calldata.
    # https://medium.com/coinmonks/solidity-v0-6-0-is-here-things-you-should-know-7d4ab5bca5f1
    accounts[0].transfer(wallet.address, "30 ether")
    assert accounts[0].balance() / 1e18 == approx(0.0)
    assert accounts[1].balance() / 1e18 == approx(30.0)  # unchanged so far
    assert wallet.vestedAmount(chain[1].timestamp) == 0
    assert wallet.released() == 0

    # make enough time pass for everything to vest
    chain.mine(blocks=3, timedelta=100)
    assert wallet.vestedAmount(chain[-1].timestamp) / 1e18 == approx(30.0)
    assert wallet.released() == 0
    assert accounts[1].balance() / 1e18 == approx(30.0)  # not released yet!

    # release the ETH. Anyone can call it
    wallet.release({"from": accounts[2]})
    assert wallet.released() / 1e18 == approx(30.0)  # now it's released!
    assert accounts[1].balance() / 1e18 == approx(30.0 + 30.0)  # beneficiary is richer

    # put some new ETH into wallet. It's immediately vested, but not released
    accounts[2].transfer(wallet.address, "10 ether")
    assert wallet.vestedAmount(chain[-1].timestamp) / 1e18 == approx(30.0 + 10.0)
    assert wallet.released() / 1e18 == approx(30.0 + 0.0)  # not released yet!

    # release the new ETH
    wallet.release({"from": accounts[3]})
    assert wallet.released() / 1e18 == approx(30.0 + 10.0)  # now new ETH is released!
    assert accounts[1].balance() / 1e18 == approx(
        30.0 + 30.0 + 10.0
    )  # beneficiary got +10 ETH


def test_tokenFunding():
    # accounts 0, 1, 2 should each start with 100 TOK
    token = BROWNIE_PROJECT057.Simpletoken.deploy(
        "TOK", "Test Token", 18, toBase18(300.0), {"from": accounts[0]}
    )
    token.transfer(accounts[1], toBase18(100.0), {"from": accounts[0]})
    token.transfer(accounts[2], toBase18(100.0), {"from": accounts[0]})

    assert token.balanceOf(accounts[0]) / 1e18 == approx(100.0)
    assert token.balanceOf(accounts[1]) / 1e18 == approx(100.0)
    assert token.balanceOf(accounts[2]) / 1e18 == approx(100.0)

    # account0 should be able to freely transfer TOK
    token.transfer(accounts[1], toBase18(10.0), {"from": accounts[0]})
    assert token.balanceOf(accounts[0]) / 1e18 == approx(90.0)
    assert token.balanceOf(accounts[1]) / 1e18 == approx(110.0)

    # set up vesting wallet (account). It vests all ETH/tokens that it receives.
    beneficiary_address = accounts[1].address
    start_timestamp = chain[-1].timestamp + 5  # magic number
    duration_seconds = 30  # magic number
    wallet = BROWNIE_PROJECT057.VestingWallet057.deploy(
        beneficiary_address, start_timestamp, duration_seconds, {"from": accounts[0]}
    )

    # send TOK to the wallet
    token.transfer(wallet.address, toBase18(90.0), {"from": accounts[0]})
    assert token.balanceOf(accounts[0]) == 0
    assert token.balanceOf(accounts[1]) / 1e18 == approx(110.0)
    assert wallet.vestedAmount(token.address, chain[-1].timestamp) == 0
    assert wallet.released(token.address) == 0

    # make enough time pass for everything to vest
    chain.mine(blocks=3, timedelta=100)
    assert wallet.vestedAmount(token.address, chain[-1].timestamp) / 1e18 == approx(
        90.0
    )
    assert wallet.released(token.address) == 0
    assert token.balanceOf(accounts[1]) / 1e18 == approx(110.0)  # not released yet!

    # release the TOK. Anyone can call it
    wallet.release(token.address, {"from": accounts[2]})
    assert wallet.released(token.address) / 1e18 == approx(90.0)  # now it's released!
    assert token.balanceOf(accounts[1]) / 1e18 == approx(200.0)  # beneficiary is richer

    # put some new TOK into wallet. It's immediately vested, but not released
    token.transfer(wallet.address, toBase18(10.0), {"from": accounts[2]})
    assert wallet.vestedAmount(token.address, chain[-1].timestamp) / 1e18 == approx(
        100.0
    )
    assert wallet.released(token.address) / 1e18 == approx(90.0)  # not released yet!

    # release the new TOK
    wallet.release(token.address, {"from": accounts[3]})
    assert wallet.released(token.address) / 1e18 == approx(
        100.0
    )  # now new TOK is released!
    assert token.balanceOf(accounts[1]) / 1e18 == approx(
        210.0
    )  # beneficiary got +10 ETH


def _vesting_wallet():
    # note: eth timestamps are in unix time (seconds since jan 1, 1970)
    beneficiary_address = brownie.network.accounts[1].address

    start_timestamp = brownie.network.chain[-1].timestamp + 5  # magic number

    duration_seconds = 30  # magic number

    w = BROWNIE_PROJECT057.VestingWallet057.deploy(
        beneficiary_address,
        start_timestamp,
        duration_seconds,
        {"from": brownie.network.accounts[0]},
    )
    return w
