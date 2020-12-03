from engine.evm import globaltokens, datatoken
from web3tools import web3util, web3wallet

def test_USD():
    wallet = web3wallet.randomWeb3Wallet()

    USD_base = web3util.toBase18(2.0)
    globaltokens.mintUSD(address=wallet.address, value_base=USD_base) 
    USD_token = globaltokens.USDtoken()
    assert isinstance(USD_token, datatoken.Datatoken)
    assert USD_token.symbol() == 'USD'
    assert USD_token.balanceOf_base(wallet.address) == USD_base
    
    globaltokens.mintUSD(address=wallet.address, value_base=USD_base) 
    assert USD_token.balanceOf_base(wallet.address) == USD_base * 2

def test_OCEAN():
    #s/USD/OCEAN/g
    wallet = web3wallet.randomWeb3Wallet()
    
    OCEAN_base = web3util.toBase18(3.0)
    globaltokens.mintOCEAN(address=wallet.address, value_base=OCEAN_base)
    OCEAN_token = globaltokens.OCEANtoken()
    assert isinstance(OCEAN_token, datatoken.Datatoken)
    assert OCEAN_token.symbol() == 'OCEAN'
    assert OCEAN_token.balanceOf_base(wallet.address) == OCEAN_base
    
    globaltokens.mintOCEAN(address=wallet.address, value_base=OCEAN_base) 
    assert OCEAN_token.balanceOf_base(wallet.address) == OCEAN_base * 2
