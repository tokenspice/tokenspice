import brownie

# import sol080.contracts.oceanv4.oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT

accounts = brownie.network.accounts
account0 = accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

def test_end_to_end_flow_without_v4util():
    erc721_template = BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": account0}
    )
    
    erc20_template = BROWNIE_PROJECT080.ERC20Template.deploy(
        {"from":account0}
    )
    OCEANtoken = BROWNIE_PROJECT080.MockOcean.deploy(address0, {"from":account0})
    OCEAN_address = OCEANtoken.address
    pool_template = BROWNIE_PROJECT080.BPool.deploy({'from': account0})
    
    router = BROWNIE_PROJECT080.FactoryRouter.deploy(
        address0,
        OCEAN_address,
        pool_template.address,
        OPF_ADDRESS,
        [],
        {'from': account0}
    )

    sideStaking = BROWNIE_PROJECT080.SideStaking.deploy(
        router.address, {'from': account0}
    )

    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721_template.address,
        erc20_template.address,
        OPF_ADDRESS,
        router.address,
        {"from":account0}
    )
    router.addFactory(erc721_factory.address, {'from': account0})
    router.addSSContract(sideStaking.address, {"from": account0})

    assert erc721_factory.tx.events["OwnershipTransferred"]["newOwner"] == address0
    assert erc721_factory.tx.events["Template20Added"]["_templateAddress"] == erc20_template.address

    current_nft_count = erc721_factory.getCurrentNFTCount()

    #1 deployERC721Contract data NFT
    erc721_template_index = 1 #refer to erc721_template
    additional_NFT_deployer_address = ZERO_ADDRESS
    token_URI = "https://mystorage.com/mytoken.png"
    tx = erc721_factory.deployERC721Contract(
        "data NFT 1",
        "DATANFT1",
        erc721_template_index,
        additional_NFT_deployer_address,
        token_URI,
        {"from":account0}
    )

    assert tx.events["NFTCreated"]["admin"] == address0
    
    # ERC721 token
    dataNFT1_address = tx.events["NFTCreated"]["newTokenAddress"]
    dataNFT1 = BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address)
    
    assert dataNFT1.name() == "data NFT 1"
    assert dataNFT1.symbol() == "DATANFT1"

    # Tests current NFT count
    assert erc721_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template = erc721_factory.getNFTTemplate(1)
    assert nft_template[0] == erc721_template.address
    assert nft_template[1] is True

    #2: Publisher createERC20
    erc20_template_index = 1 #refer to erc20_template
    DT_name, DT_symbol = "datatoken 1", "DT1"
    strings = [DT_name, DT_symbol]
    minter_addr = fee_mgr_addr = pub_mkt_addr = address0
    pub_mkt_fee_token_addr = ZERO_ADDRESS
    DT_cap = 100000
    pub_mkt_fee_amt = 0.0 # in OCEAN
    uints = [toBase18(DT_cap), toBase18(pub_mkt_fee_amt)] 
    addresses = [minter_addr, fee_mgr_addr, pub_mkt_addr, pub_mkt_fee_token_addr]
    bytes = []
    tx = dataNFT1.createERC20(
        erc20_template_index,
        strings,
        addresses,
        uints,
        bytes,
        {"from":account0}
    )

    DT_address = tx.events['TokenCreated']['newTokenAddress']
    DT = BROWNIE_PROJECT080.ERC20Template.at(DT_address)

    # Tests ERC20 token template list
    assert erc721_factory.getTokenTemplate(1)[0] == erc20_template.address
    assert erc721_factory.getTokenTemplate(1)[1] == True

    # Tests balanceOf
    assert DT.balanceOf(minter_addr) == 0

    #3 Publisher creating bpool, from ERC20 datatoken
    ss_rate = 0.1
    ss_OCEAN_decimals = 18
    ss_DT_vest_amt = 9999.0 #max 10% but 10000 gives error
    ss_DT_vested_blocks = 2500000 # = num blocks/year, if 15 s/block
    ss_OCEAN_init_liquidity = 2000.0

    LP_swap_fee = 0.001 # 1%
    mkt_swap_fee = 0.001 # 1%
    
    pool_create_data = {
        "addresses": [
            sideStaking.address, OCEAN_address, address0,
            address0, OPF_ADDRESS, pool_template.address
        ],
        "ssParams": [
            toBase18(ss_rate), ss_OCEAN_decimals,
            toBase18(ss_DT_vest_amt), ss_DT_vested_blocks,
            toBase18(ss_OCEAN_init_liquidity)
        ],
        "swapFees": [toBase18(LP_swap_fee), toBase18(mkt_swap_fee)],
    }

    OCEANtoken.approve(router.address, toBase18(ss_OCEAN_init_liquidity),{'from': account0})

    tx = DT.deployPool(
        pool_create_data["ssParams"],
        pool_create_data["swapFees"],
        pool_create_data["addresses"],
        {"from":account0}
    )