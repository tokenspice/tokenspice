from enforce_typing import enforce_types

from ..SimStrategy import SimStrategy


@enforce_types
def test1():
    # very lightweight testing: just on attribute names and basic (>0)
    ss = SimStrategy()

    assert ss.time_step > 0
    assert ss.max_ticks > 0
    assert ss.log_interval > 0

    assert ss.publisher_init_OCEAN > 0.0
    assert ss.publisher_DT_init > 0.0
    assert ss.publisher_DT_stake > 0.0
    assert ss.publisher_pool_weight_DT > 0.0
    assert ss.publisher_pool_weight_OCEAN > 0.0
    assert ss.publisher_s_between_create > 0
    assert ss.publisher_s_between_unstake > 0
    assert ss.publisher_s_between_sellDT > 0

    # data consumer
    assert ss.consumer_init_OCEAN > 0.0
    assert ss.consumer_s_between_buys > 0
    assert ss.consumer_profit_margin_on_consume > 0.0

    # staker-speculator
    assert ss.staker_init_OCEAN > 0.0
    assert ss.staker_s_between_speculates > 0

    # speculator
    assert ss.speculator_init_OCEAN > 0.0
    assert ss.speculator_s_between_speculates > 0

    # malicious publisher
    assert ss.mal_init_OCEAN > 0.0
    assert ss.mal_DT_init > 0.0
    assert ss.mal_DT_stake > 0.0
    assert ss.mal_pool_weight_DT > 0.0
    assert ss.mal_pool_weight_OCEAN > 0.0
    assert ss.mal_s_between_create > 0
    assert ss.mal_s_between_unstake > 0
    assert ss.mal_s_between_sellDT > 0
    assert ss.mal_s_wait_to_rug > 0
    assert ss.mal_s_rug_time > 0
