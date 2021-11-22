import logging
log = logging.getLogger('agents')

from enforce_typing import enforce_types
import math

from engine import AgentBase
        
@enforce_types
class VestingBeneficiaryAgent(AgentBase.AgentBaseEvm):
    def __init__(self, name: str, USD: float, OCEAN: float,
                 vesting_wallet_agent):
        super().__init__(name, USD, OCEAN)
        self._vesting_wallet_agent = vesting_wallet_agent

    @property
    def vesting_wallet_agent(self):
        return self._vesting_wallet_agent
        
    def takeStep(self, state):
        #ping the vesting wallet agent to release OCEAN
        # (anyone can ping the vesting wallet; if this agent is
        #  the beneficiary then the vesting wallet will send OCEAN)
        self.vesting_wallet_agent.releaseOCEAN()

        #ensure that self.OCEAN() is accurate
        self._wallet.resetCachedInfo()


