from enforce_typing import enforce_types

from agents.VestingWalletAgent import VestingWalletAgent
from engine import AgentBase
from util.constants import BROWNIE_PROJECT057
from util import globaltokens
from util.base18 import toBase18


@enforce_types
class VestingFunderAgent(AgentBase.AgentBaseEvm):
    """Will create and fund a VestingWalletAgent with specified name.
    The vesting wallet will vest over time; when its funds are released,
    they will go to the specified beneficiary agent."""

    def __init__(
        self,
        name: str,
        USD: float,
        OCEAN: float,
        vesting_wallet_agent_name: str,
        beneficiary_agent_name: str,
        start_timestamp: int,
        duration_seconds: int,
    ):  # pylint: disable=too-many-arguments
        super().__init__(name, USD, OCEAN)

        self._vesting_wallet_agent_name: str = vesting_wallet_agent_name
        self._beneficiary_agent_name: str = beneficiary_agent_name
        self._start_timestamp: int = start_timestamp
        self._duration_seconds: int = duration_seconds

        self._did_funding = False

    def takeStep(self, state) -> None:
        if self._did_funding:
            return
        self._did_funding = True

        # create vesting wallet
        beneficiary_agent = state.getAgent(self._beneficiary_agent_name)
        vw_contract = BROWNIE_PROJECT057.VestingWallet057.deploy(
            beneficiary_agent.address,
            self._start_timestamp,
            self._duration_seconds,
            {"from": self.account},
        )

        # fund the vesting wallet with all of self's OCEAN
        token = globaltokens.OCEANtoken()
        token.transfer(
            vw_contract.address, toBase18(self.OCEAN()), {"from": self.account}
        )
        self._wallet.resetCachedInfo()

        # create vesting wallet agent, add to state
        vw_agent = VestingWalletAgent(self._vesting_wallet_agent_name, vw_contract)
        state.addAgent(vw_agent)
