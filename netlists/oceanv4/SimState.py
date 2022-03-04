from typing import Set, List

from enforce_typing import enforce_types

from agents.PublisherAgent import (
    PublisherAgentV4,
    PublisherStrategyV4,
)
from agents.SpeculatorAgent import SpeculatorAgentV4, StakerspeculatorAgentV4

from engine import SimStateBase, AgentBase
from .KPIs import KPIs
from .SimStrategy import SimStrategy


@enforce_types
class SimState(SimStateBase.SimStateBase):
    def __init__(self, ss=None):
        # initialize self.tick, ss, agents, kpis
        super().__init__(ss)

        # now, fill in actual values for ss, agents, kpis
        if self.ss is None:
            self.ss = SimStrategy()
        ss = self.ss  # for convenience as we go forward

        # wire up the circuit
        new_agents: Set[AgentBase.AgentBase] = set()

        pub_ss = PublisherStrategyV4(
            DT_cap=self.ss.publisher_DT_cap,
            vested_amount=self.ss.publisher_vested_amount,
            # pool_weight_DT=self.ss.publisher_pool_weight_DT,
            # pool_weight_OCEAN=self.ss.publisher_pool_weight_OCEAN,
            s_between_create=self.ss.publisher_s_between_create,
            s_between_unstake=self.ss.publisher_s_between_unstake,
            s_between_sellDT=self.ss.publisher_s_between_sellDT,
            is_malicious=False,
        )
        new_agents.add(
            PublisherAgentV4(
                name="publisher",
                USD=0.0,
                OCEAN=self.ss.publisher_init_OCEAN,
                pub_ss=pub_ss,
            )
        )

        # mal_pub_ss = PublisherStrategyV4(
        #     DT_cap=self.ss.mal_DT_cap,
        #     vested_amount=self.ss.mal_vested_amount,
        #     s_between_create=self.ss.mal_s_between_create,
        #     s_between_unstake=self.ss.mal_s_between_unstake,
        #     s_between_sellDT=self.ss.mal_s_between_sellDT,
        #     is_malicious=True,
        #     s_wait_to_rug=self.ss.mal_s_wait_to_rug,
        #     s_rug_time=self.ss.mal_s_rug_time,
        # )
        # new_agents.add(
        #     PublisherAgentV4(
        #         name="maliciousPublisher",
        #         USD=0.0,
        #         OCEAN=self.ss.mal_init_OCEAN,
        #         pub_ss=mal_pub_ss,
        #     )
        # )

        # new_agents.add(
        #     DataconsumerAgentV4(
        #         name="consumer",
        #         USD=0.0,
        #         OCEAN=self.ss.consumer_init_OCEAN,
        #         s_between_buys=self.ss.consumer_s_between_buys,
        #         profit_margin_on_consume=self.ss.consumer_profit_margin_on_consume,
        #     )
        # )

        new_agents.add(
            StakerspeculatorAgentV4(
                name="stakerSpeculator",
                USD=0.0,
                OCEAN=self.ss.staker_init_OCEAN,
                s_between_speculates=self.ss.staker_s_between_speculates,
            )
        )

        new_agents.add(
            SpeculatorAgentV4(
                name="speculator",
                USD=0.0,
                OCEAN=self.ss.speculator_init_OCEAN,
                s_between_speculates=self.ss.speculator_s_between_speculates,
            )
        )

        for agent in new_agents:
            self.agents[agent.name] = agent

        # kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step)

        # pools that were rug-pulled by a malicious publisher. Some agents
        # watch for 'state.rugged_pools' and act accordingly.
        self.rugged_pools: List[str] = []
