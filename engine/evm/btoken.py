

from web3tools import web3util
from ocean_lib.web3_internal.wallet import Wallet


class BToken:
    def __init__(self, web3, contract_address: str):
        self.web3 = web3
        abi = self._abi()
        self.contract = web3.eth.contract(contract_address, abi=abi)
        
    @property
    def address(self):
        return self.contract.address
    
    def _abi(self):
        return web3util.abi(filename='./abi/BToken.abi')
        
    #============================================================
    #reflect BToken Solidity methods
    def symbol(self) -> str:
        return self.contract.functions.symbol().call()
    
    def decimals(self) -> int:
        return self.contract.functions.decimals().call()
    
    def balanceOf_base(self, address: str) -> int:
        func = self.contract.functions.balanceOf(address)
        return func.call()

    def approve(self, spender_address: str, amt_base: int,
                from_wallet: Wallet):
        f = self.contract.functions.approve(spender_address, amt_base)
        return web3util.buildAndSendTx(f, from_wallet)

    def transfer(self, dst_address: str, amt_base: int, from_wallet: Wallet):
        f = self.contract.functions.transfer(dst_address, amt_base)
        return web3util.buildAndSendTx(f, from_wallet)

    def allowance_base(self, src_address:str, dst_address: str) -> int:
        f = self.contract.functions.allowance(src_address, dst_address)
        return f.call()
