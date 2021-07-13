from enforce_typing import enforce_types
from typing import Set

from assets.agents import PublisherAgent, PoolAgent
from engine import AgentBase, AgentWallet, SimStateBase
from .KPIs import KPIs
from .SimStrategy import SimStrategy
from util.constants import S_PER_DAY
from web3tools import web3util
from web3tools.web3util import toBase18
from web3engine import bfactory, bpool, datatoken, dtfactory, globaltokens

@enforce_types
class SimState(SimStateBase.SimStateBase):
    
    def __init__(self, ss=None):
        assert ss is None
        super().__init__(ss)

        #strategy
        self.ss = SimStrategy()

        #just a publisher agent. It will create pool agents as it goes.
        pub_agent = PublisherAgent.PublisherAgent(
            name="pub1", USD=0.0, OCEAN=self.ss.pub_init_OCEAN)
        self.agents[pub_agent.name] = pub_agent

        #KPIs
        self.kpis = KPIs(self.ss.time_step)
                    
    def takeStep(self) -> None:
        super().takeStep()
