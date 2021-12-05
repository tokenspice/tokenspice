import brownie

# import sol080.contracts.oceanv4.oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT

account0 = brownie.network.accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

accounts = brownie.network.accounts

def test_1():
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
    datatoken1 = BROWNIE_PROJECT080.ERC20Template.at(datatoken1_address)
    #FIXME: solve warning "Event log does not contain enough topics for the given ABI - this is usually because an event argument is not marked as indexed"

    #from ?, deploy bpool
    #FIXME
    
