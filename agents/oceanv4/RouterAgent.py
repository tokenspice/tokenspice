import math
from typing import List

from enforce_typing import enforce_types

from engine import AgentBase
from util.constants import S_PER_MONTH


@enforce_types
class RouterAgent(AgentBase.AgentBaseNoEvm):
    def __init__(self, name: str, USD: float, OCEAN: float, receiving_agents: dict):
        """Constructor.

        Args:
            name: str -- agent name
            USD: float -- initial USD
            OCEAN: float -- initial OCEAN
            receiving_agents: dict of {agent_n_name:str : method_for_percent_going_to_agent_n:method

        Note:
            The dict values are methods, not floats, so that the return value
            can change over time. E.g. percent_burn changes.

        """
        super().__init__(name, USD, OCEAN)
        self._receiving_agents = receiving_agents

        # track amounts over time
        self._USD_per_tick: List[float] = []  # the next tick will record what's in self
        self._OCEAN_per_tick: List[float] = []  # ""

    def takeStep(self, state) -> None:
        # record what we had up until this point
        self._USD_per_tick.append(self.USD())
        self._OCEAN_per_tick.append(self.OCEAN())

        # disburse it all, as soon as agent has it
        if self.USD() > 0:
            self._disburseUSD(state)
        if self.OCEAN() > 0:
            self._disburseOCEAN(state)

    def _disburseUSD(self, state) -> None:
        USD = self.USD()
        for name, computePercent in self._receiving_agents.items():
            self._transferUSD(state.getAgent(name), computePercent() * USD)

    def _disburseOCEAN(self, state) -> None:
        OCEAN = self.OCEAN()
        for name, computePercent in self._receiving_agents.items():
            self._transferOCEAN(state.getAgent(name), computePercent() * OCEAN)

    def monthlyUSDreceived(self, state) -> float:
        """USD received in the past month. Disburses immediately on receipt."""
        tick1 = self._tickOneMonthAgo(state)
        tick2 = state.tick
        return float(sum(self._USD_per_tick[tick1 : tick2 + 1]))

    def monthlyOCEANreceived(self, state) -> float:
        """OCEAN received in past month. Disburses immediately on receipt."""
        tick1 = self._tickOneMonthAgo(state)
        tick2 = state.tick
        return float(sum(self._OCEAN_per_tick[tick1 : tick2 + 1]))

    @staticmethod
    def _tickOneMonthAgo(state) -> int:
        t2 = state.tick * state.ss.time_step
        t1 = t2 - S_PER_MONTH
        if t1 < 0:
            return 0
        tick1 = int(max(0, math.floor(t1 / float(state.ss.time_step))))
        return tick1
