import pytest

from web3engine import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools import web3util, web3wallet
from web3tools.web3util import toBase18, fromBase18

HUGEINT = 2**255

def test_notokens_basic(OCEAN_address, alice_wallet, alice_address):
    pool = _deployBPool(alice_wallet)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert not pool.isBound(OCEAN_address)
    assert pool.getNumTokens() == 0
    assert pool.getCurrentTokens() == []
    with pytest.raises(Exception):
        pool.getFinalTokens() #pool's not finalized
    assert pool.getSwapFee_base() == toBase18(1e-6)
    assert pool.getController() == alice_address
    assert str(pool)
    
    with pytest.raises(Exception): 
        pool.finalize() #can't finalize if no tokens

def test_setSwapFee_works(alice_wallet):
    pool = _deployBPool(alice_wallet)
    pool.setSwapFee(toBase18(0.011), from_wallet=alice_wallet)
    assert fromBase18(pool.getSwapFee_base()) == 0.011
    
def test_setSwapFee_fails(alice_wallet, alice_address,
                          bob_wallet, bob_address):
    factory = bfactory.BFactory()
    pool_address = factory.newBPool(alice_wallet)
    pool= bpool.BPool(pool_address)
    with pytest.raises(Exception):
        pool.setSwapFee(toBase18(0.011), from_wallet=bob_wallet) #not ok, bob isn't controller
    pool.setController(bob_address, from_wallet=alice_wallet)
    pool.setSwapFee(toBase18(0.011), from_wallet=bob_wallet) #ok now

def test_setController(alice_wallet, alice_address,
                       bob_wallet, bob_address):
    pool = _deployBPool(alice_wallet)
    pool.setController(bob_address, from_wallet=alice_wallet)
    assert pool.getController() == bob_address
    
    pool.setController(alice_address, from_wallet=bob_wallet)
    assert pool.getController() == alice_address

def test_setPublicSwap(alice_wallet):
    pool = _deployBPool(alice_wallet)
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    assert pool.isPublicSwap()
    pool.setPublicSwap(False, from_wallet=alice_wallet)
    assert not pool.isPublicSwap()

def test_2tokens_basic(T1, T2,
                       alice_wallet, alice_address):
    pool = _deployBPool(alice_wallet)
    assert T1.address != T2.address
    assert T1.address != pool.address

    assert fromBase18(T1.balanceOf_base(alice_address)) >= 90.0
    bal2 = fromBase18(T2.balanceOf_base(alice_address)) >= 10.0

    with pytest.raises(Exception): #can't bind until we approve
        pool.bind(T1.address, toBase18(90.0), toBase18(9.0))

    #Bind two tokens to the pool
    T1.approve(pool.address, toBase18(90.0), from_wallet=alice_wallet)
    T2.approve(pool.address, toBase18(10.0), from_wallet=alice_wallet)

    assert fromBase18(T1.allowance_base(alice_address, pool.address)) == 90.0
    assert fromBase18(T2.allowance_base(alice_address, pool.address)) == 10.0
    
    assert not pool.isBound(T1.address) and not pool.isBound(T1.address)
    pool.bind(T1.address,toBase18(90.0),toBase18(9.0),from_wallet=alice_wallet)
    pool.bind(T2.address,toBase18(10.0),toBase18(1.0),from_wallet=alice_wallet)
    assert pool.isBound(T1.address) and pool.isBound(T2.address)
    
    assert pool.getNumTokens() == 2
    assert pool.getCurrentTokens() == [T1.address, T2.address]

    assert pool.getDenormalizedWeight_base(T1.address) == toBase18(9.0)
    assert pool.getDenormalizedWeight_base(T2.address) == toBase18(1.0)
    assert pool.getTotalDenormalizedWeight_base() == toBase18(9.0+1.0)
    
    assert pool.getNormalizedWeight_base(T1.address) == toBase18(0.9)
    assert pool.getNormalizedWeight_base(T2.address) == toBase18(0.1)

    assert pool.getBalance_base(T1.address) == toBase18(90.0)
    assert pool.getBalance_base(T2.address) == toBase18(10.0)

    assert str(pool)

def test_unbind(T1, T2, alice_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,1.0,1.0,1.0,1.0)
    
    pool.unbind(T1.address, from_wallet=alice_wallet)
    
    assert pool.getNumTokens() == 1
    assert pool.getCurrentTokens() == [T2.address]
    assert fromBase18(pool.getBalance_base(T2.address)) == 1.0

