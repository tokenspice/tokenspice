from enforce_typing import enforce_types
import random

from engine import AgentBase
from web3engine import bpool, datatoken, globaltokens
from web3tools.web3util import toBase18
from web3engine.globaltokens import OCEAN_address
            
@enforce_types
class VestingWalletAgent(AgentBase.AgentBaseEvm):
    #this vesting wallet never owns stuff itself, therefore USD=OCEAN=0
    def __init__(self, name: str, vesting_wallet):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._vesting_wallet = vesting_wallet #brownie smart contract

    @property
    def vesting_wallet(self):
        return self._vesting_wallet

    def releaseOCEAN(self, from_account):
        self._vesting_wallet.release(OCEAN_address(), {'from':from_account})
        
    def takeStep(self, state):
        #it's a smart contract robot, it doesn't initiate anything itself
        pass
