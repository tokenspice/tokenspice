from enforce_typing import enforce_types
from typing import List, Set

from assets.agents import DataconsumerAgent
from assets.netlists.oceanv3.modifiedAgents import maliciousPublisherAgent,PublisherAgent,SpeculatorAgent, StakerspeculatorAgent
from engine import SimStateBase, AgentBase
from .KPIs import KPIs

@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        # assert ss is None
        super().__init__(ss)

        #ss is defined in this netlist module
        if self.ss is None:
            from .SimStrategy import SimStrategy
            self.ss = SimStrategy()
        ss = self.ss #for convenience as we go forward

        #wire up the circuit
        new_agents: Set[AgentBase.AgentBase] = set()

        new_agents.add(
            PublisherAgent.PublisherAgent(
            name="publisher", USD=0.0, OCEAN=self.ss.publisher_init_OCEAN
            )
        )
        new_agents.add(
            DataconsumerAgent.DataconsumerAgent(
                name="consumer", USD=0.0, OCEAN=self.ss.consumer_init_OCEAN
            )
        )
        new_agents.add(
            StakerspeculatorAgent.StakerspeculatorAgent(
                name='stakerSpeculator', USD=0.0, OCEAN = self.ss.staker_init_OCEAN
            )
        )
        new_agents.add(
            SpeculatorAgent.SpeculatorAgent(
                name='speculator', USD=0.0, OCEAN = self.ss.speculator_init_OCEAN
            )
        )

        # malicious agents
        new_agents.add(
            maliciousPublisherAgent.maliciousPublisherAgent(
                name='maliciousPublisher',USD=0.0, OCEAN = self.ss.maliciousPublisher_init_OCEAN
            )
        )

        for agent in new_agents:
            self.agents[agent.name] = agent

        #kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step) 