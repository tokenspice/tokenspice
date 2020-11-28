from engine.evm.btoken import BToken
from web3tools import web3util
from web3tools.wallet import Wallet

class Datatoken(BToken):
    def __init__(self, contract_address):
        abi = web3util.abi('DataTokenTemplate')
        web3 = web3util.get_web3()
        self.contract = web3.eth.contract(contract_address, abi=abi)
    
    #============================================================
    #new methods for Datatoken
    def download(self, *args, **kwargs):
        raise NotImplementedError()
    
    def blob(self) -> str:
        return self.contract.functions.blob().call()

    def mint(self, account: str, value_base: int, from_wallet: Wallet):
        f = self.contract.functions.mint(account, value_base)
        return web3util.buildAndSendTx(f, from_wallet)        
    
    def setMinter(self, minter: str, from_wallet: Wallet):
        f = self.contract.functions.setMinter(minter)
        return web3util.buildAndSendTx(f, from_wallet)

