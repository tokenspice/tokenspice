import brownie

# import sol080.contracts.oceanv4.oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, OPF_ACCOUNT

account0 = brownie.network.accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address

def test_direct():
    template_erc721= BROWNIE_PROJECT080.ERC721Template.deploy(
        {"from": account0}
    )

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
    tx1 = dtfactory.createToken(
        "foo_blob", "DT", "DT", toBase18(100.0), {"from": account0}
    )
    dt_address = tx1.events["TokenCreated"]["newTokenAddress"]

    erc721_factory = BROWNIE_PROJECT080.ERC721Factory.deploy(
        template_erc721.address,
        dt_address,
        OPF_ADDRESS,
        address0,
        {"from":account0}
    )

    # registered_event = brownie.chain.get_transaction(erc721_factory.tx.txid).events
    # assert registered_event["OwnershipTransferred"]["newOwner"] == account0
    # assert registered_event["Template721Added"]["_templateAddress"] == template_erc721.address

    current_nft_count = erc721_factory.getCurrentNFTCount()
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
    assert nft_template[0] == template_erc721.address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    erc721_factory.createToken(
        1, 
        ["DT","sym"], 
        [address0,address0,address0,address0],
        [1e3,0.1],
        [1],
        {"from": account0}
    )

