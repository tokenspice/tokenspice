import brownie

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080
from util.globaltokens import fundOCEANFromAbove
from sol080.contracts.oceanv4 import oceanv4util
from util.tx import txdict

accounts = brownie.network.accounts

account0 = accounts[0]
address0 = account0.address

account1 = accounts[1]
address1 = account1.address

def test_vesting_amount():
    pool = _deployBPool()
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDatatokenAddress())
    sideStakingAddress = pool.getController()
    sideStaking = BROWNIE_PROJECT080.SideStaking.at(sideStakingAddress)
    assert sideStaking.getvestingAmount(datatoken.address) == toBase18(1000)


def _deployBPool():
    brownie.chain.reset()
    router = oceanv4util.deployRouter(account0)
    fundOCEANFromAbove(address0, toBase18(10000))

    (dataNFT, erc721_factory) = oceanv4util.createDataNFT(
        "dataNFT", "DATANFTSYMBOL", account0, router
    )

    DT_cap = 10000
    datatoken = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSYMBOL", DT_cap, dataNFT, account0
    )

    OCEAN_init_liquidity = 2000
    DT_OCEAN_rate = 0.1
    DT_vest_amt = 1000
    DT_vest_num_blocks = 600
    pool = oceanv4util.createBPoolFromDatatoken(
        datatoken,
        erc721_factory,
        account0,
        OCEAN_init_liquidity,
        DT_OCEAN_rate,
        DT_vest_amt,
        DT_vest_num_blocks,
    )

    return pool
