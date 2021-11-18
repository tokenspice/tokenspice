#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
from typing import Dict, Optional, Union

from enforce_typing import enforce_types
from eth_account.datastructures import SignedMessage
from eth_account.messages import SignableMessage
from hexbytes.main import HexBytes
from assets.netlists.oceanv4.web3tools.integer import Integer
from assets.netlists.oceanv4.web3tools.constants import ENV_MAX_GAS_PRICE, MIN_GAS_PRICE
from assets.netlists.oceanv4.web3tools.utils import (
    private_key_to_address,
    private_key_to_public_key,
)
from web3.main import Web3

logger = logging.getLogger(__name__)


class Wallet:

    """
    The wallet is responsible for signing transactions and messages by using an account's
    private key.

    The use of this wallet allows Ocean tools to send rawTransactions which keeps the user
    key and password safe and they are never sent outside. Another advantage of this is that
    we can interact directly with remote network nodes without having to run a local parity
    node since we only send the raw transaction hash so the user info is safe.

    Usage:
    ```python
    wallet = Wallet(
        ocean.web3,
        private_key=private_key,
        block_confirmations=ocean.config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )
    ```

    """

    _last_tx_count = dict()

    @enforce_types
    def __init__(
        self,
        web3: Web3,
        private_key: str,
        block_confirmations: Union[Integer, int],
        transaction_timeout: Union[Integer, int],
    ) -> None:
        """Initialises Wallet object."""
        assert private_key, "private_key is required."

        self.web3 = web3
        self.block_confirmations = (
            block_confirmations
            if isinstance(block_confirmations, Integer)
            else Integer(block_confirmations)
        )
        self.transaction_timeout = (
            transaction_timeout
            if isinstance(transaction_timeout, Integer)
            else Integer(transaction_timeout)
        )
        self._last_tx_count.clear()

        self.private_key = private_key
        self._address = private_key_to_address(self.private_key)

    @property
    @enforce_types
    def address(self) -> str:
        return self._address

    @property
    @enforce_types
    def key(self) -> str:
        return self.private_key

    @staticmethod
    @enforce_types
    def reset_tx_count() -> None:
        Wallet._last_tx_count = dict()

    @enforce_types
    def __get_key(self) -> Optional[str]:
        return self.private_key

    @enforce_types
    def validate(self) -> bool:
        account = self.web3.eth.account.from_key(self.private_key)
        return account.address == self._address

    @staticmethod
    @enforce_types
    def _get_nonce(web3: Web3, address: str) -> int:
        # We cannot rely on `web3.eth.get_transaction_count` because when sending multiple
        # transactions in a row without wait in between the network may not get the chance to
        # update the transaction count for the account address in time.
        # So we have to manage this internally per account address.
        if address not in Wallet._last_tx_count:
            Wallet._last_tx_count[address] = web3.eth.get_transaction_count(address)
        else:
            Wallet._last_tx_count[address] += 1

        return Wallet._last_tx_count[address]

    @enforce_types
    def sign_tx(
        self,
        tx: Dict[str, Union[int, str, bytes]],
        fixed_nonce: Optional[int] = None,
        gas_price: Optional[int] = None,
    ) -> HexBytes:
        account = self.web3.eth.account.from_key(self.private_key)
        if fixed_nonce is not None:
            nonce = fixed_nonce
            logger.debug(
                f"Signing transaction using a fixed nonce {fixed_nonce}, tx params are: {tx}"
            )
        else:
            nonce = Wallet._get_nonce(self.web3, account.address)

        if not gas_price:
            gas_price = int(self.web3.eth.gas_price * 1.1)
            gas_price = max(gas_price, MIN_GAS_PRICE)

        max_gas_price = os.getenv(ENV_MAX_GAS_PRICE, None)
        if gas_price and max_gas_price:
            gas_price = min(gas_price, max_gas_price)

        logger.debug(
            f"`Wallet` signing tx: sender address: {account.address} nonce: {nonce}, "
            f"eth.gasPrice: {self.web3.eth.gas_price}"
        )
        tx["gasPrice"] = gas_price
        tx["nonce"] = nonce
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        logger.debug(f"Using gasPrice: {gas_price}")
        logger.debug(f"`Wallet` signed tx is {signed_tx}")
        return signed_tx.rawTransaction

    @enforce_types
    def sign(self, msg_hash: SignableMessage) -> SignedMessage:
        """Sign a transaction."""
        account = self.web3.eth.account.from_key(self.private_key)
        return account.sign_message(msg_hash)

    @enforce_types
    def keys_str(self) -> str:
        s = []
        s += [f"address: {self.address}"]
        if self.private_key is not None:
            s += [f"private key: {self.private_key}"]
            s += [f"public key: {private_key_to_public_key(self.private_key)}"]
        s += [""]
        return "\n".join(s)
