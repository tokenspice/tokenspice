"""Strategies hold 'magic numbers' related to running sim engine"""
import logging
log = logging.getLogger('simstrategy')

from enforce_typing import enforce_types

from util.constants import *
from util.strutil import StrMixin
    
@enforce_types
class SimStrategyBase(StrMixin):
    
    def __init__(self):
        #seconds per tick
        self.time_step: int = S_PER_HOUR
        
        #total sim time
        max_days = 10
        self.max_ticks = max_days * S_PER_DAY / self.time_step + 1

    def setTimeStep(self, time_step: int):
        self.time_step = time_step
        
    def setMaxTicks(self, max_ticks: int):
        self.max_ticks = max_ticks
