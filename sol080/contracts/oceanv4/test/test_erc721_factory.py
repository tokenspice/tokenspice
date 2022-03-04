import brownie
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, GOD_ACCOUNT, ZERO_ADDRESS, \
    OPF_ACCOUNT, OPF_ADDRESS
from sol080.contracts.oceanv4 import oceanv4util

accounts = brownie.network.accounts
account0 = accounts[0]
address0 = account0.address

def test_direct(): # pylint: disable=too-many-statements    
    # God deploys fake OCEAN token
    OCEANtoken = BROWNIE_PROJECT080.MockOcean.deploy(
        address0, {"from": GOD_ACCOUNT})
    OCEAN_address = OCEANtoken.address
    
    # God deploys templates
    erc721_template = BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": GOD_ACCOUNT})
    erc20_template = BROWNIE_PROJECT080.ERC20Template.deploy(
        {"from": GOD_ACCOUNT})
    pool_template = BROWNIE_PROJECT080.BPool.deploy({"from": GOD_ACCOUNT})

    # God deploys Factory Router
    router = BROWNIE_PROJECT080.FactoryRouter.deploy(
        address0, OCEAN_address, pool_template.address, OPF_ADDRESS,
        [], {"from": GOD_ACCOUNT})

    # God deploys ERC721 Factory, and reports it to the router
    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721_template.address, erc20_template.address,
        OPF_ADDRESS, router.address, {"from": account0})
    assert erc721_factory.owner() == address0
    current_nft_count = erc721_factory.getCurrentNFTCount()
    
    # Publisher creates ERC721 data NFT
    tx = erc721_factory.deployERC721Contract(
        "dataNFT1", "DATANFT1", 1, ZERO_ADDRESS, ZERO_ADDRESS,
        "https://mystorage.com/mytoken.png", {"from": account0})
    assert tx.events["NFTCreated"] is not None
    assert tx.events["NFTCreated"]["admin"] == address0
    dataNFT1_address = tx.events["NFTCreated"]["newTokenAddress"]
    dataNFT1 = BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address)
    assert dataNFT1.name() == "dataNFT1"
    assert dataNFT1.symbol() == "DATANFT1"
    
    assert erc721_factory.getCurrentNFTCount() == current_nft_count + 1

    nft_template = erc721_factory.getNFTTemplate(1)
    assert nft_template[0] == erc721_template.address
    assert nft_template[1]

    # Publisher creates ERC20 datatoken
    strings = ["datatoken1", "DT1"]
    DT_cap = 10000
    uints = [toBase18(DT_cap), toBase18(0.0)]
    addresses = [address0] * 4
    _bytes = []
    tx = dataNFT1.createERC20(
        1, strings, addresses, uints, _bytes, {"from": account0})

    DT_address = tx.events["TokenCreated"]["newTokenAddress"]
    DT = BROWNIE_PROJECT080.ERC20Template.at(DT_address)
    assert DT.name() == "datatoken1"
    assert DT.symbol() == "DT1"
    assert DT.cap() == toBase18(DT_cap)
    assert DT.balanceOf(address0) == 0
    assert erc721_factory.getTokenTemplate(1)[0] == erc20_template.address
    assert erc721_factory.getTokenTemplate(1)[1]

    # Now, the publisher has 3 options:
    # (a) Create pool
    # (b) Mint DTs and create fixed price exchange
    # (c) Mint DTs and create pools on any other market
    # Here, we do option (a)...

    # Publisher approves staking OCEAN
    OCEAN_init_liquidity = 2000.0
    OCEANtoken.approve(
        router.address, toBase18(OCEAN_init_liquidity), {"from": account0})

    # Publisher deploys 1-sided staking bot, reports info to router.
    ss_bot = BROWNIE_PROJECT080.SideStaking.deploy(
        router.address, {"from": GOD_ACCOUNT})
    router.addSSContract(ss_bot.address, {"from": account0})
    router.addFactory(erc721_factory.address, {"from": account0})

    # Publisher deploys pool, which includes a 1-sided staking bot
    ss_params = [
        toBase18(0.1),         # rate (wei)
        18,                    # OCEAN decimals
        toBase18(0.05*DT_cap), # vesting amount (wei)
        int(2.5e6),            # vested blocks
        toBase18(OCEAN_init_liquidity),
    ]
    swap_fees = [
        toBase18(0.02), #LP swap fee
        toBase18(0.01), #mkt swap fee
    ]
    addresses = [
        ss_bot.address, OCEAN_address, address0, address0,
        OPF_ADDRESS, pool_template.address]

    tx = DT.deployPool(ss_params, swap_fees, addresses, {"from": account0})
    pool_address = oceanv4util.poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT080.BPool.at(pool_address)

    assert OCEANtoken.balanceOf(pool_address) == toBase18(OCEAN_init_liquidity)
    assert pool.getSwapFee() == toBase18(0.02)
    assert pool.getMarketFee() == toBase18(0.01)


def test_createDataNFT_via_util():
    router = oceanv4util.deployRouter(account0)
    (dataNFT, f) = oceanv4util.createDataNFT(
        "dataNFT", "DATANFT", account0, router)
    assert dataNFT.name() == "dataNFT"
    assert dataNFT.symbol() == "DATANFT"
    assert dataNFT.getPermissions(account0.address) == (True, True, True, True)
    assert dataNFT.balanceOf(account0.address) == 1


def test_createDT_via_util():
    router = oceanv4util.deployRouter(account0)
    (dataNFT, f) = oceanv4util.createDataNFT("dataNFT", "DATANFT", account0, router)
    DT = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSymbol", 10000, dataNFT, account0)
    assert DT.name() == "DT"
    assert DT.symbol() == "DTSymbol"
    assert DT.cap() == toBase18(10000)
    assert DT.balanceOf(account0.address) == 0


def test_createBPool_via_util():
    brownie.chain.reset()
    router = oceanv4util.deployRouter(account0)
    (dataNFT, erc721_factory) = oceanv4util.createDataNFT(
        "dataNFT", "DATANFT", account0, router)
    DT = oceanv4util.createDatatokenFromDataNFT(
        "DT", "DTSymbol", 10000, dataNFT, account0)

    oceanv4util.fundOCEANFromAbove(address0, toBase18(10000.0))
    OCEAN = oceanv4util.OCEANtoken()

    OCEAN_init_liquidity = 2000.0
    DT_OCEAN_rate = 0.1
    DT_vest_amt = 100
    DT_vest_num_blocks = 600
    LP_swap_fee = 0.03
    mkt_swap_fee = 0.01
    pool = oceanv4util.createBPoolFromDatatoken(
        DT, erc721_factory, account0,
        OCEAN_init_liquidity, DT_OCEAN_rate,
        DT_vest_amt, DT_vest_num_blocks,
        LP_swap_fee, mkt_swap_fee)
    pool_address = pool.address

    assert pool.getBaseTokenAddress() == OCEAN.address
    assert OCEAN.balanceOf(pool_address) < toBase18(10000.0)
    assert pool.getMarketFee() == toBase18(mkt_swap_fee)
    assert pool.getSwapFee() == toBase18(LP_swap_fee)
