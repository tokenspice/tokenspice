import brownie
import pytest

import sol057.contracts.oceanv3.oceanv3util
from util import globaltokens
from util.base18 import toBase18, fromBase18

accounts = brownie.network.accounts
account0, account1 = accounts[0], accounts[1]
address0, address1 = account0.address, account1.address
OCEAN_address = globaltokens.OCEAN_address()
HUGEINT = 2 ** 255


def test_notokens_basic():
    pool = _deployBPool()

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert not pool.isBound(OCEAN_address)
    assert pool.getNumTokens() == 0
    assert pool.getCurrentTokens() == []
    with pytest.raises(Exception):
        pool.getFinalTokens()  # pool's not finalized
    assert pool.getSwapFee() == toBase18(1e-6)
    assert pool.getController() == address0
    assert str(pool)

    with pytest.raises(Exception):
        pool.finalize()  # can't finalize if no tokens


def test_setSwapFee_works():
    pool = _deployBPool()
    pool.setSwapFee(toBase18(0.011), {"from": account0})
    assert fromBase18(pool.getSwapFee()) == 0.011


def test_setSwapFee_fails():
    pool = _deployBPool()
    with pytest.raises(Exception):
        # fail, because account1 isn't controller
        pool.setSwapFee(toBase18(0.011), {"from": account1})
    pool.setController(address1, {"from": account0})
    pool.setSwapFee(toBase18(0.011), {"from": account1})  # pass now


def test_setController():
    pool = _deployBPool()
    pool.setController(address1, {"from": account0})
    assert pool.getController() == address1

    pool.setController(address0, {"from": account1})
    assert pool.getController() == address0


def test_setPublicSwap():
    pool = _deployBPool()
    pool.setPublicSwap(True, {"from": account0})
    assert pool.isPublicSwap()
    pool.setPublicSwap(False, {"from": account0})
    assert not pool.isPublicSwap()


def test_2tokens_basic(T1, T2):
    pool = _deployBPool()
    assert T1.address != T2.address
    assert T1.address != pool.address

    assert fromBase18(T1.balanceOf(address0)) >= 90.0
    assert fromBase18(T2.balanceOf(address0)) >= 10.0

    with pytest.raises(Exception):  # can't bind until we approve
        pool.bind(T1.address, toBase18(90.0), toBase18(9.0))

    # Bind two tokens to the pool
    T1.approve(pool.address, toBase18(90.0), {"from": account0})
    T2.approve(pool.address, toBase18(10.0), {"from": account0})

    assert fromBase18(T1.allowance(address0, pool.address)) == 90.0
    assert fromBase18(T2.allowance(address0, pool.address)) == 10.0

    assert not pool.isBound(T1.address) and not pool.isBound(T1.address)
    pool.bind(T1.address, toBase18(90.0), toBase18(9.0), {"from": account0})
    pool.bind(T2.address, toBase18(10.0), toBase18(1.0), {"from": account0})
    assert pool.isBound(T1.address) and pool.isBound(T2.address)

    assert pool.getNumTokens() == 2
    assert pool.getCurrentTokens() == [T1.address, T2.address]

    assert pool.getDenormalizedWeight(T1.address) == toBase18(9.0)
    assert pool.getDenormalizedWeight(T2.address) == toBase18(1.0)
    assert pool.getTotalDenormalizedWeight() == toBase18(9.0 + 1.0)

    assert pool.getNormalizedWeight(T1.address) == toBase18(0.9)
    assert pool.getNormalizedWeight(T2.address) == toBase18(0.1)

    assert pool.getBalance(T1.address) == toBase18(90.0)
    assert pool.getBalance(T2.address) == toBase18(10.0)

    assert str(pool)


def test_unbind(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 1.0, 1.0, 1.0, 1.0)

    pool.unbind(T1.address, {"from": account0})

    assert pool.getNumTokens() == 1
    assert pool.getCurrentTokens() == [T2.address]
    assert fromBase18(pool.getBalance(T2.address)) == 1.0


