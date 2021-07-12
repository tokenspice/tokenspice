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
        self.granter_init_USD: float = 0.0
        self.granter_init_OCEAN: float = 1.0
        self.granter_s_between_grants: int = S_PER_DAY*3
        self.granter_n_actions: int = 4
