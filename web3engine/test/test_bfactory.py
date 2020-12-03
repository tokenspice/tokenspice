from web3engine import bfactory, bpool

def test1(alice_wallet):
    f = bfactory.BFactory()
    p_address = f.newBPool(from_wallet=alice_wallet)
    p = bpool.BPool(p_address)
    assert isinstance(p, bpool.BPool)