def test_finalize(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert pool.totalSupply() == 0
    assert pool.balanceOf(address0) == 0
    assert pool.allowance(address0, pool.address) == 0

    pool.finalize({"from": account0})

    assert pool.isPublicSwap()
    assert pool.isFinalized()
    assert pool.totalSupply() == toBase18(100.0)
    assert pool.balanceOf(address0) == toBase18(100.0)
    assert pool.allowance(address0, pool.address) == 0

    assert pool.getFinalTokens() == [T1.address, T2.address]
    assert pool.getCurrentTokens() == [T1.address, T2.address]


def test_public_pool(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)
    BPT = pool

    # alice give Bob some tokens
    T1.transfer(address1, toBase18(100.0), {"from": account0})
    T2.transfer(address1, toBase18(100.0), {"from": account0})

    # verify holdings
    assert fromBase18(T1.balanceOf(address0)) == (1000.0 - 90.0 - 100.0)
    assert fromBase18(T2.balanceOf(address0)) == (1000.0 - 10.0 - 100.0)
    assert fromBase18(BPT.balanceOf(address0)) == 0

    assert fromBase18(T1.balanceOf(address1)) == 100.0
    assert fromBase18(T2.balanceOf(address1)) == 100.0
    assert fromBase18(BPT.balanceOf(address1)) == 0

    assert fromBase18(T1.balanceOf(pool.address)) == 90.0
    assert fromBase18(T2.balanceOf(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf(pool.address)) == 0

    # finalize
    pool.finalize({"from": account0})

    # verify holdings
    assert fromBase18(T1.balanceOf(address0)) == (1000.0 - 90.0 - 100.0)
    assert fromBase18(T2.balanceOf(address0)) == (1000.0 - 10.0 - 100.0)
    assert fromBase18(BPT.balanceOf(address0)) == 100.0  # new!

    assert fromBase18(T1.balanceOf(pool.address)) == 90.0
    assert fromBase18(T2.balanceOf(pool.address)) == 10.0
    assert fromBase18(BPT.balanceOf(pool.address)) == 0

    # bob join pool. Wants 10 BPT
    T1.approve(pool.address, toBase18(100.0), {"from": account1})
    T2.approve(pool.address, toBase18(100.0), {"from": account1})
    poolAmountOut = toBase18(10.0)  # 10 BPT
    maxAmountsIn = [toBase18(100.0), toBase18(100.0)]
    pool.joinPool(poolAmountOut, maxAmountsIn, {"from": account1})

    # verify holdings
    assert fromBase18(T1.balanceOf(address0)) == (1000.0 - 90.0 - 100.0)
    assert fromBase18(T2.balanceOf(address0)) == (1000.0 - 10.0 - 100.0)
    assert fromBase18(BPT.balanceOf(address0)) == 100.0

    assert fromBase18(T1.balanceOf(address1)) == (100.0 - 9.0)
    assert fromBase18(T2.balanceOf(address1)) == (100.0 - 1.0)
    assert fromBase18(BPT.balanceOf(address1)) == 10.0

    assert fromBase18(T1.balanceOf(pool.address)) == (90.0 + 9.0)
    assert fromBase18(T2.balanceOf(pool.address)) == (10.0 + 1.0)
    assert fromBase18(BPT.balanceOf(pool.address)) == 0

    # bob sells 2 BPT
    # -this is where BLabs fee kicks in. But the fee is currently set to 0.
    poolAmountIn = toBase18(2.0)
    minAmountsOut = [toBase18(0.0), toBase18(0.0)]
    pool.exitPool(poolAmountIn, minAmountsOut, {"from": account1})
    assert fromBase18(T1.balanceOf(address1)) == 92.8
    assert fromBase18(T2.balanceOf(address1)) == 99.2
    assert fromBase18(BPT.balanceOf(address1)) == 8.0

    # bob buys 5 more BPT
    poolAmountOut = toBase18(5.0)
    maxAmountsIn = [toBase18(90.0), toBase18(90.0)]
    pool.joinPool(poolAmountOut, maxAmountsIn, {"from": account1})
    assert fromBase18(BPT.balanceOf(address1)) == 13.0

    # bob fully exits
    poolAmountIn = toBase18(13.0)
    minAmountsOut = [toBase18(0.0), toBase18(0.0)]
    pool.exitPool(poolAmountIn, minAmountsOut, {"from": account1})
    assert fromBase18(BPT.balanceOf(address1)) == 0.0


def test_rebind_more_tokens(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)

    # insufficient allowance
    with pytest.raises(Exception):
        pool.rebind(T1.address, toBase18(120.0), toBase18(9.0), {"from": account0})

    # sufficient allowance
    T1.approve(pool.address, toBase18(30.0), {"from": account0})
    pool.rebind(T1.address, toBase18(120.0), toBase18(9.0), {"from": account0})


def test_gulp(T1):
    pool = _deployBPool()

    # bind T1 to the pool, with a balance of 2.0
    T1.approve(pool.address, toBase18(50.0), {"from": account0})
    pool.bind(T1.address, toBase18(2.0), toBase18(50.0), {"from": account0})

    # T1 is now pool's (a) ERC20 balance (b) _records[token].balance
    assert T1.balanceOf(pool.address) == toBase18(2.0)  # ERC20 balance
    assert pool.getBalance(T1.address) == toBase18(2.0)  # records[]

    # but then some joker accidentally sends 5.0 tokens to the pool's address
    #  rather than binding / rebinding. So it's in ERC20 bal but not records[]
    T1.transfer(pool.address, toBase18(5.0), {"from": account0})
    assert T1.balanceOf(pool.address) == toBase18(2.0 + 5.0)  # ERC20 bal
    assert pool.getBalance(T1.address) == toBase18(2.0)  # records[]

    # so, 'gulp' gets the pool to absorb the tokens into its balances.
    # i.e. to update _records[token].balance to be in sync with ERC20 balance
    pool.gulp(T1.address, {"from": account0})
    assert T1.balanceOf(pool.address) == toBase18(2.0 + 5.0)  # ERC20
    assert pool.getBalance(T1.address) == toBase18(2.0 + 5.0)  # records[]


def test_spot_price(T1, T2):
    (p, p_sans) = _spotPrices(T1, T2, 1.0, 1.0, 1.0, 1.0)
    assert p_sans == 1.0
    assert round(p, 8) == 1.000001

    (p, p_sans) = _spotPrices(T1, T2, 90.0, 10.0, 9.0, 1.0)
    assert p_sans == 1.0
    assert round(p, 8) == 1.000001

    (p, p_sans) = _spotPrices(T1, T2, 1.0, 2.0, 1.0, 1.0)
    assert p_sans == 0.5
    assert round(p, 8) == 0.5000005

    (p, p_sans) = _spotPrices(T1, T2, 2.0, 1.0, 1.0, 1.0)
    assert p_sans == 2.0
    assert round(p, 8) == 2.000002

    (p, p_sans) = _spotPrices(T1, T2, 9.0, 10.0, 9.0, 1.0)
    assert p_sans == 0.1
    assert round(p, 8) == 0.1000001


def _spotPrices(
    T1, T2, bal1: float, bal2: float, w1: float, w2: float
):  # pylint: disable=too-many-arguments
    pool = _createPoolWith2Tokens(T1, T2, bal1, bal2, w1, w2)
    a1, a2 = T1.address, T2.address
    return (
        fromBase18(pool.getSpotPrice(a1, a2)),
        fromBase18(pool.getSpotPriceSansFee(a1, a2)),
    )


def test_joinSwapExternAmountIn(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)
    T1.approve(pool.address, toBase18(100.0), {"from": account0})

    # pool's not public
    with pytest.raises(Exception):
        tokenIn_address = T1.address
        maxAmountIn = toBase18(100.0)
        tokenOut_address = T2.address
        tokenAmountOut = toBase18(10.0)
        maxPrice = HUGEINT
        pool.swapExactAmountOut(
            tokenIn_address,
            maxAmountIn,
            tokenOut_address,
            tokenAmountOut,
            maxPrice,
            {"from": account0},
        )

    # pool's public
    pool.setPublicSwap(True, {"from": account0})
    tokenIn_address = T1.address
    maxAmountIn = toBase18(100.0)
    tokenOut_address = T2.address
    tokenAmountOut = toBase18(1.0)
    maxPrice = HUGEINT
    pool.swapExactAmountOut(
        tokenIn_address,
        maxAmountIn,
        tokenOut_address,
        tokenAmountOut,
        maxPrice,
        {"from": account0},
    )
    assert 908.94 <= fromBase18(T1.balanceOf(address0)) <= 908.95
    assert fromBase18(T2.balanceOf(address0)) == (1000.0 - 9.0)


def test_joinswapPoolAmountOut(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)
    BPT = pool
    pool.finalize({"from": account0})
    T1.approve(pool.address, toBase18(90.0), {"from": account0})
    assert fromBase18(T1.balanceOf(address0)) == 910.0
    tokenIn_address = T1.address
    poolAmountOut = toBase18(10.0)  # BPT wanted
    maxAmountIn = toBase18(90.0)  # max T1 to spend
    pool.joinswapPoolAmountOut(
        tokenIn_address, poolAmountOut, maxAmountIn, {"from": account0}
    )
    assert fromBase18(T1.balanceOf(address0)) >= (910.0 - 90.0)
    assert fromBase18(BPT.balanceOf(address0)) == (100.0 + 10.0)


def test_exitswapPoolAmountIn(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)
    BPT = pool
    pool.finalize({"from": account0})
    assert fromBase18(T1.balanceOf(address0)) == 910.0
    tokenOut_address = T1.address
    poolAmountIn = toBase18(10.0)  # BPT spent
    minAmountOut = toBase18(1.0)  # min T1 wanted
    pool.exitswapPoolAmountIn(
        tokenOut_address, poolAmountIn, minAmountOut, {"from": account0}
    )
    assert fromBase18(T1.balanceOf(address0)) >= (910.0 + 1.0)
    assert fromBase18(BPT.balanceOf(address0)) == (100.0 - 10.0)


def test_exitswapExternAmountOut(T1, T2):
    pool = _createPoolWith2Tokens(T1, T2, 90.0, 10.0, 9.0, 1.0)
    BPT = pool
    pool.finalize({"from": account0})
    assert fromBase18(T1.balanceOf(address0)) == 910.0
    tokenOut_address = T1.address
    tokenAmountOut = toBase18(2.0)  # T1 wanted
    maxPoolAmountIn = toBase18(10.0)  # max BPT spent
    pool.exitswapExternAmountOut(
        tokenOut_address,
        tokenAmountOut,  # T1 wanted
        maxPoolAmountIn,  # max BPT spent
        {"from": account0},
    )
    assert fromBase18(T1.balanceOf(address0)) == (910.0 + 2.0)
    assert fromBase18(BPT.balanceOf(address0)) >= (100.0 - 10.0)


def test_calcSpotPrice():
    pool = _deployBPool()
    tokenBalanceIn = toBase18(10.0)
    tokenWeightIn = toBase18(1.0)
    tokenBalanceOut = toBase18(11.0)
    tokenWeightOut = toBase18(1.0)
    swapFee = 0
    x = pool.calcSpotPrice(
        tokenBalanceIn, tokenWeightIn, tokenBalanceOut, tokenWeightOut, swapFee
    )
    assert round(fromBase18(x), 3) == 0.909


def test_calcOutGivenIn():
    pool = _deployBPool()
    tokenBalanceIn = toBase18(10.0)
    tokenWeightIn = toBase18(1.0)
    tokenBalanceOut = toBase18(10.1)
    tokenWeightOut = toBase18(1.0)
    tokenAmountIn = toBase18(1.0)
    swapFee = 0
    x = pool.calcOutGivenIn(
        tokenBalanceIn,
        tokenWeightIn,
        tokenBalanceOut,
        tokenWeightOut,
        tokenAmountIn,
        swapFee,
    )
    assert round(fromBase18(x), 3) == 0.918


def test_calcInGivenOut():
    pool = _deployBPool()
    tokenBalanceIn = toBase18(10.0)
    tokenWeightIn = toBase18(1.0)
    tokenBalanceOut = toBase18(10.1)
    tokenWeightOut = toBase18(1.0)
    tokenAmountOut = toBase18(1.0)
    swapFee = 0
    x = pool.calcInGivenOut(
        tokenBalanceIn,
        tokenWeightIn,
        tokenBalanceOut,
        tokenWeightOut,
        tokenAmountOut,
        swapFee,
    )
    assert round(fromBase18(x), 3) == 1.099


def test_calcPoolOutGivenSingleIn():
    pool = _deployBPool()
    tokenBalanceIn = toBase18(10.0)
    tokenWeightIn = toBase18(1.0)
    poolSupply = toBase18(120.0)
    totalWeight = toBase18(2.0)
    tokenAmountIn = toBase18(0.1)
    swapFee = 0
    x = pool.calcPoolOutGivenSingleIn(
        tokenBalanceIn, tokenWeightIn, poolSupply, totalWeight, tokenAmountIn, swapFee
    )
    assert round(fromBase18(x), 3) == 0.599


def test_calcSingleInGivenPoolOut():
    pool = _deployBPool()
    tokenBalanceIn = toBase18(10.0)
    tokenWeightIn = toBase18(1.0)
    poolSupply = toBase18(120.0)
    totalWeight = toBase18(2.0)
    poolAmountOut = toBase18(10.0)
    swapFee = 0
    x = pool.calcSingleInGivenPoolOut(
        tokenBalanceIn, tokenWeightIn, poolSupply, totalWeight, poolAmountOut, swapFee
    )
    assert round(fromBase18(x), 3) == 1.736


def test_calcSingleOutGivenPoolIn():
    pool = _deployBPool()
    tokenBalanceOut = toBase18(10.0)
    tokenWeightOut = toBase18(1.0)
    poolSupply = toBase18(120.0)
    totalWeight = toBase18(2.0)
    poolAmountIn = toBase18(10.0)
    swapFee = 0
    x = pool.calcSingleOutGivenPoolIn(
        tokenBalanceOut, tokenWeightOut, poolSupply, totalWeight, poolAmountIn, swapFee
    )
    assert round(fromBase18(x), 3) == 1.597


def test_calcPoolInGivenSingleOut():
    pool = _deployBPool()
    tokenBalanceOut = toBase18(1000.0)
    tokenWeightOut = toBase18(5.0)
    poolSupply = toBase18(100.0)
    totalWeight = toBase18(10.0)
    tokenAmountOut = toBase18(0.1)
    swapFee = 0
    x = pool.calcPoolInGivenSingleOut(
        tokenBalanceOut,
        tokenWeightOut,
        poolSupply,
        totalWeight,
        tokenAmountOut,
        swapFee,
    )
    assert round(fromBase18(x), 3) == 0.005


def _createPoolWith2Tokens(
    T1, T2, bal1: float, bal2: float, w1: float, w2: float
):  # pylint: disable=too-many-arguments
    pool = _deployBPool()

    T1.approve(pool.address, toBase18(bal1), {"from": account0})
    T2.approve(pool.address, toBase18(bal2), {"from": account0})

    assert T1.balanceOf(address0) >= toBase18(bal1)
    assert T2.balanceOf(address0) >= toBase18(bal2)
    pool.bind(T1.address, toBase18(bal1), toBase18(w1), {"from": account0})
    pool.bind(T2.address, toBase18(bal2), toBase18(w2), {"from": account0})

    return pool


def _deployBPool():
    return sol057.contracts.oceanv3.oceanv3util.newBPool(account0)
