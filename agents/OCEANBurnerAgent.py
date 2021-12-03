from enforce_typing import enforce_types

from engine import AgentBase


@enforce_types
class OCEANBurnerAgent(AgentBase.AgentBaseNoEvm):
    def takeStep(self, state):
        if self.USD() > 0.0:
            # OCEAN price will go up as we buy. Reflect it here.
            nloops = 10
            USD_spend_per_loop = self.USD() / float(nloops)
            for _ in range(nloops):
                price = state.OCEANprice()  # a func of supply
                OCEAN = USD_spend_per_loop / price
                state._total_OCEAN_burned += OCEAN
                state._total_OCEAN_burned_USD += USD_spend_per_loop

            self._wallet.withdrawUSD(self.USD())  # we've spent the USD!
