"""Strategies hold 'magic numbers' related to running sim engine"""
import logging

from enforce_typing import enforce_types

from util.constants import S_PER_MIN, S_PER_HOUR, S_PER_DAY, S_PER_MONTH, S_PER_YEAR
from util.strutil import StrMixin

log = logging.getLogger("simstrategy")


@enforce_types
class SimStrategyBase(StrMixin):
    def __init__(self):
        # seconds per time step (tick)
        self.time_step: int = S_PER_HOUR  # type:ignore

        # max # time steps (ticks) to run until
        self.max_ticks = 1

        # how often to log to stdout and to csv (seconds)
        self.log_interval = S_PER_DAY

    def setTimeStep(self, time_step: int):
        """How many seconds are there in each time step (tick)?"""
        self.time_step = time_step

    def setMaxTicks(self, max_ticks: int):
        """What's the max # time steps (ticks) to run until?"""
        self.max_ticks = max_ticks

    def setMaxTime(self, val: int, unit: str):
        """Convenience function set max_ticks according to a time unit.
        Examples:
        val = 4, unit = 'hours' --> max time is 4 hours
        val = 10, unit = 'years' --> max time is 10 years
        Units may be: ticks, hours, days, months, years
        """
        if unit == "ticks":
            max_ticks = val
            self.max_ticks = max_ticks
        elif unit in ["min", "minutes"]:
            max_hours = val
            self.max_ticks = max_hours * S_PER_MIN / self.time_step + 1
        elif unit == "hours":
            max_hours = val
            self.max_ticks = max_hours * S_PER_HOUR / self.time_step + 1
        elif unit == "days":
            max_days = val
            self.max_ticks = max_days * S_PER_DAY / self.time_step + 1
        elif unit == "months":
            max_months = val
            self.max_ticks = max_months * S_PER_MONTH / self.time_step + 1
        elif unit == "years":
            max_years = val
            self.max_ticks = max_years * S_PER_YEAR / self.time_step + 1
        else:
            raise ValueError(unit)

    def setLogInterval(self, log_interval: int):
        """How often to log to stdout and to csv? (seconds)"""
        self.log_interval = log_interval
