from enforce_typing import enforce_types
from typing import Set

from assets.agents import GrantGivingAgent, GrantTakingAgent
from engine import AgentBase, SimStateBase
from .KPIs import KPIs
from .SimStrategy import SimStrategy
from util.constants import S_PER_DAY

@enforce_types
class SimState(SimStateBase.SimStateBase):
    
    def __init__(self, ss=None):
        #initialize self.tick, ss, agents, kpis
        assert ss is None, "simple SimState will initalize its own ss"
        super().__init__(ss)

        #now, fill in actual values for ss, agents, kpis
        self.ss = SimStrategy()
        ss = self.ss #shorter
                       
        #Instantiate and connect agent instances. "Wire up the circuit"
        new_agents: Set[AgentBase.AgentBase] = set()

        new_agents.add(GrantGivingAgent.GrantGivingAgent(
            name="granter1",
            USD=ss.granter_init_USD,
            OCEAN=ss.granter_init_OCEAN,
            receiving_agent_name="taker1",
            s_between_grants=ss.granter_s_between_grants,
            n_actions=ss.granter_n_actions))

        new_agents.add(GrantTakingAgent.GrantTakingAgent(
            name = "taker1", USD=0.0, OCEAN=0.0))

        #fill in self.agents dict
        for agent in new_agents:
            self.agents[agent.name] = agent

        #track certain metrics over time, so that we don't have to load
        self.kpis = KPIs(self.ss.time_step)
                    
    def takeStep(self) -> None:
        """This happens once per tick"""
        #update agents
        #update kpis (global state values)
        super().takeStep()

    def OCEANprice(self) -> float:
        return 1.0 #arbitrary. Need this func for GrantTakingAgent
