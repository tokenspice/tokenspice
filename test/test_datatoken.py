from engine.evm.datatoken import Datatoken
from engine.evm.dtfactory import DTFactory
from web3tools import web3util

def test1():
    pass

# def test_ERC20(alice_wallet):
#     dtfactory = DTFactory()
#     dt_address = dtfactory.createToken(blob='foo_blob', from_wallet=alice_wallet)
#     dt = Datatoken(dt_address)
#     assert isinstance(dt, Datatoken)


# def test_ERC20(alice_wallet, alice_address,
#                bob_wallet, bob_address,
#                OCEAN_address):

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