def test_finalize(T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert pool.totalSupply_base() == 0
    assert pool.balanceOf_base(alice_address) == 0
    assert pool.allowance_base(alice_address, pool.address) == 0
    
    pool.finalize(from_wallet=alice_wallet)
    
    assert pool.isPublicSwap()
    assert pool.isFinalized()
    assert pool.totalSupply_base() == toBase18(100.0)
    assert pool.balanceOf_base(alice_address) == toBase18(100.0)
    assert pool.allowance_base(alice_address, pool.address) == 0

    assert pool.getFinalTokens() == [T1.address, T2.address]
    assert pool.getCurrentTokens() == [T1.address, T2.address]
    
def test_public_pool(T1, T2,
                     alice_address, alice_wallet,
                     bob_address, bob_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool
        
    #alice give Bob some tokens
    T1.transfer(bob_address, toBase18(100.0), from_wallet=alice_wallet)
    T2.transfer(bob_address, toBase18(100.0), from_wallet=alice_wallet)

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == 0
    
    assert fromBase18(T1.balanceOf_base(bob_address)) == 100.0
    assert fromBase18(T2.balanceOf_base(bob_address)) == 100.0
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 0
    
    assert fromBase18(T1.balanceOf_base(pool.address))== 90.0
    assert fromBase18(T2.balanceOf_base(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0

    #finalize
    pool= bpool.BPool(pool.address)
    pool.finalize(from_wallet=alice_wallet)

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == 100.0 #new!
    
    assert fromBase18(T1.balanceOf_base(pool.address))== 90.0
    assert fromBase18(T2.balanceOf_base(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0

    #bob join pool. Wants 10 BPT
    T1.approve(pool.address, toBase18(100.0), from_wallet=bob_wallet)
    T2.approve(pool.address, toBase18(100.0), from_wallet=bob_wallet)
    pool.joinPool(poolAmountOut_base=toBase18(10.0), #10 BPT
                  maxAmountsIn_base=[toBase18(100.0),toBase18(100.0)],
                  from_wallet=bob_wallet)

    #verify holdings
    assert fromBase18(T1.balanceOf_base(alice_address)) == (1000.0-90.0-100.0)
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0-10.0-100.0)
    assert fromBase18(BPT.balanceOf_base(alice_address))== 100.0 
    
    assert fromBase18(T1.balanceOf_base(bob_address)) == (100.0-9.0)
    assert fromBase18(T2.balanceOf_base(bob_address)) == (100.0-1.0)
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 10.0 
    
    assert fromBase18(T1.balanceOf_base(pool.address)) == (90.0+9.0)
    assert fromBase18(T2.balanceOf_base(pool.address)) == (10.0+1.0)
    assert fromBase18(BPT.balanceOf_base(pool.address)) == 0
    
    #bob sells 2 BPT
    # -this is where BLabs fee kicks in. But the fee is currently set to 0.
    pool.exitPool(poolAmountIn_base=toBase18(2.0), 
                  minAmountsOut_base=[toBase18(0.0),toBase18(0.0)],
                  from_wallet=bob_wallet)
    assert fromBase18(T1.balanceOf_base(bob_address)) == 92.8
    assert fromBase18(T2.balanceOf_base(bob_address)) == 99.2
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 8.0 
    
    #bob buys 5 more BPT
    pool.joinPool(poolAmountOut_base=toBase18(5.0), 
                  maxAmountsIn_base=[toBase18(90.0),toBase18(90.0)],
                  from_wallet=bob_wallet)
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 13.0
    
    #bob fully exits
    pool.exitPool(poolAmountIn_base=toBase18(13.0), 
                  minAmountsOut_base=[toBase18(0.0),toBase18(0.0)],
                  from_wallet=bob_wallet)
    assert fromBase18(BPT.balanceOf_base(bob_address)) == 0.0


def test_rebind_more_tokens(T1, T2, alice_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    
    #insufficient allowance
    with pytest.raises(Exception): 
        pool.rebind(T1.address, toBase18(120.0), toBase18(9.0),
                    from_wallet=alice_wallet)
        
    #sufficient allowance
    T1.approve(pool.address, toBase18(30.0),
               from_wallet=alice_wallet)
    pool.rebind(T1.address, toBase18(120.0), toBase18(9.0),
                from_wallet=alice_wallet)
    
def test_gulp(T1, alice_wallet):
    pool = _deployBPool(alice_wallet)
    
    #bind T1 to the pool, with a balance of 2.0
    T1.approve(pool.address, toBase18(50.0), from_wallet=alice_wallet)
    pool.bind(T1.address, toBase18(2.0), toBase18(50.0),
              from_wallet=alice_wallet)

    #T1 is now pool's (a) ERC20 balance (b) _records[token].balance 
    assert T1.balanceOf_base(pool.address) == toBase18(2.0) #ERC20 balance
    assert pool.getBalance_base(T1.address) == toBase18(2.0) #records[]

    #but then some joker accidentally sends 5.0 tokens to the pool's address
    #  rather than binding / rebinding. So it's in ERC20 bal but not records[]
    T1.transfer(pool.address, toBase18(5.0), from_wallet=alice_wallet)
    assert T1.balanceOf_base(pool.address) == toBase18(2.0+5.0) #ERC20 bal
    assert pool.getBalance_base(T1.address) == toBase18(2.0) #records[]

    #so, 'gulp' gets the pool to absorb the tokens into its balances.
    # i.e. to update _records[token].balance to be in sync with ERC20 balance
    pool.gulp(T1.address, from_wallet=alice_wallet)
    assert T1.balanceOf_base(pool.address) == toBase18(2.0+5.0) #ERC20
    assert pool.getBalance_base(T1.address) == toBase18(2.0+5.0) #records[]

def test_spot_price(T1, T2, alice_wallet):
    (p, p_sans) = _spotPrices(T1, T2, alice_wallet,
                              1.0, 1.0, 1.0, 1.0)
    assert p_sans == 1.0
    assert round(p,8) == 1.000001

    (p, p_sans) = _spotPrices(T1, T2, alice_wallet,
                              90.0, 10.0, 9.0, 1.0)
    assert p_sans == 1.0
    assert round(p,8) == 1.000001
    
    (p, p_sans) = _spotPrices(T1, T2, alice_wallet,
                              1.0, 2.0, 1.0, 1.0)
    assert p_sans == 0.5
    assert round(p,8) == 0.5000005
    
    (p, p_sans) = _spotPrices(T1, T2, alice_wallet,
                              2.0, 1.0, 1.0, 1.0)
    assert p_sans == 2.0
    assert round(p,8) == 2.000002

    (p, p_sans) = _spotPrices(T1, T2, alice_wallet,
                              9.0, 10.0, 9.0,1.0)
    assert p_sans == 0.1
    assert round(p,8) == 0.1000001


def _spotPrices(T1: btoken.BToken, T2: btoken.BToken,
                wallet: web3wallet.Web3Wallet, 
                bal1:float, bal2:float, w1:float, w2:float):
    pool = _createPoolWith2Tokens(T1,T2,wallet, bal1, bal2, w1, w2)
    a1, a2 = T1.address, T2.address
    return (fromBase18(pool.getSpotPrice_base(a1, a2)),
            fromBase18(pool.getSpotPriceSansFee_base(a1, a2))) 
    
def test_joinSwapExternAmountIn(T1, T2, alice_wallet, alice_address): 
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    T1.approve(pool.address, toBase18(100.0), from_wallet=alice_wallet)

    #pool's not public
    with pytest.raises(Exception): 
        pool.swapExactAmountOut(
                tokenIn_address = T1.address,
                maxAmountIn_base = toBase18(100.0),
                tokenOut_address = T2.address,
                tokenAmountOut_base = toBase18(10.0),
                maxPrice_base = HUGEINT,
                from_wallet=alice_wallet)

    #pool's public
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    pool.swapExactAmountOut(
            tokenIn_address = T1.address,
            maxAmountIn_base = toBase18(100.0),
            tokenOut_address = T2.address,
            tokenAmountOut_base = toBase18(1.0),
            maxPrice_base = HUGEINT,
            from_wallet=alice_wallet)
    assert 908.94 <= fromBase18(T1.balanceOf_base(alice_address)) <= 908.95
    assert fromBase18(T2.balanceOf_base(alice_address)) == (1000.0 - 9.0)
    
def test_joinswapPoolAmountOut(T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize(from_wallet=alice_wallet)
    T1.approve(pool.address, toBase18(90.0), from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.joinswapPoolAmountOut(
            tokenIn_address = T1.address,
            poolAmountOut_base = toBase18(10.0), #BPT wanted
            maxAmountIn_base = toBase18(90.0),  #max T1 to spend
            from_wallet=alice_wallet) 
    assert fromBase18(T1.balanceOf_base(alice_address)) >= (910.0 - 90.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == (100.0 + 10.0)

def test_exitswapPoolAmountIn(T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize(from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.exitswapPoolAmountIn(
            tokenOut_address = T1.address,
            poolAmountIn_base = toBase18(10.0), #BPT spent
            minAmountOut_base = toBase18(1.0),  #min T1 wanted
            from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) >= (910.0 + 1.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) == (100.0 - 10.0)

def test_exitswapExternAmountOut(T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(T1,T2,alice_wallet,90.0,10.0,9.0,1.0)
    BPT = pool    
    pool.finalize(from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == 910.0
    pool.exitswapExternAmountOut(
            tokenOut_address = T1.address,
            tokenAmountOut_base = toBase18(2.0), #T1 wanted
            maxPoolAmountIn_base = toBase18(10.0), #max BPT spent 
            from_wallet=alice_wallet)
    assert fromBase18(T1.balanceOf_base(alice_address)) == (910.0 + 2.0)
    assert fromBase18(BPT.balanceOf_base(alice_address)) >= (100.0 - 10.0)

def test_calcSpotPrice_base(T1, T2, alice_address, alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcSpotPrice_base(
        tokenBalanceIn_base = toBase18(10.0),
        tokenWeightIn_base = toBase18(1.0),
        tokenBalanceOut_base = toBase18(11.0),
        tokenWeightOut_base = toBase18(1.0),
        swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.909

def test_calcOutGivenIn_base(alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcOutGivenIn_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            tokenBalanceOut = toBase18(10.1),
            tokenWeightOut_base = toBase18(1.0),
            tokenAmountIn_base = toBase18(1.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.918

def test_calcInGivenOut_base(alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcInGivenOut_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            tokenBalanceOut_base = toBase18(10.1),
            tokenWeightOut_base = toBase18(1.0),
            tokenAmountOut_base = toBase18(1.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.099

def test_calcPoolOutGivenSingleIn_base(alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcPoolOutGivenSingleIn_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            tokenAmountIn_base = toBase18(0.1),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.599    

def test_calcSingleInGivenPoolOut_base(alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcSingleInGivenPoolOut_base(
            tokenBalanceIn_base = toBase18(10.0),
            tokenWeightIn_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            poolAmountOut_base = toBase18(10.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.736

def test_calcSingleOutGivenPoolIn_base(alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcSingleOutGivenPoolIn_base(
            tokenBalanceOut_base = toBase18(10.0),
            tokenWeightOut_base = toBase18(1.0),
            poolSupply_base = toBase18(120.0),
            totalWeight_base = toBase18(2.0),
            poolAmountIn_base = toBase18(10.0),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 1.597

def test_calcPoolInGivenSingleOut_base(alice_wallet):
    pool = _deployBPool(alice_wallet)
    x = pool.calcPoolInGivenSingleOut(
            tokenBalanceOut_base = toBase18(1000.0),
            tokenWeightOut_base = toBase18(5.0),
            poolSupply_base = toBase18(100.0),
            totalWeight_base = toBase18(10.0),
            tokenAmountOut_base = toBase18(0.1),
            swapFee_base = 0)
    assert round(fromBase18(x),3) == 0.005

def _createPoolWith2Tokens(T1: btoken.BToken, T2: btoken.BToken,
                           wallet: web3wallet.Web3Wallet, 
                           bal1:float, bal2:float, w1:float, w2:float):
    pool = _deployBPool(wallet)
    
    T1.approve(pool.address, toBase18(bal1), from_wallet=wallet)
    T2.approve(pool.address, toBase18(bal2), from_wallet=wallet)

    pool.bind(T1.address, toBase18(bal1), toBase18(w1), from_wallet=wallet)
    pool.bind(T2.address, toBase18(bal2), toBase18(w2), from_wallet=wallet)

    return pool

def _deployBPool(from_wallet: web3wallet.Web3Wallet) -> bpool.BPool:
    f = bfactory.BFactory()
    p_address = f.newBPool(from_wallet=from_wallet)
    p = bpool.BPool(p_address)
    return p
