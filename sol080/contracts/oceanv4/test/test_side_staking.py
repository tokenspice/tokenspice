import brownie

from util.base18 import toBase18, fromBase18
from util.constants import BROWNIE_PROJECT080
from util.globaltokens import fundOCEANFromAbove, OCEANtoken
from sol080.contracts.oceanv4 import oceanv4util

accounts = brownie.network.accounts

account0 = accounts[0]
address0 = account0.address

account1 = accounts[1]
address1 = account1.address


def test_sideStaking_properties():
    brownie.chain.reset()
    init_block_height = brownie.chain.height
    OCEAN = OCEANtoken()

    OCEAN_base_funding = 10000
    do_extra_funding = False
    OCEAN_extra_funding = 10000
    OCEAN_init_liquidity = 2000
    
    DT_cap = 10000
    DT_vest_amt = 1000
    DT_vest_num_blocks = 600
    (DT, pool, ss_bot) = _deployBPool(
        OCEAN_base_funding, do_extra_funding, OCEAN_extra_funding,
        OCEAN_init_liquidity,
        DT_cap, DT_vest_amt, DT_vest_num_blocks)

    assert ss_bot.getPoolAddress(DT.address) == pool.address
    assert ss_bot.getBaseTokenAddress(DT.address) == pool.getBaseTokenAddress()
    assert ss_bot.getBaseTokenAddress(DT.address) == OCEAN.address
    assert ss_bot.getPublisherAddress(DT.address) == address0

    ss_bot_DT_balance = fromBase18(DT.balanceOf(ss_bot.address))
    assert ss_bot_DT_balance == 9800 #Trang had 9800, why?

    ss_bot_amt_vested = fromBase18(ss_bot.getvestingAmountSoFar(DT.address))
    assert ss_bot_amt_vested == 0

    # DT circ_supply = (DT cap) - (ss_bot DT balance) - (ss_bot amt vested)
    #                = 10000    - __??__              - 0
    #                = __??__
    expected_DT_circ_supply = DT_cap - ss_bot_DT_balance - ss_bot_amt_vested #Trang had 1200, why?
    DT_circ_supply = fromBase18(ss_bot.getDatatokenCirculatingSupply(DT.address))
    assert DT_circ_supply == expected_DT_circ_supply

    assert ss_bot.getBaseTokenBalance(DT.address) == 0
    assert fromBase18(ss_bot.getDatatokenBalance(DT.address)) == 8800

    assert ss_bot.getDatatokenCurrentCirculatingSupply(DT.address) == \
        toBase18(2000 * 0.1)  # ss_rate*ss_OCEAN_init_liquidity

    assert ss_bot.getvestingAmountSoFar(DT.address) == 0
    assert ss_bot.getvestingAmount(DT.address) == toBase18(1000)

    assert ss_bot.getvestingLastBlock(DT.address) == init_block_height
    assert ss_bot.getvestingEndBlock(DT.address) == (init_block_height+2500000)


def test_swapExactAmountIn():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    tokenInOutMarket = [OCEAN.address, DT.address, address0]
    # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(1), toBase18(100), 0]
    # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee]

    assert DT.balanceOf(address0) == 0
    pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, {"from": account0})
    assert DT.balanceOf(address0) > 0

    # swaps some DT back to Ocean swapExactAmountIn
    dt_balance_before = DT.balanceOf(address0)
    ocean_balance_before = OCEAN.balanceOf(address0)

    DT.approve(pool.address, toBase18(1000), {"from": account0})
    tokenInOutMarket = [DT.address, OCEAN.address, address0]
    # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(1), toBase18(1), toBase18(100), 0]
    # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee]
    pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, {"from": account0})

    assert DT.balanceOf(address0) < dt_balance_before
    assert OCEAN.balanceOf(address0) > ocean_balance_before


def test_swapExactAmountOut():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    tokenInOutMarket = [
        OCEAN.address,
        DT.address,
        address0,
    ]  # // [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(1000), toBase18(10), toBase18(1000), 0]

    assert DT.balanceOf(address0) == 0
    pool.swapExactAmountOut(tokenInOutMarket, amountsInOutMaxFee, {"from": account0})
    assert DT.balanceOf(address0) > 0


def test_joinPool_addTokens():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=False)

    tokenInOutMarket = [OCEAN.address, DT.address, address0]
    # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(1), toBase18(100), 0]
    # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee]

    assert DT.balanceOf(address0) == 0
    pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, {"from": account0})

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    BPTAmountOut = toBase18(0.01)
    maxAmountsIn = [toBase18(50), toBase18(50)]
    DT.approve(pool.address, toBase18(50), {"from": account0})
    tx = pool.joinPool(BPTAmountOut, maxAmountsIn, {"from": account0})

    assert tx.events["LOG_JOIN"][0]["tokenIn"] == DT.address
    assert tx.events["LOG_JOIN"][1]["tokenIn"] == OCEAN.address

    assert (
        tx.events["LOG_JOIN"][0]["tokenAmountIn"] + DT.balanceOf(address0)
        == account0_DT_balance
    )
    assert (
        tx.events["LOG_JOIN"][1]["tokenAmountIn"] + OCEAN.balanceOf(address0)
        == account0_Ocean_balance
    )
    assert account0_BPT_balance + BPTAmountOut == pool.balanceOf(address0)

    # check ssContract BPT and DT balance didn't change
    assert ssContractBPTbalance == pool.balanceOf(ss_bot.address)
    assert ssContractDTbalance == DT.balanceOf(ss_bot.address)


