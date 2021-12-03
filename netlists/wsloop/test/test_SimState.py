from enforce_typing import enforce_types

from agents import MinterAgents
from ..SimState import SimState


@enforce_types
def testSimState_MoneyFlow1():
    state = SimState()
    assert hasattr(state.ss, "_percent_burn")
    state.ss._percent_burn = 0.20
    assert state.ss.percentToBurn() == 0.20

    # opc_address -> (opc_burner, ocean_dao)
    state.getAgent("opc_address").receiveUSD(100.0)
    state.getAgent("opc_address").takeStep(state)
    assert state.getAgent("opc_burner").USD() == (0.20 * 100.0)
    assert state.getAgent("ocean_dao").USD() == (0.80 * 100.0)

    # ocean_dao -> opc_workers
    state.getAgent("ocean_dao").takeStep(state)
    assert state.getAgent("opc_workers").USD() == (0.80 * 100.0)

    # ocean_dao spends
    state.getAgent("opc_workers").takeStep(state)
    assert state.getAgent("opc_workers").USD() == 0.0


@enforce_types
def testSimState_MoneyFlow2():
    state = SimState()
    state.getAgent("ocean_51")._func = MinterAgents.ExpFunc(H=4.0)

    # send from money 51% minter -> ocean_dao
    o51_OCEAN_t0 = state.getAgent("ocean_51").OCEAN()
    dao_OCEAN_t0 = state.getAgent("ocean_dao").OCEAN()

    assert o51_OCEAN_t0 == 0.0
    assert dao_OCEAN_t0 == 0.0
    assert state._total_OCEAN_minted == 0.0

    # ocean_51 should disburse at tick=1
    state.getAgent("ocean_51").takeStep(state)
    state.tick += 1
    state.getAgent("ocean_51").takeStep(state)
    state.tick += 1

    o51_OCEAN_t1 = state.getAgent("ocean_51").OCEAN()
    dao_OCEAN_t1 = state.getAgent("ocean_dao").OCEAN()

    assert o51_OCEAN_t1 == 0.0
    assert dao_OCEAN_t1 > 0.0
    assert state._total_OCEAN_minted > 0.0
    assert state._total_OCEAN_minted == dao_OCEAN_t1
