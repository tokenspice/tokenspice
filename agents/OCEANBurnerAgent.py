import logging
log = logging.getLogger('agents')

from enforce_typing import enforce_types # type: ignore[import]

from agents.BaseAgent import BaseAgent

@enforce_types
class OCEANBurnerAgent(BaseAgent):
    def takeStep(self, state):
        if self.USD() > 0.0:
            #OCEAN price will go up as we buy. Reflect it here.
            nloops = 10
            USD_spend_per_loop = self.USD() / float(nloops)
            for i in range(nloops):
                price = state.OCEANprice() #a func of supply
                OCEAN = USD_spend_per_loop / price
                state._total_OCEAN_burned += OCEAN
                state._total_OCEAN_burned_USD += USD_spend_per_loop

            self._wallet.withdrawUSD(self.USD()) #we've spent the USD!
