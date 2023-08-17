import brownie

from sol080.contracts.oceanv4 import oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080
from util.globaltokens import fundOCEANFromAbove
from util.tx import txdict

accounts = brownie.network.accounts

account0 = accounts[0]
address0 = account0.address

account1 = accounts[1]
address1 = account1.address


def test_exactAmountIn_fee():
    pool = _deployBPool()
    OCEAN = oceanv4util.OCEANtoken()
    fundOCEANFromAbove(address0, toBase18(10000))
    OCEAN.approve(pool.address, toBase18(10000), txdict(account0))
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDatatokenAddress())

    assert datatoken.balanceOf(address0) == 0
    account0_DT_balance = datatoken.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)

    tokenInOutMarket = [OCEAN.address, datatoken.address, address1]
    # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(1), toBase18(100), toBase18(0.001)]
    # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee=0.1%]

    tx = pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, txdict(account0))
    assert datatoken.balanceOf(address0) > 0

    assert tx.events["SWAP_FEES"][0]["marketFeeAmount"] == toBase18(
        0.01 * 100
    )  # 0.01: mkt_swap_fee in oceanv4util.create_BPool_from_datatoken, 100: exactAmountIn
    assert tx.events["SWAP_FEES"][0]["tokenFeeAddress"] == OCEAN.address

    # account1 received fee
    assert OCEAN.balanceOf(address1) == toBase18(0.001 * 100)

    # account0 ocean balance decreased
    assert (
        OCEAN.balanceOf(address0) + tx.events["LOG_SWAP"][0]["tokenAmountIn"]
    ) == account0_Ocean_balance

    # account0 DT balance increased
    assert account0_DT_balance + tx.events["LOG_SWAP"][0][
        "tokenAmountOut"
    ] == datatoken.balanceOf(address0)


def _deployBPool():
    brownie.chain.reset()
    router = oceanv4util.deployRouter(account0)
    fundOCEANFromAbove(address0, toBase18(100000))

    (dataNFT, erc721_factory) = oceanv4util.createDataNFT(
        "dataNFT", "DATANFTSYMBOL", account0, router
    )

    DT_cap = 10000
    datatoken = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSYMBOL", DT_cap, dataNFT, account0
    )

    OCEAN_init_liquidity = 80000
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
