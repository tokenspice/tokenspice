from enforce_typing import enforce_types
import random

from engine import AgentBase
from util import globaltokens
from util.base18 import toBase18
from util.globaltokens import OCEAN_address


@enforce_types
class VestingWalletAgent(AgentBase.AgentBaseEvm):
    # this vesting wallet never owns stuff itself, therefore USD=OCEAN=0
    def __init__(self, name: str, vesting_wallet):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._vesting_wallet = vesting_wallet  # brownie smart contract

    @property
    def vesting_wallet(self):
        return self._vesting_wallet

    def takeStep(self, state):
        # it's a smart contract robot, it doesn't initiate anything itself
        pass
