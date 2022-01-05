"""
Main classes in this module:
-AgentBaseAbstract - abstract interface
-AgentBaseNoEvm - hold AgentWalletNoEvm
-AgentBaseEvm - hold AgentWalletEvm
-Sub-class AgentBase{NoEvm,Evm} for specific agents (buyers, publishers, ..)
"""

from abc import ABC, abstractmethod
import logging

from enforce_typing import enforce_types

from engine.AgentWallet import AgentWalletAbstract, AgentWalletEvm, AgentWalletNoEvm
from util.constants import SAFETY
from util.strutil import StrMixin

log = logging.getLogger("baseagent")


@enforce_types
class AgentBaseAbstract(ABC):
    def __init__(self, name: str):
        self.name = name
        self._wallet: AgentWalletAbstract

    @abstractmethod
    def takeStep(self, state):  # this is where the Agent does *work*
        pass

    # USD-related
    def USD(self) -> float:
        return self._wallet.USD()

    def receiveUSD(self, amount: float) -> None:
        self._wallet.depositUSD(amount)

    def _transferUSD(self, receiving_agent, amount: float) -> None:
        if SAFETY:
            assert isinstance(receiving_agent, AgentBaseAbstract) or (
                receiving_agent is None
            )
        if receiving_agent is not None:
            self._wallet.transferUSD(receiving_agent._wallet, amount)
        else:
            self._wallet.withdrawUSD(amount)

    # OCEAN-related
    def OCEAN(self) -> float:
        return self._wallet.OCEAN()

    def receiveOCEAN(self, amount: float) -> None:
        self._wallet.depositOCEAN(amount)

    def _transferOCEAN(self, receiving_agent, amount: float) -> None:
        if SAFETY:
            assert isinstance(receiving_agent, AgentBaseAbstract) or (
                receiving_agent is None
            )
        if receiving_agent is not None:
            self._wallet.transferOCEAN(receiving_agent._wallet, amount)
        else:
            self._wallet.withdrawOCEAN(amount)


@enforce_types
class AgentBaseNoEvm(StrMixin, AgentBaseAbstract):
    def __init__(self, name: str, USD: float, OCEAN: float):
        AgentBaseAbstract.__init__(self, name)
        self._wallet: AgentWalletNoEvm = AgentWalletNoEvm(USD, OCEAN)

        # postconditions
        assert self.USD() == USD
        assert self.OCEAN() == OCEAN


@enforce_types
class AgentBaseEvm(StrMixin, AgentBaseAbstract):
    def __init__(self, name: str, USD: float, OCEAN: float):
        AgentBaseAbstract.__init__(self, name)
        self._wallet: AgentWalletEvm = AgentWalletEvm(USD, OCEAN)

        # postconditions
        assert self.USD() == USD
        assert self.OCEAN() == OCEAN

    @property
    def address(self) -> str:
        return self._wallet.address

    @property
    def account(self) -> str:
        return self._wallet.account

    # datatoken and pool-related
    def DT(self, dt) -> float:
        return self._wallet.DT(dt)

    def BPT(self, pool) -> float:
        return self._wallet.BPT(pool)

    def stakeOCEAN(self, OCEAN_stake: float, pool):
        self._wallet.stakeOCEAN(OCEAN_stake, pool)

    def unstakeOCEAN(self, BPT_unstake: float, pool):
        self._wallet.unstakeOCEAN(BPT_unstake, pool)
