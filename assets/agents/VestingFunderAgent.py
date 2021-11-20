import brownie
from brownie import Wei
from enforce_typing import enforce_types
import random

from assets.agents.VestingWalletAgent import VestingWalletAgent
from engine import AgentBase
from web3engine import globaltokens
from util.constants import BROWNIE_PROJECT, S_PER_DAY

@enforce_types
class VestingFunderAgent(AgentBase.AgentBaseEvm):
    """Funds the beneficiary with all of self's OCEAN, in a one-time act"""
    def __init__(self, name: str, USD: float, OCEAN: float,
                 beneficiary_agent_name: str,
                 start_timestamp: int,
                 duration_seconds: int):
        super().__init__(name, USD, OCEAN)
        
        self._beneficiary_agent_name:str = beneficiary_agent_name
        self._start_timestamp:int = start_timestamp
        self._duration_seconds:int = duration_seconds
        
        self._did_funding = False
        
    def takeStep(self, state) -> None:
        if self._did_funding:
            return 
        self._did_funding = True

        #create vesting wallet
        beneficiary_agent = state.getAgent(self._beneficiary_agent_name)
        start_timestamp = brownie.network.chain.time() + 5 #magic number
        duration_seconds = 30 #magic number
        vw_contract = BROWNIE_PROJECT.VestingWallet.deploy(
            beneficiary_agent.address,
            self._start_timestamp,
            self._duration_seconds,
            {'from': self.account()}) #account() is a brownie account

        #fund the vesting wallet with all of self's OCEAN
        token = globaltokens.OCEANtoken()
        token.transfer(beneficary_agent.account(), Wei(self.OCEAN()),
                       {'from': self.account()})
        
        #create vesting wallet agent, add to state
        vw_agent = VestingWalletAgent("vw_agent", vw_contract)
        state.addAgent(vw_agent)