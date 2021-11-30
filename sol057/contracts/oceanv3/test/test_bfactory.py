import brownie

import sol057.contracts.oceanv3.oceanv3util
from util.constants import BROWNIE_PROJECT057

account0 = brownie.network.accounts[0]


def test_direct():
    templatepool = BROWNIE_PROJECT057.BPool.deploy({"from": account0})

    bfactory = BROWNIE_PROJECT057.BFactory.deploy(
        templatepool.address, {"from": account0}
    )

    tx = bfactory.newBPool({"from": account0})
    pool_address = tx.events["BPoolCreated"]["newBPoolAddress"]
    pool = BROWNIE_PROJECT057.BPool.at(pool_address)
    assert pool.address == pool_address
    assert pool.isFinalized() in [False, True]


def test_via_BFactory_util():
    bfactory = sol057.contracts.oceanv3.oceanv3util.BFactory()
    tx = bfactory.newBPool({"from": account0})

    pool_address = sol057.contracts.oceanv3.oceanv3util.poolAddressFromNewBPoolTx(tx)
    assert pool_address == tx.events["BPoolCreated"]["newBPoolAddress"]

    pool = BROWNIE_PROJECT057.BPool.at(pool_address)
    assert pool.address == pool_address
    assert pool.isFinalized() in [False, True]


def test_via_newBPool_util():
    pool = sol057.contracts.oceanv3.oceanv3util.newBPool(account0)
    assert pool.isFinalized() in [False, True]
