import brownie

from sol080.contracts.oceanv4 import oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT, GOD_ACCOUNT, ZERO_ADDRESS
from util.globaltokens import fundOCEANFromAbove

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
    sideStakingAddress = pool.getController()
    sideStaking = BROWNIE_PROJECT080.SideStaking.at(sideStakingAddress)
    assert sideStaking.getvestingAmount(datatoken.address) == toBase18(1000)

    # TODO: https://github.com/oceanprotocol/contracts/blob/v4main_postaudit/test/flow/Vesting.test.js#L292
    # can use brownie.chain.sleep


def _deployBPool():
    brownie.chain.reset()
    router = oceanv4util.deployRouter(account0)
    fundOCEANFromAbove(address0, toBase18(10000))
    createdDataNFT = oceanv4util.createDataNFT(
        "dataNFT", "DATANFTSYMBOL", account0, router
    )
    dataNFT = createdDataNFT[0]
    datatoken = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSYMBOL", 10000, dataNFT, account0
    )
    erc721_factory = createdDataNFT[1]
    pool = oceanv4util.createBPoolFromDatatoken(
        datatoken, 1000, 2000, account0, erc721_factory
    )
    return pool
