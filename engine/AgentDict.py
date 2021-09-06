from enforce_typing import enforce_types

from assets.agents.PublisherAgent import PublisherAgent
from assets.agents.PoolAgent import PoolAgent
from assets.agents.StakerspeculatorAgent import StakerspeculatorAgent
from assets.agents.DataconsumerAgent import DataconsumerAgent

@enforce_types
class AgentDict(dict):
    """Dict of Agent"""
    def __init__(self,*arg,**kw):
        """
        Extend the dict object to get the best of both worlds (object/dict)
        """
        super(AgentDict, self).__init__(*arg, **kw)
    
    def filterByNonzeroStake(self, agent):
        """Which pools has 'agent' staked on?"""
        return AgentDict({pool_agent.name : pool_agent
                          for pool_agent in self.filterToPool().values()
                          if agent.BPT(pool_agent.pool) > 0.0})
    
    def filterToPool(self):
        return self.filterByClass(PoolAgent)

    def filterToPublisher(self):
        return self.filterByClass(PublisherAgent)

    def filterToStakerspeculator(self):
        return self.filterByClass(StakerspeculatorAgent)

    def filterToDataconsumer(self):
        return self.filterByClass(DataconsumerAgent)
    
    def filterByClass(self, _class):
        return AgentDict({agent.name : agent
                          for agent in self.values()
                          if isinstance(agent, _class)})

    def agentByAddress(self, address):
        for agent in self.values():
            if agent.address == address:
                return agent
        return None

