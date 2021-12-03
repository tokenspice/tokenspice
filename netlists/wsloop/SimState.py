from typing import Set

from enforce_typing import enforce_types

from agents import MinterAgents
from agents.GrantGivingAgent import GrantGivingAgent
from agents.GrantTakingAgent import GrantTakingAgent
from agents.MarketplacesAgent import MarketplacesAgent
from agents.OCEANBurnerAgent import OCEANBurnerAgent
from agents.RouterAgent import RouterAgent
from engine import AgentBase, SimStateBase
from util import valuation
from util.constants import S_PER_MONTH, S_PER_DAY
from .KPIs import KPIs
from .SimStrategy import SimStrategy


@enforce_types
class SimState(
    SimStateBase.SimStateBase
):  # pylint: disable=too-many-instance-attributes
    def __init__(self, ss=None):
        # initialize self.tick, ss, agents, kpis
        super().__init__(ss)

        # now, fill in actual values for ss, agents, kpis
        if self.ss is None:
            self.ss = SimStrategy()
        ss = self.ss  # for convenience as we go forward

        # used to manage names
        self._next_free_marketplace_number = 0

        # used to add agents
        self._marketplace_tick_previous_add = 0

        # as ecosystem improves, these parameters may change
        self._total_OCEAN_minted: float = 0.0
        self._total_OCEAN_burned: float = 0.0
        self._total_OCEAN_burned_USD: float = 0.0
        self._speculation_valuation = ss._init_speculation_valuation

        # Instantiate and connnect agent instances. "Wire up the circuit"
        new_agents: Set[AgentBase.AgentBase] = set()

        # Note: could replace MarketplacesAgent with DataecosystemAgent, for a
        # higher-fidelity simulation using EVM agents
        new_agents.add(
            MarketplacesAgent(
                name="marketplaces1",
                USD=0.0,
                OCEAN=0.0,
                toll_agent_name="opc_address",
                n_marketplaces=float(ss.init_n_marketplaces),
                sales_per_marketplace_per_s=20e3 / S_PER_MONTH,  # magic number
                time_step=self.ss.time_step,
            )
        )

        new_agents.add(
            RouterAgent(
                name="opc_address",
                USD=0.0,
                OCEAN=0.0,
                receiving_agents={
                    "ocean_dao": self.ss.percentToOceanDao,
                    "opc_burner": self.ss.percentToBurn,
                },
            )
        )

        new_agents.add(OCEANBurnerAgent(name="opc_burner", USD=0.0, OCEAN=0.0))

        # func = MinterAgents.ExpFunc(H=4.0)
        func = MinterAgents.RampedExpFunc(
            H=4.0, T0=0.5, T1=1.0, T2=1.4, T3=3.0, M1=0.10, M2=0.25, M3=0.50
        )
        new_agents.add(
            MinterAgents.OCEANFuncMinterAgent(
                name="ocean_51",
                receiving_agent_name="ocean_dao",
                total_OCEAN_to_mint=ss.UNMINTED_OCEAN_SUPPLY,
                s_between_mints=S_PER_DAY,
                func=func,
            )
        )

        new_agents.add(
            GrantGivingAgent(
                name="opf_treasury_for_ocean_dao",
                USD=0.0,
                OCEAN=ss.OPF_TREASURY_OCEAN_FOR_OCEAN_DAO,
                receiving_agent_name="ocean_dao",
                s_between_grants=S_PER_MONTH,
                n_actions=12 * 3,
            )
        )

        new_agents.add(
            GrantGivingAgent(
                name="opf_treasury_for_opf_mgmt",
                USD=ss.OPF_TREASURY_USD,
                OCEAN=ss.OPF_TREASURY_OCEAN_FOR_OPF_MGMT,
                receiving_agent_name="opf_mgmt",
                s_between_grants=S_PER_MONTH,
                n_actions=12 * 3,
            )
        )

        new_agents.add(
            GrantGivingAgent(
                name="bdb_treasury",
                USD=ss.BDB_TREASURY_USD,
                OCEAN=ss.BDB_TREASURY_OCEAN,
                receiving_agent_name="bdb_mgmt",
                s_between_grants=S_PER_MONTH,
                n_actions=17,
            )
        )

        new_agents.add(
            RouterAgent(
                name="ocean_dao",
                receiving_agents={"opc_workers": funcOne},
                USD=0.0,
                OCEAN=0.0,
            )
        )

        new_agents.add(
            RouterAgent(
                name="opf_mgmt",
                receiving_agents={"opc_workers": funcOne},
                USD=0.0,
                OCEAN=0.0,
            )
        )

        new_agents.add(
            RouterAgent(
                name="bdb_mgmt",
                receiving_agents={"bdb_workers": funcOne},
                USD=0.0,
                OCEAN=0.0,
            )
        )

        new_agents.add(GrantTakingAgent(name="opc_workers", USD=0.0, OCEAN=0.0))

        new_agents.add(GrantTakingAgent(name="bdb_workers", USD=0.0, OCEAN=0.0))

        for agent in new_agents:
            self.agents[agent.name] = agent

        # track certain metrics over time, so that we don't have to load
        self.kpis = KPIs(self.ss)

    def takeStep(self) -> None:
        """This happens once per tick"""
        # update agents
        # update kpis
        super().takeStep()

        # update global state values
        self._updateSpeculationValuation()

    # ==============================================================
    def grantTakersSpentAtTick(self) -> float:
        return sum(
            agent.spentAtTick()
            for agent in self.agents.values()
            if isinstance(agent, GrantTakingAgent)
        )

    # ==============================================================
    def OCEANprice(self) -> float:
        """Estimated price of $OCEAN token, in USD"""
        price = valuation.OCEANprice(self.overallValuation(), self.OCEANsupply())
        assert price > 0.0
        return price

    # ==============================================================
    def _updateSpeculationValuation(self):
        self._speculation_valuation *= (
            1.0
            + self.ss._percent_increase_speculation_valuation_per_s * self.ss.time_step
        )

    def overallValuation(self) -> float:  # in USD
        # fundamental valuation acts as a lower bound.
        # sum() is too optimistic, so use max()
        v = max(self.fundamentalsValuation(), self.speculationValuation())
        assert v > 0.0
        return v

    def fundamentalsValuation(self) -> float:  # in USD
        sales = self.kpis.annualNetworkRevenueNow()
        return self.ss.fundamentalsValuation(sales)

    def speculationValuation(self) -> float:  # in USD
        return self._speculation_valuation

    # ==============================================================
    def OCEANsupply(self) -> float:
        """Current OCEAN token supply"""
        return self.initialOCEAN() + self.totalOCEANminted() - self.totalOCEANburned()

    def initialOCEAN(self) -> float:
        return self.ss.INIT_OCEAN_SUPPLY

    def totalOCEANminted(self) -> float:
        return self._total_OCEAN_minted

    def totalOCEANburned(self) -> float:
        return self._total_OCEAN_burned

    def totalOCEANburnedUSD(self) -> float:
        return self._total_OCEAN_burned_USD


def funcOne():
    return 1.0
