from typing import List
from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_HOUR


@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        # ==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(100, "days")
        self.setLogInterval(10 * S_PER_HOUR)

        # publisher
        self.publisher_init_OCEAN = 10000.0

        # creating DT params
        self.DT_init = 100.0

        # pool params
        self.DT_stake = 50.0
        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0
        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0

        # consumer
        self.consumer_init_OCEAN = 10000.0

        # staker
        self.staker_init_OCEAN = 10000.0

        # speculator
        self.speculator_init_OCEAN = 10000.0

        # malicious Publisher
        self.maliciousPublisher_init_OCEAN = 10000.0
        self.m_DT_init = 100.0
        self.m_DT_stake = 50.0
