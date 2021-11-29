from enforce_typing import enforce_types

from agents.PublisherAgent import PublisherAgent
from agents.PoolAgent import PoolAgent
from sol057.contracts.oceanv3 import oceanv3util
from util import globaltokens
from util.base18 import toBase18


@enforce_types
class v3PublisherAgent(PublisherAgent):
    def _createPoolAgent(self, state) -> PoolAgent:
        assert self.OCEAN() > 0.0, "should not call if no OCEAN"
        account = self._wallet._account
        OCEAN = globaltokens.OCEANtoken()

        # name
        pool_i = len(state.agents.filterToPool())
        dt_name = f"DT{pool_i}"
        pool_agent_name = f"pool{pool_i}"

        # new DT
        DT = self._createDatatoken(dt_name, mint_amt=state.ss.DT_init)  # magic number

        # new pool
        pool = oceanv3util.newBPool(account)

        # bind tokens & add initial liquidity
        OCEAN_bind_amt = self.OCEAN()  # magic number: use all the OCEAN
        DT_bind_amt = state.ss.DT_stake

        DT.approve(pool.address, toBase18(DT_bind_amt), {"from": account})
        OCEAN.approve(pool.address, toBase18(OCEAN_bind_amt), {"from": account})

        pool.bind(
            DT.address,
            toBase18(DT_bind_amt),
            toBase18(state.ss.pool_weight_DT),
            {"from": account},
        )
        pool.bind(
            OCEAN.address,
            toBase18(OCEAN_bind_amt),
            toBase18(state.ss.pool_weight_OCEAN),
            {"from": account},
        )

        pool.finalize({"from": account})

        # create agent
        pool_agent = PoolAgent(pool_agent_name, pool)
        state.addAgent(pool_agent)
        self._wallet.resetCachedInfo()

        return pool_agent
