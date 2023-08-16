import brownie
from enforce_typing import enforce_types

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT057, GOD_ACCOUNT
from util.tx import txdict

GOD_ADDRESS = GOD_ACCOUNT.address

# ===============================================================
# datatokens: template, factory, creation
@enforce_types
def templateDatatoken():
    return BROWNIE_PROJECT057.DataTokenTemplate.deploy(
        "TT",
        "TemplateToken",
        GOD_ADDRESS,
        toBase18(1e3),
        "blob",
        GOD_ADDRESS,
        txdict(GOD_ACCOUNT),
    )


_DTFACTORY = None


@enforce_types
def DTFactory():
    global _DTFACTORY  # pylint: disable=global-statement
    try:
        dt = templateDatatoken()
        factory = _DTFACTORY  # may trigger failure
        if factory is not None:
            x = factory.address  # "" #pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        factory = None
    if factory is None:
        factory = _DTFACTORY = BROWNIE_PROJECT057.DTFactory.deploy(
            dt.address, GOD_ACCOUNT, txdict(GOD_ACCOUNT)
        )
    return factory


@enforce_types
def dtAddressFromCreateTokenTx(tx):
    return tx.events["TokenCreated"]["newTokenAddress"]


@enforce_types
def newDatatoken(blob: str, name: str, symbol: str, cap: int, account):
    f = DTFactory()
    tx = f.createToken(blob, name, symbol, cap, txdict(account))
    dt_address = dtAddressFromCreateTokenTx(tx)
    dt = BROWNIE_PROJECT057.DataTokenTemplate.at(dt_address)
    return dt


# ===============================================================
# pools: template, factory, creation
@enforce_types
def templatePool():
    return BROWNIE_PROJECT057.BPool.deploy(txdict(GOD_ACCOUNT))


_BFACTORY = None


@enforce_types
def BFactory():
    global _BFACTORY  # pylint: disable=global-statement
    try:
        pool = templatePool()
        factory = _BFACTORY  # may trigger failure
        if factory is not None:
            x = factory.address  # "" #pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        factory = None
    if factory is None:
        factory = _BFACTORY = BROWNIE_PROJECT057.BFactory.deploy(
            pool.address, txdict(GOD_ACCOUNT)
        )
    return factory


@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events["BPoolCreated"]["newBPoolAddress"]


@enforce_types
def newBPool(account):
    bfactory = BFactory()
    tx = bfactory.newBPool(txdict(account))
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT057.BPool.at(pool_address)
    return pool
