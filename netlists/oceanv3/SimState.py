from enforce_typing import enforce_types
from typing import Set

from netlists.oceanv3.modifiedAgents.maliciousPublisherAgent import (
    maliciousPublisherAgent,
)
from netlists.oceanv3.modifiedAgents.v3DataconsumerAgent import v3DataconsumerAgent
from netlists.oceanv3.modifiedAgents.v3PublisherAgent import v3PublisherAgent
from netlists.oceanv3.modifiedAgents.v3SpeculatorAgent import v3SpeculatorAgent
from netlists.oceanv3.modifiedAgents.v3StakerspeculatorAgent import (
    v3StakerspeculatorAgent,
)

from engine import SimStateBase, AgentBase
from .KPIs import KPIs


@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        # assert ss is None
        super().__init__(ss)

        # ss is defined in this netlist module
        if self.ss is None:
            from .SimStrategy import SimStrategy

            self.ss = SimStrategy()
        ss = self.ss  # for convenience as we go forward

        # wire up the circuit
        new_agents: Set[AgentBase.AgentBase] = set()

        new_agents.add(
            v3PublisherAgent(
                name="publisher", USD=0.0, OCEAN=self.ss.publisher_init_OCEAN
            )
        )
        new_agents.add(
            v3DataconsumerAgent(
                name="consumer", USD=0.0, OCEAN=self.ss.consumer_init_OCEAN
            )
        )
        new_agents.add(
            v3StakerspeculatorAgent(
                name="stakerSpeculator", USD=0.0, OCEAN=self.ss.staker_init_OCEAN
            )
        )
        new_agents.add(
            v3SpeculatorAgent(
                name="speculator", USD=0.0, OCEAN=self.ss.speculator_init_OCEAN
            )
        )

        # malicious agents
        new_agents.add(
            maliciousPublisherAgent(
                name="maliciousPublisher",
                USD=0.0,
                OCEAN=self.ss.maliciousPublisher_init_OCEAN,
            )
        )

        for agent in new_agents:
            self.agents[agent.name] = agent

        # kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step)