def test_joinswapExternAmountIn_addOCEAN():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=Fales)

    account0_DT_balance = DT.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    oceanAmountIn = toBase18(100)
    minBPTOut = toBase18(0.1)

    tx = pool.joinswapExternAmountIn(
        OCEAN.address, oceanAmountIn, minBPTOut, {"from": account0}
    )

    assert tx.events["LOG_JOIN"][0]["tokenIn"] == OCEAN.address
    assert tx.events["LOG_JOIN"][0]["tokenAmountIn"] == oceanAmountIn

    assert tx.events["LOG_JOIN"][1]["tokenIn"] == DT.address
    ss_botAmountIn = ssContractDTbalance - DT.balanceOf(ss_bot.address)
    assert ss_botAmountIn == tx.events["LOG_JOIN"][1]["tokenAmountIn"]

    # we check ssContract actually moved DT and got back BPT
    assert (
        DT.balanceOf(ss_bot.address)
        == ssContractDTbalance - tx.events["LOG_JOIN"][1]["tokenAmountIn"]
    )
    assert (
        pool.balanceOf(ss_bot.address)
        == ssContractBPTbalance + tx.events["LOG_BPT"]["bptAmount"]
    )

    # no datatoken where taken from account0
    assert account0_DT_balance == DT.balanceOf(address0)


def test_joinswapPoolAmountOut_addOCEAN():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    BPTAmountOut = toBase18(0.1)
    maxOceanIn = toBase18(100)

    tx = pool.joinswapPoolAmountOut(
        OCEAN.address, BPTAmountOut, maxOceanIn, {"from": account0}
    )

    assert tx.events["LOG_JOIN"][0]["tokenIn"] == OCEAN.address
    assert tx.events["LOG_JOIN"][1]["tokenIn"] == DT.address

    # Check balance
    assert tx.events["LOG_JOIN"][0]["tokenAmountIn"] + OCEAN.balanceOf(address0) \
        == account0_Ocean_balance
    assert BPTAmountOut + account0_BPT_balance == pool.balanceOf(address0)

    # we check ssContract received the same amount of BPT
    assert ssContractBPTbalance + BPTAmountOut == pool.balanceOf(ss_bot.address)

    #  DT balance lowered in the ssContract
    ssContractDTbalance - tx.events["LOG_JOIN"][1]["tokenAmountIn"] == \
        DT.balanceOf(ss_bot.address)

    # no datatoken where taken from account0
    assert account0_DT_balance == DT.balanceOf(address0)


def test_exitPool_receiveTokens():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    BPTAmountIn = toBase18(0.5)
    minAmountOut = [toBase18(1), toBase18(1)]
    tx = pool.exitPool(BPTAmountIn, minAmountOut, {"from": account0})

    assert tx.events["LOG_EXIT"][0]["tokenOut"] == DT.address
    assert tx.events["LOG_EXIT"][1]["tokenOut"] == OCEAN.address

    assert tx.events["LOG_EXIT"][0][
        "tokenAmountOut"
    ] + account0_DT_balance == DT.balanceOf(address0)
    assert tx.events["LOG_EXIT"][1][
        "tokenAmountOut"
    ] + account0_Ocean_balance == OCEAN.balanceOf(address0)
    assert pool.balanceOf(address0) + BPTAmountIn == account0_BPT_balance

    # check the ssContract BPT and DT balance didn"t change
    assert ssContractBPTbalance == pool.balanceOf(ss_bot.address)
    assert ssContractDTbalance == DT.balanceOf(ss_bot.address)


def test_exitswapPoolAmountIn_receiveOcean():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    BPTAmountIn = toBase18(0.5)
    minOceanOut = toBase18(0.5)

    tx = pool.exitswapPoolAmountIn(
        OCEAN.address, BPTAmountIn, minOceanOut, {"from": account0}
    )

    assert DT.balanceOf(address0) == account0_DT_balance

    # check event argument
    assert tx.events["LOG_EXIT"][0]["caller"] == address0
    assert tx.events["LOG_EXIT"][0]["tokenOut"] == OCEAN.address
    assert tx.events["LOG_EXIT"][1]["tokenOut"] == DT.address

    # check user ocean balance
    assert tx.events["LOG_EXIT"][0][
        "tokenAmountOut"
    ] + account0_Ocean_balance == OCEAN.balanceOf(address0)

    # check BPT balance
    assert account0_BPT_balance == pool.balanceOf(address0) + BPTAmountIn

    # check the ssContract BPT balance
    assert ssContractBPTbalance == pool.balanceOf(ss_bot.address) + BPTAmountIn

    # ssContract got back his dt when redeeeming BPT
    assert ssContractDTbalance + tx.events["LOG_EXIT"][1][
        "tokenAmountOut"
    ] == DT.balanceOf(ss_bot.address)


