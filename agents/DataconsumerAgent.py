from enforce_typing import enforce_types
import random

from agents.BaseAgent import BaseAgent
from web3engine import bpool, datatoken, globaltokens
from web3tools.web3util import fromBase18, toBase18
from util import constants             

@enforce_types
class DataconsumerAgent(BaseAgent):
    def __init__(self, name: str, USD: float, OCEAN: float):
        super().__init__(name, USD, OCEAN)
        
        self._s_since_buy = 0
        self._s_between_buys = 3 * constants.S_PER_DAY #magic number
        
    def takeStep(self, state) -> None:
        self._s_since_buy += state.ss.time_step
        
        if self._doBuy(state):
            self._s_since_buy = 0
            self._buy(state)

    def _doBuy(self, state):
        cand_pool_agents = self._candPoolAgents(state)
        if not cand_pool_agents:
            return False
        else:
            return self._s_since_buy >= self._s_between_buys

    def _candPoolAgents(self, state):
        """Pools that this agent can afford to buy 1.0 datatokens from,
        at least based on a first approximation. 
        """
        OCEAN_address = globaltokens.OCEAN_address()
        OCEAN = self.OCEAN()
        all_pool_agents = state.agents.filterToPool().values()
        cand_pool_agents = []
        for pool_agent in all_pool_agents:
            pool = pool_agent.pool
            DT_address = pool_agent.datatoken_address
            
            pool_DT_balance_base = pool.getBalance_base(DT_address)
            pool_OCEAN_balance_base = pool.getBalance_base(OCEAN_address)
            pool_DT_weight_base = pool.getDenormalizedWeight_base(DT_address)
            pool_OCEAN_weight_base = pool.getDenormalizedWeight_base(OCEAN_address)
            pool_swapFee_base = pool.getSwapFee_base()

            DT_amount_out_base = toBase18(1.0)

            spotPriceBefore_base = pool.getSpotPrice_base(
                tokenIn_address=OCEAN_address,
                tokenOut_address=DT_address)
            OCEANamountIn_base = pool.calcInGivenOut_base(
                tokenBalanceIn_base=pool_OCEAN_balance_base,
                tokenWeightIn_base=pool_OCEAN_weight_base,
                tokenBalanceOut_base=pool_DT_balance_base,
                tokenWeightOut_base=pool_DT_weight_base,
                tokenAmountOut_base=DT_amount_out_base,
                swapFee_base=pool_swapFee_base)

            if OCEANamountIn_base < OCEAN:
                cand_pool_agents.append(pool)
                
        return cand_pool_agents

    def _buy(self, state):
        """Buy, and consume dataset"""
        OCEAN_address = globaltokens.OCEAN_address()
        OCEAN = self.OCEAN()
        OCEAN_base = self._wallet._OCEAN_base()
        DT_amount_out_base = toBase18(1.0)
        
        cand_pool_agents = self._candPoolAgents()
        assert cand_pool_agents
        random.shuffle(cand_pool_agents)

        #FIXME: there will be times when slippage is sufficiently high that
        # the data consumer won't be able to successfully buy the DT.
        # In that case, should pick the second choice in cand_pool_agents. Etc.
        pool_agent = cand_pool_agents[0]
        pool = pool_agent.pool
        DT_address = pool_agent.datatoken_address
        
        pool.swapExactAmountOut(
            tokenIn_address=OCEAN_address,
            maxAmountIn_base=OCEAN_base,
            tokenOut_address=DT_address,
            tokenAmountOut_base=DT_amount_out_base,
            maxPrice_base=constants.HUGEINT,
            from_wallet=self._wallet._web3wallet)
        
        self._wallet.resetCachedInfo()
        
