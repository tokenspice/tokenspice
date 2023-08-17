import brownie
from pytest import approx

from util.base18 import toBase18 as toWei
from util.base18 import fromBase18 as fromWei
from util.constants import BROWNIE_PROJECT057, GOD_ACCOUNT
from util.tx import txdict, transferETH

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
    vesting_wallet.release(txdict(accounts[0]))
    assert vesting_wallet.released() == 0  # wallet never got funds _to_ release!


def test_ethFunding():
    # ensure each account has exactly 30 ETH
    for i in range(3):
        bal_before = fromWei(accounts[i].balance())
        if bal_before > 30.0:
            transferETH(accounts[i], GOD_ACCOUNT, toWei(bal_before - 30.0))
        elif bal_before < 30.0:
            transferETH(GOD_ACCOUNT, accounts[i], toWei(30.0 - bal_before))
        transferETH(GOD_ACCOUNT, accounts[i], toWei(1e-4))  # safety margin

    assert fromWei(accounts[0].balance()) == approx(30.0, abs=1e-3)
    assert fromWei(accounts[1].balance()) == approx(30.0, abs=1e-3)

    # set up vesting wallet (account). It vests all ETH/tokens that it receives.
    # where beneficiary is accounts[1]
    start_timestamp = chain[-1].timestamp + 5  # magic number
    duration_seconds = 30  # magic number
    wallet = BROWNIE_PROJECT057.VestingWallet057.deploy(
        accounts[1].address, start_timestamp, duration_seconds, txdict(GOD_ACCOUNT)
    )

    # send ETH to the wallet. It has a function:
    #    receive() external payable virtual {}
    # which allows it to receive ETH. It's called for plain ETH transfers,
    # ie every call with empty calldata.
    # https://medium.com/coinmonks/solidity-v0-6-0-is-here-things-you-should-know-7d4ab5bca5f1
    transferETH(accounts[0], wallet.address, "30 ether")
    assert fromWei(accounts[0].balance()) == approx(0.0, abs=1e-3)
    assert fromWei(accounts[1].balance()) == approx(30.0, abs=1e-3)  # unchanged so far
    assert wallet.vestedAmount(chain[1].timestamp) == 0
    assert wallet.released() == 0

    for i in range(1000):
        chain.mine(blocks=30, timedelta=1000)
        vested_amt = fromWei(wallet.vestedAmount(chain[-1].timestamp))
        if vested_amt >= 29.9:
            break
    assert vested_amt == approx(30.0, abs=1e-3)
    assert wallet.released() == 0
    assert fromWei(accounts[1].balance()) == approx(30.0, abs=1e-3)  # not released yet!

    # release the ETH. Anyone can call it
    wallet.release(txdict(accounts[2]))
    for i in range(1000):
        chain.mine(blocks=30, timedelta=1000)
        released_amt = fromWei(wallet.released())
        if released_amt > 29.9:
            break
    assert released_amt == approx(30.0, abs=1e-3)  # now it's released!
    assert fromWei(accounts[1].balance()) == approx(
        30.0 + 30.0, abs=1e-3
    )  # beneficiary is richer

    # put some new ETH into wallet. It's immediately vested, but not released
    transferETH(accounts[2], wallet.address, "10 ether")
    for i in range(1000):
        chain.mine(blocks=30, timedelta=1000)
        vested_amt = fromWei(wallet.vestedAmount(chain[-1].timestamp))
        if vested_amt >= 29.9:
            break
    assert vested_amt == approx(40.0, abs=1e-3)
    assert fromWei(wallet.released()) == approx(
        30.0 + 0.0, abs=1e-3
    )  # not released yet!

    # release the new ETH
    wallet.release(txdict(accounts[3]))
    for i in range(1000):
        chain.mine(blocks=30, timedelta=1000)
        released_amt = fromWei(wallet.released())
        if released_amt > 29.9:
            break
    assert released_amt == approx(30.0, abs=1e-3)  # now it's released!
    assert fromWei(accounts[1].balance()) == approx(60.0, abs=1e-3)


def test_tokenFunding():
    # accounts 0, 1, 2 should each start with 100 TOK
    token = BROWNIE_PROJECT057.Simpletoken.deploy(
        "TOK", "Test Token", 18, toWei(300.0), txdict(accounts[0])
    )
    token.transfer(accounts[1], toWei(100.0), txdict(accounts[0]))
    token.transfer(accounts[2], toWei(100.0), txdict(accounts[0]))

    assert token.balanceOf(accounts[0]) / 1e18 == approx(100.0)
    assert token.balanceOf(accounts[1]) / 1e18 == approx(100.0)
    assert token.balanceOf(accounts[2]) / 1e18 == approx(100.0)

    # account0 should be able to freely transfer TOK
    token.transfer(accounts[1], toWei(10.0), txdict(accounts[0]))
    assert token.balanceOf(accounts[0]) / 1e18 == approx(90.0)
    assert token.balanceOf(accounts[1]) / 1e18 == approx(110.0)

    # set up vesting wallet (account). It vests all ETH/tokens that it receives.
    beneficiary_address = accounts[1].address
    start_timestamp = chain[-1].timestamp + 5  # magic number
    duration_seconds = 30  # magic number
    wallet = BROWNIE_PROJECT057.VestingWallet057.deploy(
        beneficiary_address, start_timestamp, duration_seconds, txdict(accounts[0])
    )

    # send TOK to the wallet
    token.transfer(wallet.address, toWei(90.0), txdict(accounts[0]))
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
    wallet.release(token.address, txdict(accounts[2]))
    assert wallet.released(token.address) / 1e18 == approx(90.0)  # now it's released!
    assert token.balanceOf(accounts[1]) / 1e18 == approx(200.0)  # beneficiary is richer

    # put some new TOK into wallet. It's immediately vested, but not released
    token.transfer(wallet.address, toWei(10.0), txdict(accounts[2]))
    assert wallet.vestedAmount(token.address, chain[-1].timestamp) / 1e18 == approx(
        100.0
    )
    assert wallet.released(token.address) / 1e18 == approx(90.0)  # not released yet!

    # release the new TOK
    wallet.release(token.address, txdict(accounts[3]))
    assert wallet.released(token.address) / 1e18 == approx(
        100.0
    )  # now new TOK is released!
    assert token.balanceOf(accounts[1]) / 1e18 == approx(
        210.0
    )  # beneficiary got +10 ETH


def _vesting_wallet():
    # note: eth timestamps are in unix time (seconds since jan 1, 1970)
    beneficiary_address = accounts[1].address

    start_timestamp = chain[-1].timestamp + 5  # magic number

    duration_seconds = 30  # magic number

    w = BROWNIE_PROJECT057.VestingWallet057.deploy(
        beneficiary_address,
        start_timestamp,
        duration_seconds,
        txdict(accounts[0]),
    )
    return w
