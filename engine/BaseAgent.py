import logging
log = logging.getLogger('baseagent')

from abc import ABC, abstractmethod
import enforce
import typing

from engine import BaseAgent, Wallet
from util.constants import SAFETY
from util.strutil import StrMixin

@enforce.runtime_validation
class BaseAgent(ABC, StrMixin):
    """This can be a data buyer, publisher, etc. Sub-classes implement each."""
       
    def __init__(self, name: str, USD: float, OCEAN: float):
        self.name = name
        self._wallet = Wallet.Wallet(USD=USD, OCEAN=OCEAN)

    #=======================================================================
    @abstractmethod
    def takeStep(self, state): #this is where the Agent does *work*
        pass

    #=======================================================================
    def USD(self) -> float:
        #return self._wallet.USD() #slower
        return self._wallet._USD   #faster 
    
    def receiveUSD(self, amount: float) -> None:
        self._wallet.depositUSD(amount) 

    def _transferUSD(self, receiving_agent,
                     amount: typing.Union[float,None]) -> None:
        """set receiver to None to model spending, without modeling receiver"""
        if SAFETY:
            assert isinstance(receiving_agent, BaseAgent) or (receiving_agent is None)
        if receiving_agent is not None:
            receiving_agent.receiveUSD(amount)
        self._wallet.withdrawUSD(amount)
        
    #=======================================================================
    def OCEAN(self) -> float:
        #return self._wallet.OCEAN() #slower
        return self._wallet._OCEAN   #faster 

    def receiveOCEAN(self, amount: float) -> None:
        self._wallet.depositOCEAN(amount)

    def _transferOCEAN(self, receiving_agent,
                     amount: typing.Union[float,None]) -> None:
        """set receiver to None to model spending, without modeling receiver"""
        if SAFETY:
            assert isinstance(receiving_agent, BaseAgent) or (receiving_agent is None)
        if receiving_agent is not None:
            receiving_agent.receiveOCEAN(amount)
        self._wallet.withdrawOCEAN(amount)
