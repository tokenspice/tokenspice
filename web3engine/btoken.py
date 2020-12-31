from enforce_typing import enforce_types # type: ignore[import]
from web3tools import web3util, web3wallet

@enforce_types
class BToken:
    def __init__(self, contract_address):
        name = self.__class__.__name__
        abi = web3util.abi(name)
        web3 = web3util.get_web3()
        self.contract = web3.eth.contract(contract_address, abi=abi)
        
    @property
    def address(self):
        return self.contract.address
        
    #============================================================
    #reflect BToken Solidity methods
    def symbol(self) -> str:
        return self.contract.functions.symbol().call()
    
    def decimals(self) -> int:
        return self.contract.functions.decimals().call()
    
    def balanceOf_base(self, address: str) -> int:
        func = self.contract.functions.balanceOf(address)
        return func.call()

    def transfer(self, dst_address: str, amt_base: int,
                 from_wallet: web3wallet.Web3Wallet):
        f = self.contract.functions.transfer(dst_address, amt_base)
        return web3wallet.buildAndSendTx(f, from_wallet)

    def approve(self, spender_address: str, amt_base: int,
                from_wallet: web3wallet.Web3Wallet):
        f = self.contract.functions.approve(spender_address, amt_base)
        return web3wallet.buildAndSendTx(f, from_wallet)

    def allowance_base(self, src_address:str, dst_address: str) -> int:
        f = self.contract.functions.allowance(src_address, dst_address)
        return f.call() 
