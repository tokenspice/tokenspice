from enforce_typing import enforce_types

from agents.PublisherAgent import PublisherAgent
from agents.SpeculatorAgent import StakerspeculatorAgent
from agents.DataconsumerAgent import DataconsumerAgent
from engine import AgentBase


@enforce_types
class DataecosystemAgent(AgentBase.AgentBaseNoEvm):
    """Will operate as a high-fidelity replacement for MarketplacesAgents,
    when it's ready."""

    def takeStep(self, state):
        if self._doCreatePublisherAgent(state):
            self._createPublisherAgent(state)

        if self._doCreateStakerspeculatorAgent(state):
            self._createStakerspeculatorAgent(state)

        if self._doCreateDataconsumerAgent(state):
            self._createDataconsumerAgent(state)

    @staticmethod
    def _doCreatePublisherAgent(state) -> bool:
        # magic number: rule - only create if no agents so far
        return not state.publisherAgents()

    def _createPublisherAgent(self, state) -> None:  # pylint: disable=no-self-use
        name = "foo_publisher"
        USD = 0.0  # magic number
        OCEAN = 1000.0  # magic number
        new_agent = PublisherAgent(name=name, USD=USD, OCEAN=OCEAN)
        state.addAgent(new_agent)

    @staticmethod
    def _doCreateStakerspeculatorAgent(state) -> bool:
        # magic number: rule - only create if no agents so far
        return not state.stakerspeculatorAgents()

    def _createStakerspeculatorAgent(  # pylint: disable=no-self-use
        self, state
    ) -> None:
        name = "foo_stakerspeculator"
        USD = 0.0  # magic number
        OCEAN = 1000.0  # magic number
        new_agent = StakerspeculatorAgent(name=name, USD=USD, OCEAN=OCEAN)
        state.addAgent(new_agent)

    @staticmethod
    def _doCreateDataconsumerAgent(state) -> bool:
        # magic number: rule - only create if no agents so far
        return not state.dataconumerAgents()

    def _createDataconsumerAgent(self, state) -> None:  # pylint: disable=no-self-use
        name = "foo_dataconsumer"
        USD = 0.0  # magic number
        OCEAN = 1000.0  # magic number
        new_agent = DataconsumerAgent(name=name, USD=USD, OCEAN=OCEAN)
        state.addAgent(new_agent)
