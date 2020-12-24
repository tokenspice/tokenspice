import logging
import typing
import web3

from util import constants
from web3tools import web3util, account

logger = logging.getLogger(__name__)

def randomWeb3Wallet():
    private_key = account.randomPrivateKey()
    return Web3Wallet(private_key=private_key)

class Web3Wallet:
    """Signs txs and msgs with an account's private key."""
    _last_tx_count: dict = dict()
    MIN_GAS_PRICE = 1000000000

    def __init__(self, private_key:str):
        self._private_key = private_key
        self._address = account.privateKeyToAddress(self._private_key)

        #give this wallet a bunch of ETH for gas fees
        
    
    @property
    def address(self):
        return self._address

    @property
    def private_key(self):
        return self._private_key

    @property
    def account(self):
        return account.Account(private_key=self.private_key)
    
    @staticmethod
    def reset_tx_count():
        Web3Wallet._last_tx_count = dict()

    def __get_key(self):
        return self._private_key
    
    def validate(self):
        _web3 = web3util.get_web3()
        key = self.__get_key()
        account = _web3.eth.account.from_key(key)
        return account.address == self._address

    @staticmethod
    def _get_nonce(address):
        # We cannot rely on `web3.eth.getTransactionCount` because when sending multiple
        # transactions in a row without wait in between the network may not get the chance to
        # update the transaction count for the account address in time.
        # So we have to manage this internally per account address.
        _web3 = web3util.get_web3()
        if address not in Web3Wallet._last_tx_count:
            Web3Wallet._last_tx_count[address] = _web3.eth.getTransactionCount(address)
        else:
            Web3Wallet._last_tx_count[address] += 1

        return Web3Wallet._last_tx_count[address]

    def sign_tx(self, tx):
        _web3 = web3util.get_web3()
        account = _web3.eth.account.from_key(self._private_key)
        nonce = Web3Wallet._get_nonce(account.address)
        gas_price = int(_web3.eth.gasPrice / 100)
        gas_price = max(gas_price, self.MIN_GAS_PRICE)
        tx['nonce'] = nonce
        tx['gasPrice'] = gas_price
        signed_tx = _web3.eth.account.sign_transaction(tx, private_key)
        return signed_tx.rawTransaction

    def sign(self, msg_hash):
        account = web3.eth.account.from_key(self._private_key)
        return account.signHash(msg_hash)

    def ETH_base(self) -> int: #returns ETH, in base 18 (i.e. num wei)
        _web3 = web3util.get_web3()
        return _web3.eth.getBalance(self._address)

    def fundFromAbove(self, num_wei: int):
        #Give the this wallet ETH to pay gas fees
        #Use funds given to 'TEST_PRIVATE_KEY1' from ganache (see deploy.py)
        network = web3util.get_network()
        god_key = web3util.confFileValue(network, 'TEST_PRIVATE_KEY1')
        god_wallet = Web3Wallet(god_key)
        god_wallet.sendEth(self.address, num_wei)
        
    def sendEth(self, to_address:str, num_wei:int):
        return buildAndSendTx(
            function=None, from_wallet=self, num_wei=num_wei,
            to_address=to_address)

def buildAndSendTx(function,
                   from_wallet: Web3Wallet,
                   gaslimit: int = constants.GASLIMIT_DEFAULT,
                   num_wei: int = 0,
                   to_address=None):
    assert isinstance(from_wallet.address, str)
    #assert isinstance(from_wallet.private_key, str)

    _web3 = web3util.get_web3()
    nonce = _web3.eth.getTransactionCount(from_wallet.address)
    network = web3util.get_network()
    gas_price = int(web3util.confFileValue(network, 'GAS_PRICE'))
    tx_params = {
        "from": from_wallet.address,
        "value": num_wei,
        "nonce": nonce,
        "gas": gaslimit,
        "gasPrice": gas_price,
    }

    if function is None: #just send ETH, versus smart contract call?
        assert to_address is not None
        assert isinstance(to_address, str)
        tx = tx_params
        tx["to"] = to_address
    else:
        assert to_address is None
        tx = function.buildTransaction(tx_params)
        
    signed_tx = _web3.eth.account.sign_transaction(
        tx, private_key=from_wallet.private_key)
    tx_hash = _web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    tx_receipt = _web3.eth.waitForTransactionReceipt(tx_hash)
    if tx_receipt['status'] == 0:  # did tx fail?
        raise Exception("The tx failed. tx_receipt: {tx_receipt}")
    return (tx_hash, tx_receipt)

    
