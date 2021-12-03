from enforce_typing import enforce_types

from engine import AgentBase
from util import globaltokens
from util.constants import BROWNIE_PROJECT057


@enforce_types
class PoolAgent(AgentBase.AgentBaseEvm):
    def __init__(self, name: str, pool):
        super().__init__(name, USD=0.0, OCEAN=0.0)
        self._pool = pool

        self._dt_address = self._datatokenAddress()
        self._dt = BROWNIE_PROJECT057.DataTokenTemplate.at(self._dt_address)
        self._controller_address = self._controllerAddress()

    @property
    def pool(self):
        return self._pool

    @property
    def datatoken_address(self) -> str:
        return self._dt_address

    @property
    def datatoken(self):
        return self._dt

    def takeStep(self, state):
        # it's a smart contract robot, it doesn't initiate anything itself
        pass

    def _datatokenAddress(self):
        addrs = self._pool.getCurrentTokens()
        assert len(addrs) == 2
        OCEAN_addr = globaltokens.OCEAN_address()
        for addr in addrs:
            if addr != OCEAN_addr:
                return addr
        raise AssertionError("should never get here")

    @property
    def controller_address(self) -> str:
        return self._controller_address

    def _controllerAddress(self):
        return self._pool.getController()
