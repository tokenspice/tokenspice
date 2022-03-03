import brownie
from enforce_typing import enforce_types

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, GOD_ACCOUNT, ZERO_ADDRESS, \
    OPF_ACCOUNT, OPF_ADDRESS
from util.globaltokens import OCEANtoken, fundOCEANFromAbove

_ERC721_TEMPLATE = None


@enforce_types
def ERC721Template():
    global _ERC721_TEMPLATE  # pylint: disable=global-statement
    try:
        erc721template = _ERC721_TEMPLATE  # may trigger failure
        if erc721template is not None:
            x = erc721template.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        erc721template = None
    if erc721template is None:
        erc721template = _ERC721_TEMPLATE = BROWNIE_PROJECT080.ERC721Template.deploy(
            {"from": GOD_ACCOUNT}
        )
    return erc721template


_ERC20_TEMPLATE = None


@enforce_types
def ERC20Template():
    global _ERC20_TEMPLATE  # pylint: disable=global-statement
    try:
        erc20template = _ERC20_TEMPLATE  # may trigger failure
        if erc20template is not None:
            x = erc20template.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        erc20template = None
    if erc20template is None:
        erc20template = _ERC20_TEMPLATE = BROWNIE_PROJECT080.ERC20Template.deploy(
            {"from": GOD_ACCOUNT}
        )
    return erc20template


_POOL_TEMPLATE = None


@enforce_types
def POOLTemplate():
    global _POOL_TEMPLATE  # pylint: disable=global-statement
    try:
        pooltemplate = _POOL_TEMPLATE  # may trigger failure
        if pooltemplate is not None:
            x = pooltemplate.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        pooltemplate = None
    if pooltemplate is None:
        pooltemplate = _POOL_TEMPLATE = BROWNIE_PROJECT080.BPool.deploy(
            {"from": GOD_ACCOUNT}
        )
    return pooltemplate


@enforce_types
def deployRouter(account):
    oceanToken = OCEANtoken()
    poolTemplate = POOLTemplate()
    return BROWNIE_PROJECT080.FactoryRouter.deploy(
        account.address,
        oceanToken.address,
        poolTemplate,
        OPF_ADDRESS,
        [],
        {"from": account},
    )


@enforce_types
def deployERC721Factory(account, router):
    erc721Template = ERC721Template()
    erc20Template = ERC20Template()
    return BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721Template.address,
        erc20Template.address,
        OPF_ADDRESS,
        router.address,
        {"from": account},
    )


@enforce_types
def createDataNFT(
    name: str,
    symbol: str,
    account,
    router,
):
    erc721_factory = deployERC721Factory(account, router)
    erc721_template_index = 1
    token_URI = "https://mystorage.com/mytoken.png"
    tx = erc721_factory.deployERC721Contract(
        name,
        symbol,
        erc721_template_index,
        router.address,
        ZERO_ADDRESS, # additionalMetaDataUpdater set to 0x00 for now
        token_URI,
        {"from": account},
    )
    dataNFT1_address = tx.events["NFTCreated"]["newTokenAddress"]
    return BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address), erc721_factory


@enforce_types
def createDatatokenFromDataNFT(DT_name, DT_symbol, DT_cap, dataNFT, account):
    erc20_template_index = 1
    strings = [
        DT_name,
        DT_symbol,
    ]
    addresses = [
        account.address, # minter
        account.address, # fee mgr
        account.address, # pub mkt
        ZERO_ADDRESS,    # pub mkt fee token addr
    ]   
    uints = [
        toBase18(DT_cap),
        toBase18(0.0), # pub mkt fee amt
    ]
    _bytes = []

    tx = dataNFT.createERC20(
        erc20_template_index, strings, addresses, uints, _bytes,
        {"from": account})
    
    DT_address = tx.events["TokenCreated"]["newTokenAddress"]
    DT = BROWNIE_PROJECT080.ERC20Template.at(DT_address)

    return DT


@enforce_types
def deploySideStaking(account, router):
    return BROWNIE_PROJECT080.SideStaking.deploy(
        router.address, {"from": account})


@enforce_types
def createBPoolFromDatatoken(
        datatoken, DT_vest_amt, OCEAN_init_liquidity, account, erc721_factory,
        LP_swap_fee = 0.03, mkt_swap_fee = 0.01
):
        
    OCEAN = OCEANtoken()
    poolTemplate = POOLTemplate()
    
    router_address = datatoken.router()
    router = BROWNIE_PROJECT080.FactoryRouter.at(router_address)
    router.updateMinVestingPeriod(500, {"from":account})

    OCEAN.approve(
        router.address, toBase18(OCEAN_init_liquidity), {"from": account})
    
    ss_bot = deploySideStaking(account, router)
    router.addSSContract(ss_bot.address, {"from": account})
    router.addFactory(erc721_factory.address, {"from": account})

    ss_params = [
        toBase18(0.1),         # rate (wei)
        18,                    # OCEAN decimals
        toBase18(DT_vest_amt), # vesting amount (wei)
        600,                   # vested blocks
        toBase18(OCEAN_init_liquidity),
        ]
    swap_fees = [
        toBase18(LP_swap_fee), #LP swap fee
        toBase18(mkt_swap_fee), #mkt swap fee
    ]
    addresses = [
        ss_bot.address, OCEAN.address, account.address, account.address,
        OPF_ADDRESS, poolTemplate.address]

    tx = datatoken.deployPool(
        ss_params, swap_fees, addresses, {"from": account})
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)
    
    return pool


@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events["NewPool"]["poolAddress"]
