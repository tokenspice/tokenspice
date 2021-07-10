import logging
log = logging.getLogger('kpis')

from abc import ABC, abstractmethod
from enforce_typing import enforce_types

@enforce_types
class KPIsBase(ABC):
    def __init__(self, time_step: int):
        self._time_step = time_step #seconds per tick

    @abstractmethod
    def takeStep(self, state):
        pass

    @abstractmethod
    def tick(self) -> int:
        """# ticks that have elapsed since the beginning of the run"""
        pass

    def elapsedTime(self) -> int:
        """Elapsed time (seconds) since the beginning of the run"""
        return self.tick() * self._time_step
        
