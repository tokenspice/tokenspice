from web3engine import datatoken, dtfactory

def test1(alice_wallet):
    f = dtfactory.DTFactory()
    dt_address = f.createToken('foo', 'DT', 'DT', 100000, alice_wallet)
    dt = datatoken.Datatoken(dt_address)
    assert isinstance(dt, datatoken.Datatoken)
    assert dt.blob() == 'foo'
