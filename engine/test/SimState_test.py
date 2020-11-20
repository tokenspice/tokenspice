import logging, logging.config
logging.config.fileConfig('logging.conf')
log = logging.getLogger('simstate')

import enforce
from enforce.exceptions import RuntimeTypeError
import unittest

from engine import MinterAgents, SimState, SimStrategy
from util.constants import S_PER_DAY

@enforce.runtime_validation
class SimStateTest(unittest.TestCase):
        
    def testBasicInit(self):
        ss = SimStrategy.SimStrategy()
        state = SimState.SimState(ss)
        self.assertTrue(isinstance(state.ss, SimStrategy.SimStrategy))
        self.assertEqual(state.tick, 0)
        
        self.assertTrue(state.numAgents() > 0)
        
    def testGetAgent(self):
        ss = SimStrategy.SimStrategy()
        state = SimState.SimState(ss)
        self.assertEqual(
            id(state.getAgent("ocean_dao")),
            id(state.agents["ocean_dao"]))

    def testMoneyFlow1(self):
        ss = SimStrategy.SimStrategy()
        state = SimState.SimState(ss)
        assert hasattr(state, '_percent_burn')
        state._percent_burn = 0.20

        #opc_address -> (opc_burner, ocean_dao)
        state.getAgent("opc_address").receiveUSD(100.0)
        state.getAgent("opc_address").takeStep(state)
        self.assertEqual(state.getAgent("opc_burner").USD(), 0.20 * 100.0)
        self.assertEqual(state.getAgent("ocean_dao").USD(), 0.80 * 100.0)

        #ocean_dao -> opc_workers
        state.getAgent("ocean_dao").takeStep(state)
        self.assertEqual(state.getAgent("opc_workers").USD(), 0.80 * 100.0)
        
        #ocean_dao spends
        state.getAgent("opc_workers").takeStep(state)
        self.assertEqual(state.getAgent("opc_workers").USD(), 0.0)
        
    def testMoneyFlow2(self):
        ss = SimStrategy.SimStrategy()
        state = SimState.SimState(ss)
        state.getAgent("ocean_51")._func = MinterAgents.ExpFunc(H=4.0)
        
        #send from money 51% minter -> ocean_dao
        o51_OCEAN_t0 = state.getAgent("ocean_51").OCEAN()
        dao_OCEAN_t0 = state.getAgent("ocean_dao").OCEAN()

        self.assertEqual(o51_OCEAN_t0, 0.0)
        self.assertEqual(dao_OCEAN_t0, 0.0)
        self.assertEqual(state._total_OCEAN_minted, 0.0)

        #ocean_51 should disburse at tick=1
        state.getAgent("ocean_51").takeStep(state); state.tick += 1
        state.getAgent("ocean_51").takeStep(state); state.tick += 1
        
        o51_OCEAN_t1 = state.getAgent("ocean_51").OCEAN()
        dao_OCEAN_t1 = state.getAgent("ocean_dao").OCEAN()
        
        self.assertEqual(o51_OCEAN_t1, 0.0) 
        self.assertTrue(dao_OCEAN_t1 > 0.0)
        self.assertTrue(state._total_OCEAN_minted > 0.0)
        self.assertEqual(state._total_OCEAN_minted, dao_OCEAN_t1)
