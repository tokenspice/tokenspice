from enforce_typing import enforce_types
from typing import Set

from agents.DataconsumerAgent import DataconsumerAgent
from agents.maliciousPublisherAgent import maliciousPublisherAgent
from agents.PublisherAgent import PublisherAgent
from agents.SpeculatorAgent import SpeculatorAgent
from agents.StakerspeculatorAgent import StakerspeculatorAgent

from engine import SimStateBase, AgentBase
from .KPIs import KPIs


@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        # initialize self.tick, ss, agents, kpis
        super().__init__(ss)

        # now, fill in actual values for ss, agents, kpis
        if self.ss is None:
            from .SimStrategy import SimStrategy
            self.ss = SimStrategy()
        ss = self.ss  # for convenience as we go forward

        # wire up the circuit
        new_agents: Set[AgentBase.AgentBase] = set()

        new_agents.add(
            PublisherAgent(
                name="publisher", USD=0.0, OCEAN=self.ss.publisher_init_OCEAN,
                DT_init=self.ss.DT_init, DT_stake=self.ss.DT_stake
            )
        )
        new_agents.add(
            DataconsumerAgent(
                name="consumer", USD=0.0, OCEAN=self.ss.consumer_init_OCEAN
            )
        )
        new_agents.add(
            StakerspeculatorAgent(
                name="stakerSpeculator",
                USD=0.0, OCEAN=self.ss.staker_init_OCEAN,
                s_between_speculates=self.ss.staker_s_between_speculates
            )
        )
        new_agents.add(
            SpeculatorAgent(
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

        # pools that were rug-pulled by a malicious publisher
        self.rugged_pools:List[str] = []
