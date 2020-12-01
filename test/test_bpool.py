import pytest

from engine.evm import bfactory, bpool, btoken, datatoken, dtfactory
from web3tools import web3util
from web3tools.web3util import toBase18
from web3tools.wallet import Wallet

def test_notokens_basic(OCEAN_address, alice_wallet, alice_address):
    pool = _deployBPool(alice_wallet)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert not pool.isBound(OCEAN_address)
    assert pool.getNumTokens() == 0
    assert pool.getCurrentTokens() == []
    with pytest.raises(Exception):
        pool.getFinalTokens() #pool's not finalized
    assert pool.getSwapFee_base() == toBase18(1e-6)
    assert pool.getController() == alice_address
    assert str(pool)
    
    with pytest.raises(Exception): 
        pool.finalize() #can't finalize if no tokens

def _deployBPool(from_wallet: Wallet) -> bpool.BPool:
    f = bfactory.BFactory()
    p_address = f.newBPool(from_wallet=from_wallet)
    p = bpool.BPool(p_address)
    return p
