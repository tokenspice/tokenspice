import brownie

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT, GOD_ACCOUNT
import sol080.contracts.oceanv4.oceanv4util
from sol080.contracts.oceanv4.oceanv4util import OCEANtoken, fundOCEANFromAbove, ROUTER

GOD_ADDRESS = GOD_ACCOUNT.address
OPF_ADDRESS = OPF_ACCOUNT.address

accounts = brownie.network.accounts

account0 = accounts[0]
address0 = account0.address

account1 = accounts[1]
address1 = account1.address


def test_exactAmountIn_fee():
    pool = _deployBPool()
    OCEAN = OCEANtoken()
    fundOCEANFromAbove(address0, toBase18(10000))
    OCEAN.approve(pool.address, toBase18(10000), {"from": account0})
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())

    assert datatoken.balanceOf(address0) == 0
    account0_DT_balance = datatoken.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    oceanMarketFeeBal = pool.publishMarketFees(OCEAN.address)

    tokenInOutMarket = [OCEAN.address, datatoken.address, address1]
    # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(1), toBase18(100), toBase18(0.001)]
    # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee=0.1%]

    tx = pool.swapExactAmountIn(
        tokenInOutMarket, amountsInOutMaxFee, {"from": account0}
    )
    assert datatoken.balanceOf(address0) > 0

    assert tx.events["SWAP_FEES"][0]["marketFeeAmount"] == toBase18(
        0.01 * 100
    )  # 0.01: mkt_swap_fee in oceanv4util.create_BPool_from_datatoken, 100: exactAmountIn
    assert tx.events["SWAP_FEES"][0]["tokenFees"] == OCEAN.address
    assert oceanMarketFeeBal + tx.events["SWAP_FEES"][0][
        "marketFeeAmount"
    ] == pool.publishMarketFees(tx.events["SWAP_FEES"][0]["tokenFees"])

    # account1 received fee
    assert OCEAN.balanceOf(address1) == toBase18(0.001 * 100)

    # account0 ocean balance decreased
    assert (
        OCEAN.balanceOf(address0) + tx.events["LOG_SWAP"][0]["tokenAmountIn"]
        == account0_Ocean_balance
    )

    # account0 DT balance increased
    assert account0_DT_balance + tx.events["LOG_SWAP"][0][
        "tokenAmountOut"
    ] == datatoken.balanceOf(address0)


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
