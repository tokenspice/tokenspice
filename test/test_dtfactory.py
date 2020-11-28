from engine.evm.datatoken import Datatoken
from engine.evm.dtfactory import DTFactory
from web3tools.wallet import Wallet

def test1(alice_wallet):
    dtfactory = DTFactory()
    dt_address = dtfactory.createToken(blob='foo_blob', from_wallet=alice_wallet)
    dt = Datatoken(dt_address)
    assert isinstance(dt, Datatoken)
    assert dt.blob() == 'foo_blob'
