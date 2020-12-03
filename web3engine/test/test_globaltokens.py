from web3engine import globaltokens, datatoken
from web3tools import web3util, web3wallet

def test_OCEAN():
    wallet = web3wallet.randomWeb3Wallet()
    
    OCEAN_base = web3util.toBase18(3.0)
    globaltokens.mintOCEAN(address=wallet.address, value_base=OCEAN_base)
    OCEAN_token = globaltokens.OCEANtoken()
    assert isinstance(OCEAN_token, datatoken.Datatoken)
    assert OCEAN_token.symbol() == 'OCEAN'
    assert OCEAN_token.balanceOf_base(wallet.address) == OCEAN_base
    
    globaltokens.mintOCEAN(address=wallet.address, value_base=OCEAN_base) 
    assert OCEAN_token.balanceOf_base(wallet.address) == OCEAN_base * 2
