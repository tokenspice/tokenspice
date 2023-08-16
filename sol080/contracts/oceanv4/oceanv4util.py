from typing import Any, List
from enforce_typing import enforce_types

import brownie

from util.base18 import toBase18
from util.constants import (
    BROWNIE_PROJECT080,
    GOD_ACCOUNT,
    ZERO_ADDRESS,
    OPF_ADDRESS,
)
from util.globaltokens import OCEANtoken
from util.tx import txdict

_ERC721_TEMPLATE = None


@enforce_types
def ERC721Template():
    global _ERC721_TEMPLATE  # pylint: disable=global-statement
    try:
        erc721_template = _ERC721_TEMPLATE  # may trigger failure
        if erc721_template is not None:
            x = erc721_template.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        erc721_template = None
    if erc721_template is None:
        _ERC721_TEMPLATE = BROWNIE_PROJECT080.ERC721Template.deploy(
            txdict(GOD_ACCOUNT)
        )
        erc721_template = _ERC721_TEMPLATE
    return erc721_template


_ERC20_TEMPLATE = None


@enforce_types
def ERC20Template():
    global _ERC20_TEMPLATE  # pylint: disable=global-statement
    try:
        erc20_template = _ERC20_TEMPLATE  # may trigger failure
        if erc20_template is not None:
            x = erc20_template.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        erc20_template = None
    if erc20_template is None:
        _ERC20_TEMPLATE = BROWNIE_PROJECT080.ERC20Template.deploy(txdict(GOD_ACCOUNT))
        erc20_template = _ERC20_TEMPLATE
    return erc20_template


_POOL_TEMPLATE = None


@enforce_types
def POOLTemplate():
    global _POOL_TEMPLATE  # pylint: disable=global-statement
    try:
        pool_template = _POOL_TEMPLATE  # may trigger failure
        if pool_template is not None:
            x = pool_template.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        pool_template = None
    if pool_template is None:
        _POOL_TEMPLATE = BROWNIE_PROJECT080.BPool.deploy(txdict(GOD_ACCOUNT))
        pool_template = _POOL_TEMPLATE

    return pool_template


@enforce_types
def deployRouter(from_account):
    OCEAN = OCEANtoken()
    pool_template = POOLTemplate()
    router = BROWNIE_PROJECT080.FactoryRouter.deploy(
        from_account.address,
        OCEAN.address,
        pool_template,
        OPF_ADDRESS,
        [],
        txdict(from_account),
    )
    return router


@enforce_types
def deployERC721Factory(from_account, router):
    erc721_template = ERC721Template()
    erc20_template = ERC20Template()
    factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721_template.address,
        erc20_template.address,
        OPF_ADDRESS,
        router.address,
        txdict(from_account),
    )
    return factory


@enforce_types
def createDataNFT(name: str, symbol: str, from_account, router):
    erc721_factory = deployERC721Factory(from_account, router)
    erc721_template_index = 1
    token_URI = "https://mystorage.com/mytoken.png"
    tx = erc721_factory.deployERC721Contract(
        name,
        symbol,
        erc721_template_index,
        router.address,
        ZERO_ADDRESS,  # additionalMetaDataUpdater set to 0x00 for now
        token_URI,
        txdict(from_account),
    )
    data_NFT_address = tx.events["NFTCreated"]["newTokenAddress"]
    data_NFT = BROWNIE_PROJECT080.ERC721Template.at(data_NFT_address)
    return (data_NFT, erc721_factory)


@enforce_types
def createDatatokenFromDataNFT(
    DT_name: str, DT_symbol: str, DT_cap: int, dataNFT, from_account
):

    erc20_template_index = 1
    strings = [
        DT_name,
        DT_symbol,
    ]
    addresses = [
        from_account.address,  # minter
        from_account.address,  # fee mgr
        from_account.address,  # pub mkt
        ZERO_ADDRESS,  # pub mkt fee token addr
    ]
    uints = [
        toBase18(DT_cap),
        toBase18(0.0),  # pub mkt fee amt
    ]
    _bytes: List[Any] = []

    tx = dataNFT.createERC20(
        erc20_template_index, strings, addresses, uints, _bytes, txdict(from_account)
    )
    DT_address = tx.events["TokenCreated"]["newTokenAddress"]
    DT = BROWNIE_PROJECT080.ERC20Template.at(DT_address)

    return DT


@enforce_types
def deploySideStaking(from_account, router):
    return BROWNIE_PROJECT080.SideStaking.deploy(router.address, txdict(from_account))


@enforce_types
def createBPoolFromDatatoken(
    datatoken,
    erc721_factory,
    from_account,
    OCEAN_init_liquidity=2000,
    DT_OCEAN_rate=0.1,
    DT_vest_amt=1000,
    DT_vest_num_blocks=600,
    LP_swap_fee=0.03,
    mkt_swap_fee=0.01,
): #pylint: disable=too-many-arguments

    OCEAN = OCEANtoken()
    pool_template = POOLTemplate()

    router_address = datatoken.router()
    router = BROWNIE_PROJECT080.FactoryRouter.at(router_address)
    router.updateMinVestingPeriod(500, txdict(from_account))

    OCEAN.approve(
        router.address, toBase18(OCEAN_init_liquidity), txdict(from_account)
    )

    ssbot = deploySideStaking(from_account, router)
    router.addSSContract(ssbot.address, txdict(from_account))
    router.addFactory(erc721_factory.address, txdict(from_account))

    ss_params = [
        toBase18(DT_OCEAN_rate),
        OCEAN.decimals(),
        toBase18(DT_vest_amt),
        DT_vest_num_blocks,  # do _not_ convert to wei
        toBase18(OCEAN_init_liquidity),
    ]
    swap_fees = [
        toBase18(LP_swap_fee),
        toBase18(mkt_swap_fee),
    ]
    addresses = [
        ssbot.address,
        OCEAN.address,
        from_account.address,
        from_account.address,
        OPF_ADDRESS,
        pool_template.address,
    ]

    tx = datatoken.deployPool(ss_params, swap_fees, addresses, txdict(from_account))
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)

    return pool


@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events["NewPool"]["poolAddress"]
