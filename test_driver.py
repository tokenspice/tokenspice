_OCEAN_INIT = 1000.0
_OCEAN_STAKE = 200.0
_DT_INIT = 100.0
_DT_STAKE = 20.0


POOL_WEIGHT_DT    = 3.0
POOL_WEIGHT_OCEAN = 7.0
assert (POOL_WEIGHT_DT + POOL_WEIGHT_OCEAN) == 10.0

from enforce_typing import enforce_types # type: ignore[import]
from typing import Dict
from agents.AgentWallet import AgentWallet
from web3engine.globaltokens import OCEANtoken
from web3engine.bfactory import BFactory
from web3engine.bpool import BPool
from web3engine.datatoken import Datatoken
from web3engine.dtfactory import DTFactory
from web3tools import web3util, web3wallet

# @enforce_types
# def _createPool(DT: Datatoken, web3_w: web3wallet.Web3Wallet):
    # OCEAN = OCEANtoken()
    
    # #Create OCEAN-DT pool
    # p_address = BFactory().newBPool(from_wallet=web3_w)
    # pool = BPool(p_address)

    # DT.approve(pool.address, web3util.toBase18(_DT_STAKE), from_wallet=web3_w)
    # OCEAN.approve(pool.address, web3util.toBase18(_OCEAN_STAKE),from_wallet=web3_w)

    # pool.bind(DT.address, web3util.toBase18(_DT_STAKE),
              # web3util.toBase18(POOL_WEIGHT_DT), from_wallet=web3_w)
    # pool.bind(OCEAN.address, web3util.toBase18(_OCEAN_STAKE),
              # web3util.toBase18(POOL_WEIGHT_OCEAN), from_wallet=web3_w)

    # pool.finalize(from_wallet=web3_w)
    # return pool



# @enforce_types
# def _make_info(private_key_name:str):
    # # TOTALLY STRIP THIS FUNCTION IN FAVOR OF A BETTER AGENT INTERFACE
    
    # info.web3wallet = info.agent_wallet._web3wallet

    # info.DT = _createDT(info.web3wallet)
    # info.pool = _createPool(DT=info.DT, web3_w=info.web3wallet)
    # return info


# class Environment:

class AgentTEST:

    def __init__(self, agent_name: str, network_name: str, _OCEAN_INIT: float):
        self.private_key = web3util.confFileValue(network_name, agent_name)
        self.wallet = AgentWallet(OCEAN=_OCEAN_INIT, private_key=self.private_key)
        self.web3wallet = self.wallet._web3wallet
        self.datatokens_created: Dict[str, Datatoken] = {}
        self._CACHED_DT = None

    @enforce_types
    def create_datatoken(self,
                         blob: str,
                         name: str,
                         symbol: str,
                         cap_base: float,
                         use_cache: bool=False):
        if self._CACHED_DT and use_cache:
            return self._CACHED_DT
        cap_base = web3util.toBase18(cap_base)
        datatoken_address = DTFactory().createToken(blob, name, symbol, cap_base, self.web3wallet)
        dt = Datatoken(datatoken_address)
        dt.mint(account=self.web3wallet.address, value_base=cap_base, from_wallet=self.web3wallet)
        self._CACHED_DT = dt
        self.datatokens_created[symbol] = dt
        return dt


    @enforce_types
    def create_pool(self, 
                   datatoken: Datatoken, 
                   _DT_STAKE: float, 
                   _OCEAN_STAKE: float, 
                   POOL_WEIGHT_DT: float,
                   POOL_WEIGHT_OCEAN: float):
        OCEAN = OCEANtoken()
        dt_stake: int = web3util.toBase18(_DT_STAKE)
        ocean_stake: int = web3util.toBase18(_OCEAN_STAKE)
        pool_weight_dt: int = web3util.toBase18(POOL_WEIGHT_DT)
        pool_weight_ocean: int = web3util.toBase18(POOL_WEIGHT_OCEAN)
        pool_address = BFactory().newBPool(from_wallet=self.web3wallet)
        pool = BPool(pool_address)
        datatoken.approve(pool.address, web3util.toBase18(dt_stake), from_wallet=self.web3wallet)
        OCEAN.approve(pool.address, web3util.toBase18(_OCEAN_STAKE), from_wallet=self.web3wallet)
        pool.bind(
            token_address=datatoken.address, 
            balance_base=dt_stake, 
            weight_base=pool_weight_dt,
            from_wallet=self.web3wallet)
        pool.bind(
            token_address=OCEAN.address,
            balance_base=ocean_stake,
            weight_base=pool_weight_ocean,
            from_wallet=self.web3wallet)
        pool.finalize(from_wallet=self.web3wallet)

        return pool


private_key_name: str='TEST_PRIVATE_KEY1'
network: str = web3util.confFileValue('general', 'NETWORK')
alice = AgentTEST(agent_name=private_key_name, network_name=network, _OCEAN_INIT=_OCEAN_INIT)
alice_datatoken = alice.create_datatoken(blob="", name="Alice Coin", symbol="ALC", cap_base=_DT_INIT, use_cache=False)
alice_pool = alice_pool = alice.create_pool(
    datatoken=alice_datatoken,
    _DT_STAKE=_DT_STAKE,
    _OCEAN_STAKE=_OCEAN_STAKE,
    POOL_WEIGHT_DT=POOL_WEIGHT_DT,
    POOL_WEIGHT_OCEAN=POOL_WEIGHT_OCEAN
)

# test DT
alice_DT_amt: float = alice.wallet.DT(alice_datatoken)
print(alice_DT_amt, _DT_INIT, _DT_STAKE)

assert alice_DT_amt == (_DT_INIT - _DT_STAKE)
