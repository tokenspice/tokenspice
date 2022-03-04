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
    
    OCEAN_init_liquidity = 2000 #initial liquidity in OCEAN on pool creation
    DT_OCEAN_rate = 0.1
    
    DT_cap = 10000
    DT_vest_amt = 1000
    DT_vest_num_blocks = 600
    (DT, pool, ssbot) = _deployBPool(
        OCEAN_base_funding, do_extra_funding, OCEAN_extra_funding,
        OCEAN_init_liquidity, DT_OCEAN_rate,
        DT_cap, DT_vest_amt, DT_vest_num_blocks)

    #basic tests
    assert pool.getBaseTokenAddress() == OCEAN.address
    assert ssbot.getBaseTokenAddress(DT.address) == OCEAN.address
    assert ssbot.getBaseTokenBalance(DT.address) == 0
    
    assert ssbot.getPublisherAddress(DT.address) == address0
    assert ssbot.getPoolAddress(DT.address) == pool.address
    
    assert fromBase18(ssbot.getvestingAmount(DT.address)) == 1000

    # ssbot manages DTs in two specific ways:
    # 1. Linear vesting of DTs to publisher over a fixed # blocks
    # 2. When OCEAN liquidity is added to the pool, it
    #    moves DT from its balance into the pool (ultimately, DT circ supply)
    #    such that DT:OCEAN ratio stays constant

    # Therefore: (DT_vested) + (ssbot_DT_balance + DT_circ_supply) = DT_cap

    # No blocks have passed since pool creation. Therefore no vesting yet
    assert ssbot.getvestingAmountSoFar(DT.address) == 0
    
    # We start out with a given OCEAN_init_liquidity. And, DT_OCEAN_rate is
    # the initial DT:OCEAN ratio.
    # Therefore we know how many DT the bot was supposed to add to the pool:
    # OCEAN_init_liquidity * DT_OCEAN_rate = 2000*0.1 = 200
    # Since no one's swapped for DT, then this is also DT circulating supply
    assert fromBase18(ssbot.getDatatokenCirculatingSupply(DT.address)) == 200
    
    # The ssbot holds the rest of the DT. Rerrange formula above to see amt.
    # So,ssbot_DT_balance = DT_cap - DT_vested - DT_circ_supply
    #                     = 10000  - 0         - 200
    #                     = 9800
    assert fromBase18(DT.balanceOf(ssbot.address)) == 9800

    # ========================================================
    # Test vesting... (recall DT_vest_amt = 1000)
    assert fromBase18(ssbot.getvestingAmount(DT.address)) == 1000

    #datatoken.deployPool() 
    # -> call BFactory.newBPool()
    # -> call SideStaking.newDatatokenCreated()
    # -> emit VestingCreated(datatokenAddress, publisherAddress,
    #                       _datatokens[datatokenAddress].vestingEndBlock,
    #                       _datatokens[datatokenAddress].vestingAmount)
    
    assert ssbot.getAvailableVesting(DT.address) == 0
    assert ssbot.getvestingAmountSoFar(DT.address) == 0
    
    # Pass enough time to make all vesting happen!    
    brownie.chain.mine(blocks=DT_vest_num_blocks)

    # Test key numbers
    block_number = len(brownie.chain)
    vesting_end_block = ssbot.getvestingEndBlock(DT.address)
    vesting_last_block = ssbot.getvestingLastBlock(DT.address) 
    blocks_passed = vesting_end_block - vesting_last_block 
    available_vesting = fromBase18(ssbot.getAvailableVesting(DT.address)) 

    assert block_number == 616
    assert vesting_end_block == 615
    assert vesting_last_block == 15 #last block when tokens were vested
    assert blocks_passed == 600
    assert available_vesting == 1000

    # Publisher hasn't claimed yet, so no vesting or DTs
    assert ssbot.getvestingAmountSoFar(DT.address) == 0
    assert DT.balanceOf(account0) == 0

    # Publisher claims. Now he has vesting and DTs
    ssbot.getVesting(DT.address, {"from": account0}) #claim!
    assert fromBase18(ssbot.getvestingAmountSoFar(DT.address)) == 1000
    assert fromBase18(DT.balanceOf(account0)) == 1000

    # The ssbot's holdings are updated too
    # ssbot_DT_balance = DT_cap - DT_vested - DT_circ_supply
    #                  = 10000  - 1000      - 200
    #                  = 8800
    assert fromBase18(ssbot.getDatatokenBalance(DT.address)) == 8800

    #
    assert ssbot.getvestingLastBlock(DT.address) == 616 == block_number

