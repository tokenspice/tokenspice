from enforce_typing import enforce_types # type: ignore[import]
import warnings

from web3tools import web3util, web3wallet

@enforce_types
class BFactory:
    def __init__(self):
        name = self.__class__.__name__
        abi = web3util.abi(name)
        web3 = web3util.get_web3()
        contract_address = web3util.contractAddress(name)
        self.contract = web3.eth.contract(contract_address, abi=abi)
        
    @property
    def address(self):
        return self.contract.address
        
    #============================================================
    #reflect BFactory Solidity methods
    def newBPool(self, from_wallet: web3wallet.Web3Wallet) -> str:
        print("BPool.newSPool(). Begin.")
        f = self.contract.functions.newBPool()
        (tx_hash, tx_receipt) = web3wallet.buildAndSendTx(f, from_wallet)

        # grab pool_address
        warnings.filterwarnings("ignore") #ignore unwarranted warning up next
        rich_logs = self.contract.events.BPoolCreated().processReceipt(tx_receipt)
        warnings.resetwarnings()
        pool_address = rich_logs[0]['args']['newBPoolAddress']
        print(f"  pool_address = {pool_address}")

        print("BPool.newSPool(). Done.")
        return pool_address

