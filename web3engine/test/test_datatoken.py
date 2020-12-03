from web3engine import datatoken, dtfactory
from web3tools import web3util

def test_ERC20(alice_wallet, alice_address,
               bob_wallet, bob_address):
    f = dtfactory.DTFactory()
    dt_address = f.createToken('foo', 'DT1', 'DT1', web3util.toBase18(100.0),
                               from_wallet=alice_wallet)
    dt = datatoken.Datatoken(dt_address)
    dt.mint(alice_address, web3util.toBase18(100.0), from_wallet=alice_wallet)

    #functionality inherited from btoken
    assert dt.address == dt_address
    assert dt.symbol() == 'DT1'
    assert dt.decimals() == 18
    assert dt.balanceOf_base(alice_address) == web3util.toBase18(100.0)
    dt.transfer(bob_address, web3util.toBase18(50.0), from_wallet=alice_wallet)
    assert dt.allowance_base(alice_address, bob_address) == 0
    dt.approve(bob_address, int(1e18), from_wallet=alice_wallet)
    assert dt.allowance_base(alice_address, bob_address) == int(1e18)
    
    #functionality for just datatoken
    assert dt.blob() == 'foo'
    assert 'mint' in dir(dt)
    assert 'setMinter' in dir(dt)

