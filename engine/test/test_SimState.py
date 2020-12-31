from enforce_typing import enforce_types # type: ignore[import]

from agents import MinterAgents
from engine import SimState, SimStrategy
from util.constants import S_PER_DAY

@enforce_types
def testBasicInit():
    ss = SimStrategy.SimStrategy()
    state = SimState.SimState(ss)
    assert isinstance(state.ss, SimStrategy.SimStrategy)
    assert state.tick == 0

    assert state.numAgents() > 0

@enforce_types
def testGetAgent():
    ss = SimStrategy.SimStrategy()
    state = SimState.SimState(ss)
    assert id(state.getAgent("ocean_dao")) == id(state.agents["ocean_dao"])

@enforce_types
def testMoneyFlow1():
    ss = SimStrategy.SimStrategy()
    state = SimState.SimState(ss)
    assert hasattr(state, '_percent_burn')
    state._percent_burn = 0.20

    #opc_address -> (opc_burner, ocean_dao)
    state.getAgent("opc_address").receiveUSD(100.0)
    state.getAgent("opc_address").takeStep(state)
    assert state.getAgent("opc_burner").USD() == (0.20 * 100.0)
    assert state.getAgent("ocean_dao").USD() == (0.80 * 100.0)

    #ocean_dao -> opc_workers
    state.getAgent("ocean_dao").takeStep(state)
    assert state.getAgent("opc_workers").USD() == (0.80 * 100.0)

    #ocean_dao spends
    state.getAgent("opc_workers").takeStep(state)
    assert state.getAgent("opc_workers").USD() == 0.0

@enforce_types
def testMoneyFlow2():
    ss = SimStrategy.SimStrategy()
    state = SimState.SimState(ss)
    state.getAgent("ocean_51")._func = MinterAgents.ExpFunc(H=4.0)

    #send from money 51% minter -> ocean_dao
    o51_OCEAN_t0 = state.getAgent("ocean_51").OCEAN()
    dao_OCEAN_t0 = state.getAgent("ocean_dao").OCEAN()

    assert o51_OCEAN_t0 == 0.0
    assert dao_OCEAN_t0 == 0.0
    assert state._total_OCEAN_minted == 0.0

    #ocean_51 should disburse at tick=1
    state.getAgent("ocean_51").takeStep(state); state.tick += 1
    state.getAgent("ocean_51").takeStep(state); state.tick += 1

    o51_OCEAN_t1 = state.getAgent("ocean_51").OCEAN()
    dao_OCEAN_t1 = state.getAgent("ocean_dao").OCEAN()

    assert o51_OCEAN_t1 == 0.0 
    assert dao_OCEAN_t1 > 0.0
    assert state._total_OCEAN_minted > 0.0
    assert state._total_OCEAN_minted == dao_OCEAN_t1
