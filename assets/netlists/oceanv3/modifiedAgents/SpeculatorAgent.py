from enforce_typing import enforce_types
import random
from assets.agents import SpeculatorAgent
from assets.agents.PoolAgent import PoolAgent
from engine.AgentBase import AgentBase
from web3engine import bfactory, bpool, datatoken, dtfactory, globaltokens
from web3tools.web3util import toBase18
from util.constants import S_PER_DAY, S_PER_HOUR

@enforce_types
class SpeculatorAgent(SpeculatorAgent.SpeculatorAgent):

    def _speculateAction(self, state):
        pool_agents = state.agents.filterToPool()
        # exclude rugged pool
        for pool_name in state.ss.rugged_pools:
            try:
                del pool_agents[pool_name]
            except:
                pass
        
        pool_agents = pool_agents.values()
        assert pool_agents, "need pools to be able to speculate"
        
        pool_agent = random.choice(list(pool_agents))
        pool = pool_agent.pool

        DT = self.DT(pool_agent.datatoken)
        datatoken = pool_agent.datatoken

        max_OCEAN_allow = self.OCEAN()
        if DT > 0.0 and random.random() < 0.50: #magic number
            DT_sell_amt = 1.0 * DT #magic number
            self._wallet.sellDT(pool,datatoken, DT_sell_amt)
            
        else:
            DT_buy_amt = 1.0 #magic number
            self._wallet.buyDT(pool, datatoken, DT_buy_amt, max_OCEAN_allow)