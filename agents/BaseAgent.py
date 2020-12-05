import logging
log = logging.getLogger('baseagent')

from abc import ABC, abstractmethod
import enforce
import typing

from agents import BaseAgent, AgentWallet
from web3engine import bpool, globaltokens
from util.constants import SAFETY
from util.strutil import StrMixin
from web3tools.web3util import toBase18

@enforce.runtime_validation
class BaseAgent(ABC, StrMixin):
    """This can be a data buyer, publisher, etc. Sub-classes implement each."""
       
    def __init__(self, name: str, USD: float, OCEAN: float):
        self.name = name
        self._wallet = AgentWallet.AgentWallet(USD, OCEAN)

        #postconditions
        assert self.USD() == USD
        assert self.OCEAN() == OCEAN

    #=======================================================================
    @abstractmethod
    def takeStep(self, state): #this is where the Agent does *work*
        pass

    #=======================================================================
    def BPT(self, pool:bpool.BPool) -> float:
        return self._wallet.BPT(pool) 

    #=======================================================================
    def USD(self) -> float:
        return self._wallet.USD() 
    
    def receiveUSD(self, amount: float) -> None:
        self._wallet.depositUSD(amount) 

    def _transferUSD(self, receiving_agent, amount: float) -> None:
        """set receiver to None to model spending, without modeling receiver"""
        if SAFETY:
            assert isinstance(receiving_agent, BaseAgent) or (receiving_agent is None)
        if receiving_agent is not None:
            self._wallet.transferUSD(receiving_agent._wallet, amount)
        else:
            self._wallet.withdrawUSD(amount)
        
    #=======================================================================
    def OCEAN(self) -> float:
        return self._wallet.OCEAN() 

    def receiveOCEAN(self, amount: float) -> None:
        self._wallet.depositOCEAN(amount)

    def _transferOCEAN(self, receiving_agent, amount: float) -> None:
        """set receiver to None to model spending, without modeling receiver"""
        if SAFETY:
            assert isinstance(receiving_agent, BaseAgent) or (receiving_agent is None)
        if receiving_agent is not None:
            self._wallet.transferOCEAN(receiving_agent._wallet, amount)
        else:
            self._wallet.withdrawOCEAN(amount)
            
