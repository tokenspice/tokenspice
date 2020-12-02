
import logging
import typing

from web3tools import web3util

logger = logging.getLogger(__name__)

from web3tools.account import Account, privateKeyToAddress

class Wallet:
    """Signs txs and msgs with an account's private key."""
    _last_tx_count = dict()
    MIN_GAS_PRICE = 1000000000

    def __init__(self, private_key:str):
        self._private_key = private_key
        self._address = privateKeyToAddress(self._private_key)
    
    @property
    def address(self):
        return self._address

    @property
    def private_key(self):
        return self._private_key

    @property
    def account(self):
        return Account(private_key=self.private_key)
    
    @staticmethod
    def reset_tx_count():
        Wallet._last_tx_count = dict()

    def __get_key(self):
        return self._private_key
    
    def validate(self):
        web3 = web3util.get_web3()
        key = self.__get_key()
        account = web3.eth.account.from_key(key)
        return account.address == self._address

    @staticmethod
    def _get_nonce(address):
        # We cannot rely on `web3.eth.getTransactionCount` because when sending multiple
        # transactions in a row without wait in between the network may not get the chance to
        # update the transaction count for the account address in time.
        # So we have to manage this internally per account address.
        web3 = web3util.get_web3()
        if address not in Wallet._last_tx_count:
            Wallet._last_tx_count[address] = web3.eth.getTransactionCount(address)
        else:
            Wallet._last_tx_count[address] += 1

        return Wallet._last_tx_count[address]

    def sign_tx(self, tx):
        web3 = web3util.get_web3()
        account = web3.eth.account.from_key(self._private_key)
        nonce = Wallet._get_nonce(account.address)
        logger.debug(f'`Wallet` signing tx: sender address: {account.address} nonce: {nonce}, '
                     f'gasprice: {web3.eth.gasPrice}')
        gas_price = int(web3.eth.gasPrice / 100)
        gas_price = max(gas_price, self.MIN_GAS_PRICE)
        tx['nonce'] = nonce
        tx['gasPrice'] = gas_price
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        logger.debug(f'`Wallet` signed tx is {signed_tx}')
        return signed_tx.rawTransaction

    def sign(self, msg_hash):
        account = web3.eth.account.from_key(self._private_key)
        return account.signHash(msg_hash)
