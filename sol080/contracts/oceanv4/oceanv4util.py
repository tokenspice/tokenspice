from os import access
import brownie
from enforce_typing import enforce_types
# from sol080.contracts.oceanv4.test.test_SideStaking import OPF_ADDRESS

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, GOD_ACCOUNT, OPF_ACCOUNT, ZERO_ADDRESS

GOD_ADDRESS = GOD_ACCOUNT.address
OPF_ADDRESS = OPF_ACCOUNT.address

@enforce_types
def erc721_template():
    return BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": GOD_ACCOUNT}
    )

@enforce_types
def erc20_template():
    return BROWNIE_PROJECT080.ERC20Template.deploy(
        {"from": GOD_ACCOUNT}
    )

_OCEAN_TOKEN = None
@enforce_types
def OCEANtoken():
    global _OCEAN_TOKEN  # pylint: disable=global-statement
    try:
        token = _OCEAN_TOKEN  # may trigger failure
        if token is not None:
            x = token.address  # "" # pylint: disable=unused-variable
    except brownie.exceptions.ContractNotFound:
        token = None
    if token is None:
        token = _OCEAN_TOKEN = BROWNIE_PROJECT080.MockOcean.deploy(
            GOD_ADDRESS, {"from":GOD_ACCOUNT}
        )
    return token


@enforce_types
def OCEAN_address() -> str:
    return OCEANtoken().address


@enforce_types
def fundOCEANFromAbove(dst_address: str, amount_base: int):
    OCEANtoken().transfer(dst_address, amount_base, {"from": GOD_ACCOUNT})

@enforce_types
def pool_template():
    return BROWNIE_PROJECT080.BPool.deploy({'from': GOD_ACCOUNT})

@enforce_types
def deploy_router(account):
    oceanToken = OCEANtoken()
    poolTemplate = pool_template()
    router = BROWNIE_PROJECT080.FactoryRouter.deploy(
        account.address,
        oceanToken.address,
        poolTemplate,
        OPF_ADDRESS,
        [],
        {'from': GOD_ACCOUNT}
    )
    return router, oceanToken, poolTemplate

@enforce_types
def createDataNFT(
        name: str, symbol: str, account, additional_NFT_deployer_address = GOD_ADDRESS
    ):
    
    erc721Template = erc721_template()
    erc20Template = erc20_template()

    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721Template.address,
        erc20Template.address,
        OPF_ADDRESS,
        additional_NFT_deployer_address,
        {"from":account}
    )
    erc721_template_index = 1
    additional_NFT_deployer_address = ZERO_ADDRESS
    token_URI = "https://mystorage.com/mytoken.png"
    tx = erc721_factory.deployERC721Contract(
        name,
        symbol,
        erc721_template_index,
        additional_NFT_deployer_address,
        token_URI,
        {"from":account}
    )
    dataNFT1_address = tx.events["NFTCreated"]["newTokenAddress"]
    return BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address), erc721_factory

@enforce_types
def createDatatoken(
    DT_name, DT_symbol, DT_cap, account, dataNFT
    ):
    erc20_template_index = 1 #refer to erc20_template
    strings = [DT_name, DT_symbol]
    minter_addr = fee_mgr_addr = pub_mkt_addr = account.address
    pub_mkt_fee_token_addr = ZERO_ADDRESS
    pub_mkt_fee_amt = 0.0 # in OCEAN
    uints = [toBase18(DT_cap), toBase18(pub_mkt_fee_amt)] 
    addresses = [minter_addr, fee_mgr_addr, pub_mkt_addr, pub_mkt_fee_token_addr]
    bytes = []

    tx = dataNFT.createERC20(
        erc20_template_index,
        strings,
        addresses,
        uints,
        bytes,
        {"from":account}
    )
    DT_address = tx.events['TokenCreated']['newTokenAddress']
    return BROWNIE_PROJECT080.ERC20Template.at(DT_address)

@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events["NewPool"]["poolAddress"]

@enforce_types
def createBPool(account):
    deployed_router = deploy_router(account)
    router = deployed_router[0]
    OCEANtoken = deployed_router[1]
    poolTemplate = deployed_router[2]    

    NFT_creation = createDataNFT("dataNFT", "DATANFT", account, additional_NFT_deployer_address=router.address)
    dataNFT = NFT_creation[0]
    erc721_factory = NFT_creation[1]

    datatoken = createDatatoken("DT", "DTSymbol", 1000.0, account, dataNFT=dataNFT)
    
    sideStaking = BROWNIE_PROJECT080.SideStaking.deploy(
        router.address, {'from': GOD_ACCOUNT}
    )
    router.addSSContract(sideStaking.address, {"from": account})
    router.addFactory(erc721_factory.address, {'from': account})

    OCEANtoken.transfer(account, toBase18(10000.0), {"from": GOD_ACCOUNT})
    ss_rate = 0.1
    ss_OCEAN_decimals = 18
    ss_DT_vest_amt = 10.0 #max 10% but 10000 gives error
    ss_DT_vested_blocks = 2500000 # = num blocks/year, if 15 s/block
    ss_OCEAN_init_liquidity = 100.0

    LP_swap_fee = 0.001 # 1%
    mkt_swap_fee = 0.001 # 1%
    pool_create_data = {
        "addresses": [
            sideStaking.address, OCEANtoken.address, account.address,
            account.address, OPF_ADDRESS, poolTemplate.address
        ],
        "ssParams": [
            toBase18(ss_rate), ss_OCEAN_decimals,
            toBase18(ss_DT_vest_amt), ss_DT_vested_blocks,
            toBase18(ss_OCEAN_init_liquidity)
        ],
        "swapFees": [toBase18(LP_swap_fee), toBase18(mkt_swap_fee)],
    }

    OCEANtoken.approve(router.address, toBase18(ss_OCEAN_init_liquidity),{'from': account})

    tx = datatoken.deployPool(
        pool_create_data["ssParams"],
        pool_create_data["swapFees"],
        pool_create_data["addresses"],
        {"from":account}
    )
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)
    return pool