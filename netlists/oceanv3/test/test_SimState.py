from enforce_typing import enforce_types

from agents.PublisherAgent import PublisherAgent
from agents.DataconsumerAgent import DataconsumerAgent
from agents.SpeculatorAgent import SpeculatorAgent, StakerspeculatorAgent
from ..SimState import KPIs
from ..SimState import SimState


@enforce_types
def test1():
    state = SimState()

    assert hasattr(state.ss, "publisher_init_OCEAN")
    assert isinstance(state.getAgent("publisher"), PublisherAgent)
    assert isinstance(state.getAgent("consumer"), DataconsumerAgent)
    assert isinstance(state.getAgent("speculator"), SpeculatorAgent)
    assert isinstance(state.getAgent("stakerSpeculator"), StakerspeculatorAgent)
    assert isinstance(state.getAgent("maliciousPublisher"), PublisherAgent)

    assert isinstance(state.kpis, KPIs)

    assert state.rugged_pools == []
