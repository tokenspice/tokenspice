import brownie

# import sol080.contracts.oceanv4.oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT

account0 = brownie.network.accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

accounts = brownie.network.accounts

def test_end_to_end_flow_without_v4util():
    erc721_template = BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": account0}
    )
    
    erc20_template = BROWNIE_PROJECT080.ERC20Template.deploy(
        {"from":account0}
    )

    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721_template.address,
        erc20_template.address,
        OPF_ADDRESS,
        address0,
        {"from":account0}
    )

    assert erc721_factory.tx.events["OwnershipTransferred"]["newOwner"] == address0
    assert erc721_factory.tx.events["Template20Added"]["_templateAddress"] == erc20_template.address

    current_nft_count = erc721_factory.getCurrentNFTCount()

    #from factory, deployERC721Contract data NFT
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

    # Step 2: Publisher createERC20
    erc20_template_index = 1 #refer to erc20_template
    DT_name, DT_symbol = "datatoken 1", "DT1"
    strings = [DT_name, DT_symbol]
    minter_addr = fee_mgr_addr = pub_mkt_addr = address0
    pub_mkt_fee_token_addr = ZERO_ADDRESS
    DT_cap = 1000.0
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

    # Tests templateCount function (one of them should be the Enterprise template)
    # assert erc721_factory.templateCount() == 2

    # Tests ERC20 token template list
    assert erc721_factory.getTokenTemplate(1)[0] == erc20_template.address
    assert erc721_factory.getTokenTemplate(1)[1] == True

    # Tests starting multiple token orders successfully
    consumer_acc = accounts[1]
    consumer_addr = consumer_acc.address
    assert DT.balanceOf(minter_addr) == 0
    assert DT.balanceOf(consumer_addr) == 0    

    # DT_amount = toBase18(1)
    # DT.addMinter(consumer_addr, {"from":account0})
    # DT.mint(consumer_addr, DT_amount, {"from":consumer_acc})
    # assert DT.balanceOf(consumer_addr) == DT_amount

    # DT.approve(erc721_factory.address, DT_amount, {"from":consumer_acc})

    #FIXME
    # https://github.com/oceanprotocol/ocean.py/blob/21e5d90d19e6de6d18fd59c6175611b1f1e07a3f/ocean_lib/models/v4/test/test_erc721_factory.py#L150

    # Test creating bpool
     #from ERC20 datatoken, deploy bpool ***WIP***
    ss_rate = 0.01
    ss_OCEAN_decimals = erc20_template.decimals()
    ss_DT_vest_amt = 100.0
    ss_DT_vested_blocks = 25000000 # = num blocks/year, if 15 s/block
    ss_OCEAN_init_liquidity = 100.0

    LP_swap_fee = 0.01 # 1%
    mkt_swap_fee = 0.01 # 1%

    # addresses refers to an array of addresses passed by user
    # [0]  = side staking contract address
    # [1]  = basetoken address for pool creation(OCEAN or other)
    # [2]  = basetokenSender user which will provide the baseToken amount for initial liquidity
    # [3]  = publisherAddress user which will be assigned the vested amount
    # [4]  = marketFeeCollector marketFeeCollector address
    # [5] = poolTemplateAddress

    router_addr = brownie.network.accounts[1].address
    ss_contract = BROWNIE_PROJECT080.SideStaking.deploy(address0, {"from":account0})
    ss_contract_addr = ss_contract.address # [0]  = side staking contract address
    MockOcean_contract =  BROWNIE_PROJECT080.MockOcean.deploy(OPF_ADDRESS, {"from":account0})
    OCEAN_address = MockOcean_contract.address # [1]  = basetoken address for pool creation(OCEAN or other)
    OCEAN_sender_addr = address0 #[2]  = basetokenSender user which will provide the baseToken amount for initial liquidity
    pub_addr = address0 #[3]  = publisherAddress user which will be assigned the vested amount
    mkt_fee_collector_addr = OPF_ADDRESS #[4]  = marketFeeCollector marketFeeCollector address
    bpool_contract = BROWNIE_PROJECT080.BPool.deploy({"from":account0})
    pool_template_addr = bpool_contract.address #[5] = poolTemplateAddress

#     FactoryRouter.deploy(address0, address _oceanToken, address _bpoolTemplate, address _opfCollector, addres
# s[] _preCreatedPools, {'from'

    

    pool_create_data = {
        "addresses": [
            # ss_contract_addr, OCEAN_address, OCEAN_sender_addr, pub_addr, 
            # mkt_fee_collector_addr, pool_template_addr
            ss_contract_addr, DT_address, erc721_factory.address,
            pub_addr, mkt_fee_collector_addr, pool_template_addr
        ],
        "ssParams": [
            toBase18(ss_rate), toBase18(ss_OCEAN_decimals),
            toBase18(ss_DT_vest_amt), toBase18(ss_DT_vested_blocks),
            toBase18(ss_OCEAN_init_liquidity)
        ],
        "swapFees": [toBase18(LP_swap_fee), toBase18(mkt_swap_fee)],
    }
    # DT.addMinter(pub_addr, {"from":account0})
    tx = DT.deployPool(
        pool_create_data["ssParams"],
        pool_create_data["swapFees"],
        pool_create_data["addresses"],
        {"from":account0}
    )
    #pool_address = tx.events['FIXME']['FIXME']
    #pool = BROWNIE_PROJECT080.ERC20Template.at(datatoken1_address)
    
    
    
    
    
    # Tests creating NFT with ERC20
    nft_create_data = {
        "name": "72120Bundle",
        "symbol": "72Bundle",
        "templateIndex": 1,
        "tokenURI": "https://mystorage.com/mytoken.png",
    }
    erc_create_data = {
        "strings": ["ERC20B1", "ERC20DT1Symbol"],
        "templateIndex": 1,
        "addresses": [
            pub_mkt_addr,
            consumer_addr,
            pub_mkt_addr,
            ZERO_ADDRESS,
        ],
        "uints": [toBase18(10), 0],
        "bytess": [b""],
    }

    tx = erc721_factory.createNftWithErc(
        (
            nft_create_data["name"], nft_create_data["symbol"],
            nft_create_data["templateIndex"], nft_create_data["tokenURI"]
        ),
        (
            erc_create_data["templateIndex"], erc_create_data["strings"],
            erc_create_data["addresses"], erc_create_data["uints"],
            erc_create_data["bytess"]
        )
    )

    assert tx.events["NFTCreated"]["admin"] == pub_mkt_addr

    dataNFT2_address = tx.events["NFTCreated"]["newTokenAddress"]
    dataNFT2 = BROWNIE_PROJECT080.ERC721Template.at(dataNFT2_address)
    assert dataNFT2.name() == "72120Bundle"
    assert dataNFT2.symbol() == "72Bundle"

    DT_address_2 = tx.events["TokenCreated"]["newTokenAddress"]
    DT_2 = BROWNIE_PROJECT080.ERC20Template.at(DT_address_2)
    assert DT_2.name() == "ERC20B1"
    assert DT_2.symbol == "ERC20DT1Symbol"