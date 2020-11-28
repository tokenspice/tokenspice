from engine.evm.datatoken import DataTokenTemplate
from engine.evm.dtfactory import DTFactory
from web3tools.wallet import Wallet

def test1(alice_wallet):
    dtfactory = DTFactory()
    dt_address = dtfactory.createToken(blob='foo_blob', from_wallet=alice_wallet)
    dt = DataTokenTemplate(dt_address)
    assert isinstance(dt, DataTokenTemplate)
    assert dt.blob() == 'foo_blob'
