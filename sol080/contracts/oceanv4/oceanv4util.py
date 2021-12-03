import brownie
from enforce_typing import enforce_types

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, GOD_ACCOUNT, OPF_ACCOUNT

GOD_ADDRESS = GOD_ACCOUNT.address
OPF_ADDRESS = OPF_ACCOUNT.address

OPFCommunityFeeCollector = BROWNIE_PROJECT080.OPFCommunityFeeCollector

# ===============================================================
# datatokens: template, factory, creation
@enforce_types
def templateDatatoken():
    return BROWNIE_PROJECT080.V3DataTokenTemplate.deploy(
        "TT",
        "TemplateToken",
        GOD_ADDRESS,
        toBase18(1e3),
        "blob",
        GOD_ADDRESS,
        {"from": GOD_ACCOUNT},
    )


_DTFACTORY = None


@enforce_types
def DTFactory():
    global _DTFACTORY
    try:
        dt = templateDatatoken()
        factory = _DTFACTORY  # may trigger failure
        if factory is not None:
            x = factory.address  # ""
    except brownie.exceptions.ContractNotFound:
        factory = None
    if factory is None:
        factory = _DTFACTORY = BROWNIE_PROJECT080.V3DTFactory.deploy(
            dt.address, GOD_ADDRESS, {"from": GOD_ACCOUNT}
        )
    return factory


@enforce_types
def dtAddressFromCreateTokenTx(tx):
    return tx.events["TokenCreated"]["newTokenAddress"]


@enforce_types
def newDatatoken(blob: str, name: str, symbol: str, cap: int, account):
    f = DTFactory()
    tx = f.createToken(blob, name, symbol, cap, {"from": account})
    dt_address = dtAddressFromCreateTokenTx(tx)
    dt = BROWNIE_PROJECT080.V3DataTokenTemplate.at(dt_address)
    return dt


# ===============================================================
# pools: template, factory, creation
@enforce_types
def templatePool():
    return BROWNIE_PROJECT080.BPool.deploy({"from": GOD_ACCOUNT})


_BFACTORY = None


@enforce_types
def BFactory():
    global _BFACTORY
    try:
        pool = templatePool()
        factory = _BFACTORY  # may trigger failure
        if factory is not None:
            x = factory.address  # ""
    except brownie.exceptions.ContractNotFound:
        factory = None
    if factory is None:
        factory = _BFACTORY = BROWNIE_PROJECT080.BFactory.deploy(
            pool.address, 
            OPF_ADDRESS,
            # [GOD_ADDRESS],
            {"from": GOD_ACCOUNT}
        )
    return factory


@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events["BPoolCreated"]["newBPoolAddress"]


@enforce_types
def newBPool(account):
    bfactory = BFactory()
    tx = bfactory.newBPool({"from": account})
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)
    return pool


@enforce_types
def templateNFT():
    return BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": GOD_ACCOUNT}
    )
