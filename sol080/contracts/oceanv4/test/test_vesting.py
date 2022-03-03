import brownie

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080
from sol080.contracts.oceanv4 import oceanv4util

accounts = brownie.network.accounts

account0 = accounts[0]
address0 = account0.address

account1 = accounts[1]
address1 = account1.address


def test_fail_to_mint():
    pool = _deployBPool()
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())

    assert datatoken.isMinter(address0)

    try:
        datatoken.mint(address0, toBase18(1), {"from": account0})
    except brownie.exceptions.VirtualMachineError:
        pass

    assert datatoken.balanceOf(address0) == 0


def test_vesting_amount():
    pool = _deployBPool()
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())
    sideStakingAddress = pool.getController()
    sideStaking = BROWNIE_PROJECT080.SideStaking.at(sideStakingAddress)
    assert sideStaking.getvestingAmount(datatoken.address) == toBase18(1000)


def _deployBPool():
    brownie.chain.reset()
    router = oceanv4util.deployRouter(account0)
    oceanv4util.fundOCEANFromAbove(address0, toBase18(10000))
    (dataNFT, erc721_factory) = oceanv4util.createDataNFT(
        "dataNFT", "DATANFTSYMBOL", account0, router)
    datatoken = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSYMBOL", 10000, dataNFT, account0)
    pool = oceanv4util.createBPoolFromDatatoken(
        datatoken, 1000, 2000, account0, erc721_factory)
    return pool
