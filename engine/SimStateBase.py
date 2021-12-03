from enforce_typing import enforce_types
from engine.AgentDict import AgentDict


@enforce_types
class SimStateBase:
    def __init__(self, ss=None):
        # number of ticks elapsed in the simulation
        self.tick = 0

        # child of SimStrategy. Holds max num ticks, etc.
        self.ss = ss

        # agent instances. Holds state for each agent
        self.agents = AgentDict()  # agent_name : Agent instance

        # extra-agenent state variables, to track metrics. Child of Kpis
        self.kpis = None

    def takeStep(self) -> None:
        """This happens once per tick"""
        # update agents
        for agent in list(self.agents.values()):
            agent.takeStep(self)

        # update global state values
        self.kpis.takeStep(self)

    # ==============================================================
    # basic agent management
    def getAgent(self, name: str):
        return self.agents[name]

    def allAgents(self):
        return set(self.agents.values())

    def numAgents(self) -> int:
        return len(self.agents)

    def addAgent(self, agent):
        assert agent.name not in self.agents, "have an agent with this name"
        self.agents[agent.name] = agent
