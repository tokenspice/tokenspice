from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        #==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(10, 'days')

        #==attributes specific to this netlist
        self.granter_init_USD: float = 0.0
        self.granter_init_OCEAN: float = 1.0
        self.granter_s_between_grants: int = S_PER_DAY*3
        self.granter_n_actions: int = 4
