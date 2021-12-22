import brownie

import sol080.contracts.oceanv4.oceanv4util 
from sol080.contracts.oceanv4.oceanv4util import OCEANtoken, fundOCEANFromAbove, ROUTER, SIDESTAKING
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT, GOD_ACCOUNT, ZERO_ADDRESS

GOD_ADDRESS = GOD_ACCOUNT.address
OPF_ADDRESS = OPF_ACCOUNT.address

accounts = brownie.network.accounts
account0 = accounts[0] 
address0 = account0.address

account1 = accounts[1]
address1 = account1.address

account2 = accounts[2] 
address2 = account2.address

account3 = accounts[3] 
address3 = account3.address

OPF_ADDRESS = OPF_ACCOUNT.address

def test_sideStaking_properties():    
    pool = _deployBPool()
    pool_address = pool.address
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())
    dt_address = datatoken.address
    OCEAN = OCEANtoken()
    sideStaking = SIDESTAKING()
    initialBlockNum = brownie.chain.height

    assert sideStaking.getPoolAddress(dt_address) == pool_address
    assert sideStaking.getBaseTokenAddress(dt_address) == pool.getBaseTokenAddress()
    assert sideStaking.getBaseTokenAddress(dt_address) == OCEAN.address
    assert sideStaking.getPublisherAddress(dt_address) == address0

    assert datatoken.balanceOf(sideStaking.address) == toBase18(9800) #depend on ss_rate, DT_vest_amount, ss_OCEAN_init_liquidity
    assert sideStaking.getDataTokenCirculatingSupply(datatoken.address) == toBase18(1200)

    assert sideStaking.getBaseTokenBalance(datatoken.address) == 0
    assert sideStaking.getDataTokenBalance(datatoken.address) == toBase18(8800)

    assert sideStaking.getDataTokenCurrentCirculatingSupply(datatoken.address) == toBase18(2000*0.1) # ss_rate*ss_OCEAN_init_liquidity

    assert sideStaking.getvestingAmountSoFar(dt_address) == 0
    assert sideStaking.getvestingAmount(datatoken.address) == toBase18(1000)

    assert sideStaking.getvestingLastBlock(datatoken.address) == initialBlockNum
    assert sideStaking.getvestingEndBlock(datatoken.address) == initialBlockNum + 2500000

    
def test_swapExactAmountIn():
    pool = _deployBPool()
    OCEAN = OCEANtoken()
    fundOCEANFromAbove(address1, toBase18(10000))
    OCEAN.approve(pool.address, toBase18(10000), {"from": account1})
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())
    
    tokenInOutMarket = [OCEAN.address, datatoken.address, address1]; # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(1), toBase18(100), 0]; # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee]

    assert datatoken.balanceOf(address1) == 0
    pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, {"from":account1})
    assert datatoken.balanceOf(address1) > 0

    # swaps some DT back to Ocean swapExactAmountIn
    dt_balance_before = datatoken.balanceOf(account1.address)
    ocean_balance_before = OCEAN.balanceOf(account1.address)

    datatoken.approve(pool.address, toBase18(1000), {"from":account1})
    tokenInOutMarket = [datatoken.address, OCEAN.address, address1]; # [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(1), toBase18(1), toBase18(100), 0]; # [exactAmountIn,minAmountOut,maxPrice,_swapMarketFee]
    pool.swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee, {"from":account1})

    assert datatoken.balanceOf(account1.address) < dt_balance_before
    assert OCEAN.balanceOf(account1.address) > ocean_balance_before

def test_swapExactAmountOut():
    pool = _deployBPool()
    OCEAN = OCEANtoken()
    fundOCEANFromAbove(address1, toBase18(10000))
    OCEAN.approve(pool.address, toBase18(10000), {"from": account1})
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())

    tokenInOutMarket = [OCEAN.address, datatoken.address, address1] #// [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(1000), toBase18(10), toBase18(1000), 0]

    pool.swapExactAmountOut(tokenInOutMarket, amountsInOutMaxFee, {"from": account1})
    assert datatoken.balanceOf(address1) > 0

def test_add_liquidity_both_tokens_with_joinPool():
    pool = _deployBPool()
    OCEAN = OCEANtoken()
    fundOCEANFromAbove(address1, toBase18(10000))
    OCEAN.approve(pool.address, toBase18(10000), {"from": account1})
    datatoken = BROWNIE_PROJECT080.ERC20Template.at(pool.getDataTokenAddress())
    datatoken.approve(pool.address, toBase18(50), {"from": account1})

    tokenInOutMarket = [OCEAN.address, datatoken.address, address1] #// [tokenIn,tokenOut,marketFeeAddress]
    amountsInOutMaxFee = [toBase18(100), toBase18(10), toBase18(10), 0]

    pool.swapExactAmountOut(tokenInOutMarket, amountsInOutMaxFee, {"from": account1})

    BPTAmountOut = toBase18(0.01)
    maxAmountsIn = [
        toBase18(50), #// Amounts IN
        toBase18(50) # // Amounts IN
    ]
    pool.joinPool(BPTAmountOut,maxAmountsIn, {"from":account1})

# def test_add_liquidity_only_OCEAN_with_joinswapExternAmountIn_()
# def adds more liquidity with joinswapPoolAmountOut (only OCEAN)



def _deployBPool():
    router = ROUTER()
    dataNFT = sol080.contracts.oceanv4.oceanv4util.createDataNFT("dataNFT", "DATANFTSYMBOL", account0, router)
    datatoken = sol080.contracts.oceanv4.oceanv4util.create_datatoken_from_dataNFT("DT", "DTSYMBOL", 10000, dataNFT, account0)
    pool = sol080.contracts.oceanv4.oceanv4util.create_BPool_from_datatoken(datatoken, 1000, 2000, account0)

    return pool
