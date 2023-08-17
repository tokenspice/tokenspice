from enforce_typing import enforce_types

from agents.RouterAgent import RouterAgent
from engine import AgentBase, SimStateBase, SimStrategyBase
from util.constants import S_PER_DAY, S_PER_MONTH

SimState = SimStateBase.SimStateBase
SimStrategy = SimStrategyBase.SimStrategyBase


@enforce_types
def test_RouterAgent():
    ss = SimStrategy()
    ss.time_step = S_PER_DAY
    state = SimState(ss)

    class FooAgent(AgentBase.AgentBaseNoEvm):
        def takeStep(self, state):
            pass

    state.agents["a1"] = a1 = FooAgent("a1", 0.0, 0.0)
    state.agents["a2"] = a2 = FooAgent("a2", 0.0, 0.0)

    def perc_f1():
        return 0.2

    def perc_f2():
        return 0.8

    am = RouterAgent("moneyrouter", 1.0, 10.0, {"a1": perc_f1, "a2": perc_f2})

    assert not am._USD_per_tick
    assert not am._OCEAN_per_tick
    assert am._tickOneMonthAgo(state) == (0)
    assert am.monthlyUSDreceived(state) == (0.0)
    assert am.monthlyOCEANreceived(state) == (0.0)

    am.takeStep(state)
    assert a1.USD() == (0.2 * 1.0)
    assert a2.USD() == (0.8 * 1.0)

    assert a1.OCEAN() == (0.2 * 10.0)
    assert a2.OCEAN() == (0.8 * 10.0)

    assert am._USD_per_tick == ([1.0])
    assert am._OCEAN_per_tick == ([10.0])
    assert am._tickOneMonthAgo(state) == (0)
    assert am.monthlyUSDreceived(state) == (1.0)
    assert am.monthlyOCEANreceived(state) == (10.0)

    am.takeStep(state)
    state.tick += 1
    am.takeStep(state)
    state.tick += 1

    assert am._USD_per_tick == ([1.0, 0.0, 0.0])
    assert am._OCEAN_per_tick == ([10.0, 0.0, 0.0])
    assert am._tickOneMonthAgo(state) == (0)
    assert am.monthlyUSDreceived(state) == (1.0)
    assert am.monthlyOCEANreceived(state) == (10.0)

    # make a month pass, give $
    ticks_per_mo = int(S_PER_MONTH / float(state.ss.time_step))
    for _ in range(ticks_per_mo):
        am.receiveUSD(2.0)
        am.receiveOCEAN(3.0)
        am.takeStep(state)
        state.tick += 1
    assert am._tickOneMonthAgo(state) > 1  # should be 2
    assert am.monthlyUSDreceived(state) == (2.0 * ticks_per_mo)
    assert am.monthlyOCEANreceived(state) == (3.0 * ticks_per_mo)

    # make another month pass, don't give $ this time
    for _ in range(ticks_per_mo + 1):
        am.takeStep(state)
        state.tick += 1
    assert am._tickOneMonthAgo(state) > (1 + ticks_per_mo)
    assert am.monthlyUSDreceived(state) == (0.0)
    assert am.monthlyOCEANreceived(state) == (0.0)