def test_exitswapPoolAmountIn_receiveDT():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    BPTAmountIn = toBase18(0.5)
    minDTOut = toBase18(0.5)

    tx = pool.exitswapPoolAmountIn(
        DT.address, BPTAmountIn, minDTOut, {"from": account0}
    )

    assert OCEAN.balanceOf(address0) == account0_Ocean_balance
    assert (
        pool.balanceOf(address0)
        == account0_BPT_balance - tx.events["LOG_BPT"][0]["bptAmount"]
    )

    # check exit event argument
    assert tx.events["LOG_EXIT"][0]["caller"] == address0
    assert tx.events["LOG_EXIT"][0]["tokenOut"] == DT.address

    # check DT balance before and after
    assert tx.events["LOG_EXIT"][0][
        "tokenAmountOut"
    ] + account0_DT_balance == DT.balanceOf(address0)

    # chekc BPT
    assert account0_BPT_balance == pool.balanceOf(address0) + BPTAmountIn

    # ssContract BPT and DT balance didn't change
    assert ssContractBPTbalance == pool.balanceOf(ss_bot.address)
    assert ssContractDTbalance == DT.balanceOf(ss_bot.address)


def test_exitswapExternAmountOut_receiveOcean():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    maxBPTIn = toBase18(0.5)
    exactOceanOut = toBase18(1)

    tx = pool.exitswapExternAmountOut(
        OCEAN.address, maxBPTIn, exactOceanOut, {"from": account0}
    )

    assert DT.balanceOf(address0) == account0_DT_balance
    assert (
        pool.balanceOf(address0)
        == account0_BPT_balance - tx.events["LOG_BPT"][0]["bptAmount"]
    )

    assert tx.events["LOG_EXIT"][0][
        "tokenAmountOut"
    ] + account0_Ocean_balance == OCEAN.balanceOf(address0)
    assert ssContractBPTbalance - tx.events["LOG_BPT"][0][
        "bptAmount"
    ] == pool.balanceOf(ss_bot.address)
    assert ssContractDTbalance + tx.events["LOG_EXIT"][1][
        "tokenAmountOut"
    ] == DT.balanceOf(ss_bot.address)


def test_exitswapExternAmountOut_receiveDT():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ss_bot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_Ocean_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ss_bot.address)
    ssContractBPTbalance = pool.balanceOf(ss_bot.address)

    maxBPTIn = toBase18(0.5)
    exacDTOut = toBase18(1)

    tx = pool.exitswapExternAmountOut(
        DT.address, maxBPTIn, exacDTOut, {"from": account0}
    )

    assert OCEAN.balanceOf(address0) == account0_Ocean_balance
    assert (
        pool.balanceOf(address0)
        == account0_BPT_balance - tx.events["LOG_BPT"][0]["bptAmount"]
    )

    assert tx.events["LOG_EXIT"][0]["tokenAmountOut"] + account0_DT_balance \
        == DT.balanceOf(address0)
    assert ssContractBPTbalance == pool.balanceOf(ss_bot.address)
    assert ssContractDTbalance == DT.balanceOf(ss_bot.address)


def _deployBPool(
        OCEAN_base_funding=10000,
        do_extra_funding:bool=True,
        OCEAN_extra_funding=10000,
        OCEAN_init_liquidity=2000,
        DT_cap=10000, 
        DT_vest_amt=1000,
        DT_vest_num_blocks=600,
):

    fundOCEANFromAbove(address0, toBase18(OCEAN_base_funding))
    
    router = oceanv4util.deployRouter(account0)
    
    (data_NFT, erc721_factory) = oceanv4util.createDataNFT(
        "dataNFT", "DATANFTSYMBOL", account0, router)

    DT = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSYMBOL", DT_cap, data_NFT, account0)

    DT_OCEAN_rate = 0.1
    pool = oceanv4util.createBPoolFromDatatoken(
        DT, erc721_factory, account0,
        OCEAN_init_liquidity, DT_OCEAN_rate,
        DT_vest_amt, DT_vest_num_blocks)
    
    ss_bot_address = pool.getController()
    ss_bot = BROWNIE_PROJECT080.SideStaking.at(ss_bot_address)

    if do_extra_funding:
        fundOCEANFromAbove(address0, toBase18(OCEAN_base_funding))
        OCEAN = OCEANtoken()
        OCEAN.approve(
            pool.address, toBase18(OCEAN_extra_funding), {"from": account0})
    
    return (DT, pool, ss_bot)
