from enforce_typing import enforce_types

from engine import SimStrategyBase
from util.constants import S_PER_HOUR, S_PER_DAY


@enforce_types
class SimStrategy(
    SimStrategyBase.SimStrategyBase
):  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super().__init__()

        # ==baseline
        self.setTimeStep(S_PER_HOUR)
        self.setMaxTime(60, "days")
        self.setLogInterval(12 * S_PER_HOUR)

        # data publisher
        self.publisher_init_OCEAN = 5000.0
        self.publisher_DT_cap = 1000.0
        self.publisher_vested_amount = 100.0
        self.publisher_s_between_create = 1 * S_PER_DAY
        self.publisher_s_between_unstake = 500 * S_PER_DAY
        self.publisher_s_between_sellDT = 100 * S_PER_DAY

        # data consumer
        self.consumer_init_OCEAN = 5000.0
        self.consumer_s_between_buys = 3 * S_PER_DAY
        self.consumer_profit_margin_on_consume = 0.2

        # staker-speculator
        self.staker_init_OCEAN = 5000.0
        # self.staker_s_between_speculates = 8 * S_PER_HOUR
        self.staker_s_between_speculates = 1 * S_PER_DAY

        # speculator
        self.speculator_init_OCEAN = 5000.0
        self.speculator_s_between_speculates = 3 * S_PER_DAY

        # malicious publisher
        # self.buySellRobot_init_OCEAN = 5000.0
        # self.buysell_s_between_speculates = 6 * S_PER_HOUR

        # malicious publisher
        # self.mal_init_OCEAN = 5000.0
        # self.mal_DT_cap = 1000.0
        # self.mal_vested_amount = 100.0
        # self.mal_s_between_create = 2 * S_PER_DAY
        # self.mal_s_between_unstake = 1 * S_PER_HOUR
        # self.mal_s_between_sellDT = 1 * S_PER_HOUR
        # self.mal_s_wait_to_rug = 5 * S_PER_DAY
        # self.mal_s_rug_time = 2 * S_PER_DAY
