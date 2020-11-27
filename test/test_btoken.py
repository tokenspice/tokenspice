from web3 import Web3

from web3tools import web3util

def test1():
    network = 'ganache'
    web3 = Web3(web3util.get_web3_provider(network))

# def test_ERC20(network,
#                alice_wallet, alice_address,
#                bob_wallet, bob_address,
#                OCEAN_address):
#     web3 = Web3(util.get_web3_provider(network))
#     token = BToken(web3, OCEAN_address)

#     assert token.symbol() == 'OCEAN'
#     assert token.decimals() == 18
#     assert token.balanceOf_base(alice_address) > util.toBase18(10.0)
#     assert token.balanceOf_base(bob_address) > util.toBase18(10.0)

#     assert token.allowance_base(alice_address, bob_address) == 0
#     token.approve(bob_address, int(1e18), from_wallet=alice_wallet)
#     assert token.allowance_base(alice_address, bob_address) == int(1e18)

#     #alice sends all her OCEAN to Bob, then Bob sends it back
#     alice_OCEAN = token.balanceOf_base(alice_address)
#     bob_OCEAN = token.balanceOf_base(bob_address)
#     token.transfer(bob_address, alice_OCEAN, from_wallet=alice_wallet)
#     assert token.balanceOf_base(alice_address) == 0
#     assert token.balanceOf_base(bob_address) == (alice_OCEAN+bob_OCEAN)
    
#     token.transfer(alice_address, alice_OCEAN, from_wallet=bob_wallet)
#     assert token.balanceOf_base(alice_address) == alice_OCEAN
#     assert token.balanceOf_base(bob_address) == bob_OCEAN
