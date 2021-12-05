import brownie

# import sol080.contracts.oceanv4.oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT

account0 = brownie.network.accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

accounts = brownie.network.accounts

def test_trent_play():
    #deploy templates, then factory
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

    #from factory, deploy an ERC721 data NFT
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
    dataNFT1_address = tx.events['NFTCreated']['newTokenAddress']
    dataNFT1 = BROWNIE_PROJECT080.ERC721Template.at(dataNFT1_address)

    #from erc271 data NFT, deploy an ERC20 datatoken
    erc20_template_index = 1 #refer to erc20_template
    strings = ["datatoken 1", "DT1"] #name, symbol
    addresses = [address0]*4 #minter, fee mgr, pub mkt addr, pub mkt fee token
    uints = [toBase18(1000.0), toBase18(0.1)] # erc20 cap, pub mkt fee amt
    bytes = []
    tx = dataNFT1.createERC20(
        erc20_template_index,
        strings,
        addresses,
        uints,
        bytes,
        {"from":account0}
    )
    datatoken1_address = tx.events['TokenCreated']['newTokenAddress']
    datatoken1 = BROWNIE_PROJECT080.ERC20Template.at(1_address)
    #FIXME: solve warning "Event log does not contain enough topics for the given ABI - this is usually because an event argument is not marked as indexed"

    #from ?, deploy bpool
    #FIXME
    
def test_direct():
    erc721_token= BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": account0}
    )

    # Step 1: DataPublisher interacts with NFTFactory
    tt = BROWNIE_PROJECT080.V3DataTokenTemplate.deploy(
        "TT",
        "TemplateToken",
        address0,
        toBase18(1e3),
        "blob",
        address0,
        {"from": account0},
    )

    dtfactory = BROWNIE_PROJECT080.V3DTFactory.deploy(
        tt.address, account0.address, {"from": account0}
    )
    tx2 = dtfactory.createToken(
        "foo_blob", "DT", "DT", toBase18(100.0), {"from": account0}
    )
    dt_address = tx2.events["TokenCreated"]["newTokenAddress"]

    # Deploy ERC721Factory
    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        erc721_token.address,
        dt_address,
        OPF_ADDRESS,
        address0,
        {"from":account0}
    )

    current_nft_count = erc721_factory.getCurrentNFTCount()

    # Deploy ERC721Contract
    tx2 = erc721_factory.deployERC721Contract(
        "NFT",
        "NFTSYMBOL",
        1,
        account0,
        "https://oceanprotocol.com/nft/",
        {"from":account0}
    )

    registered_event = tx2.events
    assert registered_event["NFTCreated"]["tokenName"] == "NFT"
    assert registered_event["NFTCreated"]["symbol"] == "NFTSYMBOL"

    # Tests current NFT count
    assert erc721_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template = erc721_factory.getNFTTemplate(1)
    assert nft_template[0] == erc721_token.address
    assert nft_template[1] is True

    # Step 2: Publisher createERC20
    erc721_token.initialize(
        address0,
        "NFT1",
        "NFTSYMBOL1",
        erc721_token.address,
        address0,
        "https://oceanprotocol.com/nft/",
        {"from":account0}
    )

    # Tests creating successfully an ERC20 token
    erc721_token.createERC20(1,
        ["ERC20DT1", "ERC20DT1Symbol"], 
        [address0, accounts[1].address, accounts[2].address, accounts[3].address],
        [100,0],
        [b""], 
        {"from":account0}
    )
