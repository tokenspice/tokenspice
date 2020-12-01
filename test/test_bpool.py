def test1():
    pass

# def test_notokens_basic(OCEAN_address, network, alice_wallet, alice_address):
#     pool = _deployBPool(network, alice_wallet)

#     assert not pool.isPublicSwap()
#     assert not pool.isFinalized()
#     assert not pool.isBound(OCEAN_address)
#     assert pool.getNumTokens() == 0
#     assert pool.getCurrentTokens() == []
#     with pytest.raises(Exception):
#         pool.getFinalTokens() #pool's not finalized
#     assert pool.getSwapFee_base() == toBase18(1e-6)
#     assert pool.getController() == alice_address
#     assert str(pool)
    
#     with pytest.raises(Exception): 
#         pool.finalize() #can't finalize if no tokens

# def _deployBPool(network: str, from_wallet: Wallet) -> SPool:
#     web3 = from_wallet.web3
#     factory_address = util.confFileValue(network, 'BFACTORY_ADDRESS')
#     factory = BFactory(web3, factory_address)
#     pool_address = factory.newBPool(from_wallet=from_wallet)
#     pool = BPool(web3, pool_address)
#     return pool
