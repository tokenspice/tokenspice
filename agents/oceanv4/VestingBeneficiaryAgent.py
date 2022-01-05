from enforce_typing import enforce_types

from engine import AgentBase
from util.globaltokens import OCEAN_address


@enforce_types
class VestingBeneficiaryAgent(AgentBase.AgentBaseEvm):
    def __init__(
        self, name: str, USD: float, OCEAN: float, vesting_wallet_agent_name: str
    ):
        super().__init__(name, USD, OCEAN)
        self._vesting_wallet_agent_name = vesting_wallet_agent_name

    def takeStep(self, state):
        # ping the vesting wallet agent to release OCEAN
        # (anyone can ping the vesting wallet; if this agent is
        #  the beneficiary then the vesting wallet will send OCEAN)
        vw = state.getAgent(self._vesting_wallet_agent_name).vesting_wallet
        vw.release(OCEAN_address(), {"from": self._wallet.account})

        # ensure that self.OCEAN() is accurate
        self._wallet.resetCachedInfo()
