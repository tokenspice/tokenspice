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

        #agents
        pub_agent = PublisherAgent.PublisherAgent(
            name="pub1", USD=0.0, OCEAN=self.ss.pub_init_OCEAN)
        web3_w = pub_agent._wallet._web3wallet
        pool = self._buildPool(web3_w)
        pool_agent = PoolAgent.PoolAgent(name="pool1", pool=pool)
        
        for agent in [pub_agent, pool_agent]:
            self.agents[agent.name] = agent

        #KPIs
        self.kpis = KPIs(self.ss.time_step)
                    
    def takeStep(self) -> None:
        super().takeStep()

    def _buildPool(self, web3_w):
        #create DT
        ss = self.ss
        DT_address = dtfactory.DTFactory().createToken(
            '', 'DT1', 'DT1', toBase18(ss.DT_init),from_wallet=web3_w)
        DT = datatoken.Datatoken(DT_address)
        DT.mint(web3_w.address, toBase18(ss.DT_init), from_wallet=web3_w)

        #create pool
        OCEAN = globaltokens.OCEANtoken()
    
        p_address = bfactory.BFactory().newBPool(from_wallet=web3_w)
        pool = bpool.BPool(p_address)

        DT.approve(pool.address, toBase18(ss.DT_stake), from_wallet=web3_w)
        OCEAN.approve(pool.address, toBase18(ss.OCEAN_stake),from_wallet=web3_w)

        pool.bind(DT.address, toBase18(ss.DT_stake),
                  toBase18(ss.pool_weight_DT), from_wallet=web3_w)
        pool.bind(OCEAN.address, toBase18(ss.OCEAN_stake),
                  toBase18(ss.pool_weight_OCEAN), from_wallet=web3_w)

        pool.finalize(from_wallet=web3_w)

        return pool
