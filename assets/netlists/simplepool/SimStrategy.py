from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_HOUR

@enforce_types
class SimStrategy(SimStrategyBase.SimStrategyBase):
    def __init__(self):
        super().__init__()

        #==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(20, 'days')

        #==attributes specific to this netlist
        
        #publisher 
        self.pub_init_OCEAN = 10000.0

        #pool
        self.OCEAN_init = 1000.0
        self.OCEAN_stake = 200.0
        self.DT_init = 100.0
        self.DT_stake = 20.0
        self.pool_weight_DT = 3.0
        self.pool_weight_OCEAN = 7.0

        assert (self.pool_weight_DT + self.pool_weight_OCEAN) == 10.0
