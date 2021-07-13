import math
from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_DAY, S_PER_HOUR

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        #===set base-class values we want for this netlist====
        self.setTimeStep(S_PER_HOUR)
        max_days = 10
        self.setMaxTicks(max_days * S_PER_DAY / self.time_step + 1)

        #===new attributes specific to this netlist===
        #when publisher is created
        self.pub_init_OCEAN = 10000.0

        #for pool creation
        self.OCEAN_init = 1000.0
        self.OCEAN_stake = 200.0
        self.DT_init = 100.0
        self.DT_stake = 20.0
        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0

        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0
