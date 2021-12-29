from configparser import Error
from logging import error
import brownie

import sol080.contracts.oceanv4.oceanv4util
from sol080.contracts.oceanv4.oceanv4util import (
    OCEANtoken,
    fundOCEANFromAbove,
    ROUTER,
    SIDESTAKING,
)
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT, GOD_ACCOUNT, ZERO_ADDRESS

GOD_ADDRESS = GOD_ACCOUNT.address
OPF_ADDRESS = OPF_ACCOUNT.address

accounts = brownie.network.accounts

account0 = accounts[0]
address0 = account0.address

account1 = accounts[1]
address1 = account1.address


def test_fail_to_mint():
    pool = _deployBPool()
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())

    assert datatoken.isMinter(address0) == True
    try:
        datatoken.mint(address0, toBase18(1), {"from": account0})
    except brownie.exceptions.VirtualMachineError:
        pass

    assert datatoken.balanceOf(address0) == 0


def test_vesting_amount():
    pool = _deployBPool()
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())
    OCEAN = OCEANtoken()

    dataNFT_address = datatoken.getERC721Address()
    dataNFT = BROWNIE_PROJECT080.ERC721Template.at(dataNFT_address)

    sideStaking = SIDESTAKING()

    assert sideStaking.getvestingAmount(datatoken.address) == toBase18(1000)

    # TODO: https://github.com/oceanprotocol/contracts/blob/v4main_postaudit/test/flow/Vesting.test.js#L292
    # can use brownie.chain.sleep
    pubDTbalBEFORE = datatoken.balanceOf(dataNFT.address)
    for i in range(100):
        OCEAN.transfer(address1, 0, {'from':GOD_ACCOUNT})
    sideStaking.getVesting


def _deployBPool():
    brownie.chain.reset()
    router = ROUTER()
    dataNFT = sol080.contracts.oceanv4.oceanv4util.createDataNFT(
        "dataNFT", "DATANFTSYMBOL", account0, router
    )
    datatoken = sol080.contracts.oceanv4.oceanv4util.create_datatoken_from_dataNFT(
        "DT", "DTSYMBOL", 10000, dataNFT, account0
    )
    pool = sol080.contracts.oceanv4.oceanv4util.create_BPool_from_datatoken(
        datatoken, 1000, 2000, account0
    )
    return pool
