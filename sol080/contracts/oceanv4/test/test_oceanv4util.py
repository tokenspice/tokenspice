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
    DT_name, DT_symbol = "datatoken 1", "DT1"
    strings = [DT_name, DT_symbol]
    minter_addr = fee_mgr_addr = pub_mkt_addr = address0
    pub_mkt_fee_token_addr = OCEAN_addr
    addresses = [minter_addr, fee_mgr_addr, pub_mkt_addr, pub_mkt_fee_token_addr)
    DT_cap = 1000.0
    pub_mkt_fee_amt = 1000.0 # in OCEAN
    uints = [toBase18(DT_cap), toBase18(pub_mkt_fee_amt)] 
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
    #FIXME: solve warning "Event log does not contain enough topics for the given ABI - this is usually because an event argument is not marked as indexed"

    #from ERC20 datatoken, deploy bpool ***WIP***
    # ss_rate = 0.01
    # ss_OCEAN_decimals = 18
    # ss_DT_vest_amt = 100.0
    # ss_DT_vested_blocks = 2102666.6 # = num blocks/year, if 15 s/block
    # ss_OCEAN_init_liquidity = 100.0
    # ss_params = [toBase18(ss_rate), toBase18(ss_OCEAN_decimals),
    #              toBase18(ss_DT_vest_amt), toBase18(ss_DT_vested_blocks),
    #              toBase18(ss_OCEAN_init_liquidity))
    
    # LP_swap_fee = 0.01 # 1%
    # mkt_swap_fee = 0.01 # 1%
    # swap_fees = [to_base18(LP_swap_fee), toBase18(mkt_swap_fee)]

    # ss_contract_addr = FIXME
    # OCEAN_addr = FIXME
    # OCEAN_sender_addr = address0
    # pub_addr = address0
    # mkt_fee_collector_addr = address0
    # pool_template_addr = FIXME
    
    # tx = datatoken1.deployPool(
    #     ss_params,
    #     swap_fees,
    #     addresses,
    #     {"from":account0}
    # )
    #pool_address = tx.events['FIXME']['FIXME']
    #pool = BROWNIE_PROJECT080.ERC20Template.at(datatoken1_address)
