import brownie

import sol080.contracts.oceanv4.oceanv4util
from util.constants import BROWNIE_PROJECT080

account0 = brownie.network.accounts[0]


def test_direct():
    templatepool = BROWNIE_PROJECT080.BPool.deploy({"from": account0})

    bfactory = BROWNIE_PROJECT080.BFactory.deploy(
        templatepool.address, {"from": account0}
    )

    tx = bfactory.newBPool({"from": account0})
    pool_address = tx.events["BPoolCreated"]["newBPoolAddress"]
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)
    assert pool.address == pool_address
    assert pool.isFinalized() in [False, True]


def test_via_BFactory_util():
    bfactory = sol080.contracts.oceanv4.oceanv4util.BFactory()
    tx = bfactory.newBPool({"from": account0})

    pool_address = sol080.contracts.oceanv4.oceanv4util.poolAddressFromNewBPoolTx(tx)
    assert pool_address == tx.events["BPoolCreated"]["newBPoolAddress"]

    pool = BROWNIE_PROJECT080.BPool.at(pool_address)
    assert pool.address == pool_address
    assert pool.isFinalized() in [False, True]


def test_via_newBPool_util():
    pool = sol080.contracts.oceanv3.oceanv3util.newBPool(account0)
    assert pool.isFinalized() in [False, True]
