from typing import Set, List

from enforce_typing import enforce_types

from agents.DataconsumerAgent import DataconsumerAgent
from agents.PublisherAgent import PublisherAgent, PublisherStrategy
from agents.SpeculatorAgent import SpeculatorAgent, StakerspeculatorAgent

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

        pub_ss = PublisherStrategy(
            DT_init=self.ss.publisher_DT_init,
            DT_stake=self.ss.publisher_DT_stake,
            pool_weight_DT=self.ss.publisher_pool_weight_DT,
            pool_weight_OCEAN=self.ss.publisher_pool_weight_OCEAN,
            s_between_create=self.ss.publisher_s_between_create,
            s_between_unstake=self.ss.publisher_s_between_unstake,
            s_between_sellDT=self.ss.publisher_s_between_sellDT,
            is_malicious=False,
        )
        new_agents.add(
            PublisherAgent(
                name="publisher",
                USD=0.0,
                OCEAN=self.ss.publisher_init_OCEAN,
                pub_ss=pub_ss,
            )
        )

        new_agents.add(
            DataconsumerAgent(
                name="consumer",
                USD=0.0,
                OCEAN=self.ss.consumer_init_OCEAN,
                s_between_buys=self.ss.consumer_s_between_buys,
                profit_margin_on_consume=self.ss.consumer_profit_margin_on_consume,
            )
        )

        new_agents.add(
            StakerspeculatorAgent(
                name="stakerSpeculator",
                USD=0.0,
                OCEAN=self.ss.staker_init_OCEAN,
                s_between_speculates=self.ss.staker_s_between_speculates,
            )
        )

        new_agents.add(
            SpeculatorAgent(
                name="speculator",
                USD=0.0,
                OCEAN=self.ss.speculator_init_OCEAN,
                s_between_speculates=self.ss.speculator_s_between_speculates,
            )
        )

        mal_pub_ss = PublisherStrategy(
            DT_init=self.ss.mal_DT_init,
            DT_stake=self.ss.mal_DT_stake,
            pool_weight_DT=self.ss.mal_pool_weight_DT,
            pool_weight_OCEAN=self.ss.mal_pool_weight_OCEAN,
            s_between_create=self.ss.mal_s_between_create,
            s_between_unstake=self.ss.mal_s_between_unstake,
            s_between_sellDT=self.ss.mal_s_between_sellDT,
            is_malicious=True,
            s_wait_to_rug=self.ss.mal_s_wait_to_rug,
            s_rug_time=self.ss.mal_s_rug_time,
        )
        new_agents.add(
            PublisherAgent(
                name="maliciousPublisher",
                USD=0.0,
                OCEAN=self.ss.mal_init_OCEAN,
                pub_ss=mal_pub_ss,
            )
        )

        for agent in new_agents:
            self.agents[agent.name] = agent

        # kpis is defined in this netlist module
        self.kpis = KPIs(self.ss.time_step)

        # pools that were rug-pulled by a malicious publisher. Some agents
        # watch for 'state.rugged_pools' and act accordingly.
        self.rugged_pools: List[str] = []
