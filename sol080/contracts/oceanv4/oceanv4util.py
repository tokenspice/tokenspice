import brownie
from enforce_typing import enforce_types

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, GOD_ACCOUNT, OPF_ACCOUNT, ZERO_ADDRESS
from util.globaltokens import OCEANtoken, fundOCEANFromAbove

GOD_ADDRESS = GOD_ACCOUNT.address
OPF_ADDRESS = OPF_ACCOUNT.address

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


_ERC721FACTORY = None


@enforce_types
def ERC721Factory(additional_NFT_deployer_address):
    global _ERC721FACTORY  # pylint: disable=global-statement
    try:
        erc721Template = ERC721Template()
        erc20Template = ERC20Template()
        factory = _ERC721FACTORY  # may trigger failure
        if factory is not None:
            x = factory.address  # "" #pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        factory = None
    if factory is None:
        factory = _ERC721FACTORY = BROWNIE_PROJECT080.ERC721Factory.deploy(
            erc721Template.address,
            erc20Template.address,
            OPF_ADDRESS,
            additional_NFT_deployer_address,
            {"from": GOD_ACCOUNT},
        )
    return factory



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


_ROUTER = None


@enforce_types
def ROUTER():
    global _ROUTER  # pylint: disable=global-statement
    try:
        oceanToken = OCEANtoken()
        poolTemplate = POOLTemplate()
        router = _ROUTER  # may trigger failure
        if router is not None:
            x = router.address  # "" #pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        router = None
    if router is None:
        router = _ROUTER = BROWNIE_PROJECT080.FactoryRouter.deploy(
            GOD_ADDRESS,
            oceanToken.address,
            poolTemplate,
            OPF_ADDRESS,
            [],
            {"from": GOD_ACCOUNT},
        )
    return router


_SIDE_STAKING = None


@enforce_types
def SIDESTAKING():
    global _SIDE_STAKING  # pylint: disable=global-statement
    try:
        ss = _SIDE_STAKING  # may trigger failure
        if ss is not None:
            x = ss.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        ss = None
    if ss is None:
        router = ROUTER()
        ss = _SIDE_STAKING = BROWNIE_PROJECT080.SideStaking.deploy(
            router.address, {"from": GOD_ACCOUNT}
        )
    return ss


@enforce_types
def createDataNFT(
    name: str,
    symbol: str,
    account,
    additional_NFT_deployer_address=GOD_ADDRESS,
):
    erc721_factory = ERC721Factory(additional_NFT_deployer_address)
    erc721_template_index = 1
    additional_NFT_deployer_address = ZERO_ADDRESS
    token_URI = "https://mystorage.com/mytoken.png"
    tx = erc721_factory.deployERC721Contract(
        name,
        symbol,
        erc721_template_index,
        additional_NFT_deployer_address,
        token_URI,
        {"from": account},
    )
    dataNFT1_address = tx.events["NFTCreated"]["newTokenAddress"]
    return BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address)


@enforce_types
def create_datatoken_from_dataNFT(DT_name, DT_symbol, DT_cap, dataNFT, account):
    erc20_template_index = 1  # refer to erc20_template
    strings = [DT_name, DT_symbol]
    minter_addr = fee_mgr_addr = pub_mkt_addr = account.address
    pub_mkt_fee_token_addr = ZERO_ADDRESS
    pub_mkt_fee_amt = 0.0  # in OCEAN
    uints = [toBase18(DT_cap), toBase18(pub_mkt_fee_amt)]
    addresses = [minter_addr, fee_mgr_addr, pub_mkt_addr, pub_mkt_fee_token_addr]
    bytes = []

    tx = dataNFT.createERC20(
        erc20_template_index, strings, addresses, uints, bytes, {"from": account}
    )
    DT_address = tx.events["TokenCreated"]["newTokenAddress"]
    return BROWNIE_PROJECT080.ERC20Template.at(DT_address)


@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events["NewPool"]["poolAddress"]


@enforce_types
def create_BPool_from_datatoken(
    datatoken, DT_vest_amount, OCEAN_init_liquidity, account
):
    router = ROUTER()
    if router.routerOwner() == GOD_ADDRESS:
        router.changeRouterOwner(account.address, {"from": GOD_ACCOUNT})
    OCEAN = OCEANtoken()
    poolTemplate = POOLTemplate()
    erc721_factory = ERC721Factory(router.address)

    sideStaking = SIDESTAKING()
    router.addSSContract(sideStaking.address, {"from": account})
    router.addFactory(erc721_factory.address, {"from": account})

    ss_rate = 0.1
    ss_OCEAN_decimals = 18
    ss_DT_vest_amt = DT_vest_amount  # max 10% but 10000 gives error
    ss_DT_vested_blocks = 2500000  # = num blocks/year, if 15 s/block
    ss_OCEAN_init_liquidity = OCEAN_init_liquidity
    
    OCEAN.approve(router.address, toBase18(ss_OCEAN_init_liquidity), {"from": account})

    LP_swap_fee = 0.02
    mkt_swap_fee = 0.01
    pool_create_data = {
        "addresses": [
            sideStaking.address,
            OCEAN.address,
            account.address,
            account.address,
            OPF_ADDRESS,
            poolTemplate.address,
        ],
        "ssParams": [
            toBase18(ss_rate),
            ss_OCEAN_decimals,
            toBase18(ss_DT_vest_amt),
            ss_DT_vested_blocks,
            toBase18(ss_OCEAN_init_liquidity),
        ],
        "swapFees": [toBase18(LP_swap_fee), toBase18(mkt_swap_fee)],
    }

    tx = datatoken.deployPool(
        pool_create_data["ssParams"],
        pool_create_data["swapFees"],
        pool_create_data["addresses"],
        {"from": account},
    )
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)
    return pool