def test_swapExactAmountIn():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ssbot) = _deployBPool(do_extra_funding=True)

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
    (DT, pool, ssbot) = _deployBPool(do_extra_funding=True)

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
    (DT, pool, ssbot) = _deployBPool(do_extra_funding=True)

    tokenInOutMarket = [OCEAN.address, DT.address, address0]
    # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(1), toBase18(100), 0]
    # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee]

    assert DT.balanceOf(address0) == 0
    pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, {"from": account0})

    account0_DT_balance = DT.balanceOf(address0)
    account0_OCEAN_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ssbot.address)
    ssContractBPTbalance = pool.balanceOf(ssbot.address)

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
        == account0_OCEAN_balance
    )
    assert account0_BPT_balance + BPTAmountOut == pool.balanceOf(address0)

    # check ssContract BPT and DT balance didn't change
    assert ssContractBPTbalance == pool.balanceOf(ssbot.address)
    assert ssContractDTbalance == DT.balanceOf(ssbot.address)


def test_joinswapExternAmountIn_addOCEAN():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ssbot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ssbot.address)
    ssContractBPTbalance = pool.balanceOf(ssbot.address)

    oceanAmountIn = toBase18(100)
    minBPTOut = toBase18(0.1)

    tx = pool.joinswapExternAmountIn(
        oceanAmountIn, minBPTOut, {"from": account0}
    )

    assert tx.events["LOG_JOIN"][0]["tokenIn"] == OCEAN.address
    assert tx.events["LOG_JOIN"][0]["tokenAmountIn"] == oceanAmountIn

    assert tx.events["LOG_JOIN"][1]["tokenIn"] == DT.address
    ssbotAmountIn = ssContractDTbalance - DT.balanceOf(ssbot.address)
    assert ssbotAmountIn == tx.events["LOG_JOIN"][1]["tokenAmountIn"]

    # we check ssContract actually moved DT and got back BPT
    assert (
        DT.balanceOf(ssbot.address)
        == ssContractDTbalance - tx.events["LOG_JOIN"][1]["tokenAmountIn"]
    )
    assert (
        pool.balanceOf(ssbot.address)
        == ssContractBPTbalance + tx.events["LOG_BPT"]["bptAmount"]
    )

    # no datatoken where taken from account0
    assert account0_DT_balance == DT.balanceOf(address0)


def test_exitPool_receiveTokens():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ssbot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_OCEAN_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ssbot.address)
    ssContractBPTbalance = pool.balanceOf(ssbot.address)

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
    ] + account0_OCEAN_balance == OCEAN.balanceOf(address0)
    assert pool.balanceOf(address0) + BPTAmountIn == account0_BPT_balance

    # check the ssContract BPT and DT balance didn"t change
    assert ssContractBPTbalance == pool.balanceOf(ssbot.address)
    assert ssContractDTbalance == DT.balanceOf(ssbot.address)


def test_exitswapPoolAmountIn_receiveOcean():
    brownie.chain.reset()
    OCEAN = OCEANtoken()
    (DT, pool, ssbot) = _deployBPool(do_extra_funding=True)

    account0_DT_balance = DT.balanceOf(address0)
    account0_OCEAN_balance = OCEAN.balanceOf(address0)
    account0_BPT_balance = pool.balanceOf(address0)
    ssContractDTbalance = DT.balanceOf(ssbot.address)
    ssContractBPTbalance = pool.balanceOf(ssbot.address)

    BPTAmountIn = toBase18(0.5)
    minOceanOut = toBase18(0.5)

    tx = pool.exitswapPoolAmountIn(
        BPTAmountIn, minOceanOut, {"from": account0}
    )

    assert DT.balanceOf(address0) == account0_DT_balance

    # check event argument
    assert tx.events["LOG_EXIT"][0]["caller"] == address0
    assert tx.events["LOG_EXIT"][0]["tokenOut"] == OCEAN.address
    assert tx.events["LOG_EXIT"][1]["tokenOut"] == DT.address

    # check user ocean balance
    assert tx.events["LOG_EXIT"][0][
        "tokenAmountOut"
    ] + account0_OCEAN_balance == OCEAN.balanceOf(address0)

    # check BPT balance
    assert account0_BPT_balance == pool.balanceOf(address0) + BPTAmountIn

    # check the ssContract BPT balance
    assert ssContractBPTbalance == pool.balanceOf(ssbot.address) + BPTAmountIn

    # ssContract got back his dt when redeeeming BPT
    assert ssContractDTbalance + tx.events["LOG_EXIT"][1][
        "tokenAmountOut"
    ] == DT.balanceOf(ssbot.address)


def _deployBPool(
        OCEAN_base_funding=10000,
        do_extra_funding:bool=True,
        OCEAN_extra_funding=10000,
        OCEAN_init_liquidity=2000,
        DT_OCEAN_rate=0.1,
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

    pool = oceanv4util.createBPoolFromDatatoken(
        DT, erc721_factory, account0,
        OCEAN_init_liquidity, DT_OCEAN_rate,
        DT_vest_amt, DT_vest_num_blocks)
    
    ssbot_address = pool.getController()
    ssbot = BROWNIE_PROJECT080.SideStaking.at(ssbot_address)

    if do_extra_funding:
        fundOCEANFromAbove(address0, toBase18(OCEAN_base_funding))
        OCEAN = OCEANtoken()
        OCEAN.approve(
            pool.address, toBase18(OCEAN_extra_funding), {"from": account0})
    
    return (DT, pool, ssbot)
