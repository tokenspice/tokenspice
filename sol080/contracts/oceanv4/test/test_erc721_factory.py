import brownie
from sol080.contracts.oceanv4.oceanv4util import (
    POOLTemplate,
    deployRouter,
    createDataNFT,
    createDatatokenFromDataNFT,
    createBPoolFromDatatoken,
    poolAddressFromNewBPoolTx, 
    deploySideStaking
)
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT, GOD_ACCOUNT, ZERO_ADDRESS
from util.globaltokens import fundOCEANFromAbove, OCEANtoken

accounts = brownie.network.accounts
account0 = accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address


def test_direct():
    erc721_template = BROWNIE_PROJECT080.ERC721Template.deploy({"from": GOD_ACCOUNT})

    erc20_template = BROWNIE_PROJECT080.ERC20Template.deploy({"from": GOD_ACCOUNT})
    OCEANtoken = BROWNIE_PROJECT080.MockOcean.deploy(address0, {"from": GOD_ACCOUNT})
    OCEAN_address = OCEANtoken.address
    pool_template = BROWNIE_PROJECT080.BPool.deploy({"from": GOD_ACCOUNT})

    # DEPLOY ROUTER, SETTING OWNER
    router = BROWNIE_PROJECT080.FactoryRouter.deploy(
        address0,
        OCEAN_address,
        pool_template.address,
        OPF_ADDRESS,
        [],
        {"from": GOD_ACCOUNT},
    )

    # SETUP ERC721 Factory with template
    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721_template.address,
        erc20_template.address,
        OPF_ADDRESS,
        router.address,
        {"from": account0},
    )

    assert erc721_factory.owner() == address0

    current_nft_count = erc721_factory.getCurrentNFTCount()

    # 1 Publisher deployERC721Contract
    erc721_template_index = 1  # refer to erc721_template
    additional_NFT_deployer_address = ZERO_ADDRESS
    token_URI = "https://mystorage.com/mytoken.png"
    tx = erc721_factory.deployERC721Contract(
        "dataNFT1",
        "DATANFT1",
        erc721_template_index,
        additional_NFT_deployer_address,
        token_URI,
        {"from": account0},
    )

    assert tx.events["NFTCreated"] is not None
    assert tx.events["NFTCreated"]["admin"] == address0

    # ERC721 token
    dataNFT1_address = tx.events["NFTCreated"]["newTokenAddress"]
    dataNFT1 = BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address)

    assert dataNFT1.name() == "dataNFT1"
    assert dataNFT1.symbol() == "DATANFT1"

    # Tests current NFT count
    assert erc721_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template = erc721_factory.getNFTTemplate(1)
    assert nft_template[0] == erc721_template.address
    assert nft_template[1] is True

    # 2: Publisher createERC20
    erc20_template_index = 1  # refer to erc20_template
    DT_name, DT_symbol = "datatoken1", "DT1"
    strings = [DT_name, DT_symbol]
    minter_addr = fee_mgr_addr = pub_mkt_addr = address0
    pub_mkt_fee_token_addr = ZERO_ADDRESS
    DT_cap = 100000
    pub_mkt_fee_amt = 0.0  # in OCEAN
    uints = [toBase18(DT_cap), toBase18(pub_mkt_fee_amt)]
    addresses = [minter_addr, fee_mgr_addr, pub_mkt_addr, pub_mkt_fee_token_addr]
    bytes = []
    tx = dataNFT1.createERC20(
        erc20_template_index, strings, addresses, uints, bytes, {"from": account0}
    )

    DT_address = tx.events["TokenCreated"]["newTokenAddress"]
    DT = BROWNIE_PROJECT080.ERC20Template.at(DT_address)

    assert DT.name() == DT_name
    assert DT.symbol() == DT_symbol
    assert DT.cap() == toBase18(DT_cap)

    # Tests ERC20 token template list
    assert erc721_factory.getTokenTemplate(1)[0] == erc20_template.address
    assert erc721_factory.getTokenTemplate(1)[1] == True

    # Tests balanceOf
    assert DT.balanceOf(address0) == 0

    # Once ERC20 DT has been created, publisher has 3 options:
    # Details here: https://github.com/oceanprotocol/contracts/blob/v4main_postaudit/docs/quickstart_pubFlow.md
    # 1. Create pool
    # 2. Mint DTs and create fixed price exchange
    # 3. Mint DTs and created pools on any other market

    # FOCUS on option 1
    # 3 Publisher creating bpool, from ERC20 datatoken
    sideStaking = BROWNIE_PROJECT080.SideStaking.deploy(
        router.address, {"from": GOD_ACCOUNT}
    )
    router.addSSContract(sideStaking.address, {"from": account0})
    router.addFactory(erc721_factory.address, {"from": account0})

    ss_rate = 0.1
    ss_OCEAN_decimals = 18
    ss_DT_vest_amt = 9999.0  # max 10% but 10000 gives error
    ss_DT_vested_blocks = 2500000  # = num blocks/year, if 15 s/block
    ss_OCEAN_init_liquidity = 2000.0

    LP_swap_fee = 0.02  # 2%
    mkt_swap_fee = 0.01  # 1%

    
    pool_create_data = {
        "addresses": [
            sideStaking.address,
            OCEAN_address,
            address0,
            address0,
            OPF_ADDRESS,
            pool_template.address,
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

    OCEANtoken.approve(
        router.address, toBase18(ss_OCEAN_init_liquidity), {"from": account0}
    )

    tx = DT.deployPool(
        pool_create_data["ssParams"],
        pool_create_data["swapFees"],
        pool_create_data["addresses"],
        {"from": account0},
    )
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)

    assert OCEANtoken.balanceOf(pool_address) == toBase18(ss_OCEAN_init_liquidity)
    assert pool.getMarketFee() == toBase18(mkt_swap_fee)
    assert pool.getSwapFee() == toBase18(LP_swap_fee)


def test_createDataNFT_via_util():
    router = deployRouter(account0)
    dataNFT = createDataNFT("dataNFT", "DATANFT", account0, router)
    createdDataNFT = createDataNFT("dataNFT", "DATANFT", account0, router)
    dataNFT = createdDataNFT[0]
    assert dataNFT.name() == "dataNFT"
    assert dataNFT.symbol() == "DATANFT"
    assert dataNFT.getPermissions(account0.address) == (True, True, True, True)
    assert dataNFT.balanceOf(account0.address) == 1


def test_createDT_via_util():
    router = deployRouter(account0)
    createdDataNFT = createDataNFT("dataNFT", "DATANFT", account0, router)
    dataNFT = createdDataNFT[0]
    DT = createDatatokenFromDataNFT("DT", "DTSymbol", 10000, dataNFT, account0)
    assert DT.name() == "DT"
    assert DT.symbol() == "DTSymbol"
    assert DT.cap() == toBase18(10000)
    assert DT.balanceOf(account0.address) == 0


def test_createBPool_via_util():
    brownie.chain.reset()
    router = deployRouter(account0)
    createdDataNFT = createDataNFT("dataNFT", "DATANFT", account0, router)
    dataNFT = createdDataNFT[0]
    erc721_factory = createdDataNFT[1]
    DT = createDatatokenFromDataNFT("DT", "DTSymbol", 10000, dataNFT, account0)    
    
    fundOCEANFromAbove(address0, toBase18(10000.0))
    OCEAN = OCEANtoken()
    pool = createBPoolFromDatatoken(DT, 100, 2000.0, account0, erc721_factory)
    pool_address = pool.address

    assert pool.getBaseTokenAddress() == OCEAN.address
    assert OCEAN.balanceOf(pool_address) < toBase18(10000.0)
    assert pool.getMarketFee() == toBase18(0.01)
    assert pool.getSwapFee() == toBase18(0.02)
