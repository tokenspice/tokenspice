
from enforce_typing import enforce_types # type: ignore[import]
import pytest

from agents import AgentWallet, BaseAgent
from web3tools import web3util, web3wallet
from web3tools.web3util import toBase18
from web3engine import bfactory, bpool, datatoken, dtfactory, globaltokens
from util.constants import POOL_WEIGHT_DT, POOL_WEIGHT_OCEAN

#alice:
# 1. starts with an init OCEAN
# 2. creates a DT, and mints an init amount
# 3. creates a DT-OCEAN pool, and adds init liquidity

_OCEAN_INIT = 1000.0
_OCEAN_STAKE = 200.0
_DT_INIT = 100.0
_DT_STAKE = 20.0

@pytest.fixture
def alice_private_key() -> str:
    return _alice_wallet().private_key

@pytest.fixture
def alice_agent_wallet() -> AgentWallet.AgentWallet:
    return _alice_wallet().agent_wallet

@pytest.fixture
def alice_web3wallet() -> web3wallet.Web3Wallet:
    return _alice_wallet().wallet

@pytest.fixture
def alice_DT() -> datatoken.Datatoken:
    return _alice_wallet().DT

@pytest.fixture
def alice_pool():
    return _alice_wallet().pool

@enforce_types
def _alice_wallet(cache=True):
    return _make_wallet(private_key_name='TEST_PRIVATE_KEY1', cache=cache)

_CACHED_WALLET = None
@enforce_types
def _make_wallet(private_key_name:str, cache: bool):
    global _CACHED_WALLET
    if _CACHED_WALLET is None and cache:
        class _Wallet:
            pass
        wallet = _Wallet()
        
        network = web3util.get_network()
        wallet.private_key = web3util.confFileValue(network, private_key_name)
        wallet.agent_wallet = AgentWallet.AgentWallet(
            OCEAN=_OCEAN_INIT,private_key=wallet.private_key)
        wallet.web3wallet = wallet.agent_wallet._web3wallet

        wallet.DT = _createDT(wallet.web3wallet)
        wallet.pool = _createPool(DT=wallet.DT, web3_w=wallet.web3wallet)
        _CACHED_WALLET = wallet
        return _CACHED_WALLET
    return _CACHED_WALLET

# Eureka I got it. We should cache the whole wallet object, not just the datatoken. I
# have a feeling that that will solve the issues we are facing. 
@enforce_types
def _createDT(web3_w:web3wallet.Web3Wallet)-> datatoken.Datatoken:
    DT_address = dtfactory.DTFactory().createToken(
        'foo', 'DT1', 'DT1', toBase18(_DT_INIT),from_wallet=web3_w)
    DT = datatoken.Datatoken(DT_address)
    DT.mint(web3_w.address, toBase18(_DT_INIT), from_wallet=web3_w)
    return DT

@enforce_types
def _createPool(DT:datatoken.Datatoken, web3_w:web3wallet.Web3Wallet):
    OCEAN = globaltokens.OCEANtoken()
    
    #Create OCEAN-DT pool
    p_address = bfactory.BFactory().newBPool(from_wallet=web3_w)
    pool = bpool.BPool(p_address)

    DT.approve(pool.address, toBase18(_DT_STAKE), from_wallet=web3_w)
    OCEAN.approve(pool.address, toBase18(_OCEAN_STAKE),from_wallet=web3_w)

    pool.bind(DT.address, toBase18(_DT_STAKE),
              toBase18(POOL_WEIGHT_DT), from_wallet=web3_w)
    pool.bind(OCEAN.address, toBase18(_OCEAN_STAKE),
              toBase18(POOL_WEIGHT_OCEAN), from_wallet=web3_w)

    pool.finalize(from_wallet=web3_w)
    
    return pool

@pytest.fixture
def alice_agent() -> BaseAgent.BaseAgent:
    return _alice_agent()

@pytest.fixture
def alice_agent_DT() -> datatoken.Datatoken:
    return _alice_agent().DT

@pytest.fixture
def alice_agent_pool():
    return _alice_agent().pool

@enforce_types
def _alice_agent(cache=True):
    return _make_agent(private_key_name='TEST_PRIVATE_KEY1', cache=cache)

_CACHED_AGENT = None
@enforce_types
def _make_agent(private_key_name: str, cache: bool=True) -> str:
    global _CACHED_AGENT
    if _CACHED_AGENT is None and cache:
        class _Agent(BaseAgent.BaseAgent):
            def takeStep(self, state):
                pass
        network = web3util.get_network()
        private_key = web3util.confFileValue(network, private_key_name)
        alice = _Agent(
            name="agent1",
            USD=0.0,OCEAN=_OCEAN_INIT, 
            private_key=private_key)
        alice.web3wallet = alice._wallet._web3wallet
        alice.DT = _createDT(alice.web3wallet)
        alice.pool = _createPool(alice.DT, alice.web3wallet)
        _CACHED_AGENT = alice
        return _CACHED_AGENT
    return _CACHED_AGENT
