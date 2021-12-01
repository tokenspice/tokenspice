from typing import List
from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        # ==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(100, "days")
        self.setLogInterval(10 * S_PER_HOUR)

        # data publisher
        self.publisher_init_OCEAN = 10000.0
        self.DT_init = 100.0
        self.DT_stake = 50.0
        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0
        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0

        # data consumer
        self.consumer_init_OCEAN = 10000.0

        # staker-speculator
        self.staker_init_OCEAN = 10000.0
        self.staker_s_between_speculates = 8 * S_PER_HOUR

        # speculator
        self.speculator_init_OCEAN = 10000.0

        # malicious publisher
        self.mal_init_OCEAN = 10000.0
        self.mal_DT_init = 100.0
        self.mal_DT_stake = 50.0
        self.mal_pool_weight_DT = self.pool_weight_DT
        self.mal_pool_weight_OCEAN = self.pool_weight_OCEAN
        assert (self.mal_pool_weight_DT + self.mal_pool_weight_OCEAN) == 10.0
        self.mal_s_between_create = 10 * S_PER_DAY
        self.mal_s_between_unstake = 1 * S_PER_HOUR
        self.mal_s_between_sellDT = 1 * S_PER_HOUR
        self.mal_s_wait_to_rug = 5 * S_PER_DAY
        self.mal_s_rug_time = 1 * S_PER_DAY
