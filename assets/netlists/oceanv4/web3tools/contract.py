#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Dict, Optional

from enforce_typing import enforce_types
from hexbytes.main import HexBytes
from assets.netlists.oceanv4.web3tools.integer import Integer
from assets.netlists.oceanv4.web3tools.constants import BLOCK_NUMBER_POLL_INTERVAL
from assets.netlists.oceanv4.web3tools.utils import get_chain_id
from assets.netlists.oceanv4.web3tools.wallet import Wallet
from assets.netlists.oceanv4.web3tools.web3_overrides_utils import (
    wait_for_transaction_receipt_and_block_confirmations,
)
from web3.contract import prepare_transaction
from web3.main import Web3


@enforce_types
class CustomContractFunction:
    def __init__(self, contract_function):
        """Initializes CustomContractFunction."""
        self._contract_function = contract_function

    def transact(
        self,
        transaction: Dict[str, Any],
        block_confirmations: int,
        transaction_timeout: int,
    ) -> HexBytes:
        """Customize calling smart contract transaction functions.
        This function is copied from web3 ContractFunction with a few changes:

        1. Don't set `from` using the web3.eth.default account
        2. Add chainId if `chainId` is not in the `transaction` dict
        3. Estimate gas limit if `gas` is not in the `transaction` dict

        :param transaction: dict which has the required transaction arguments
        :return: hex str transaction hash
        """
        transact_transaction = dict(**transaction)

        if "data" in transact_transaction:
            raise ValueError("Cannot set data in transact transaction")

        cf = self._contract_function
        if cf.address is not None:
            transact_transaction.setdefault("to", cf.address)

        if "to" not in transact_transaction:
            if isinstance(self, type):
                raise ValueError(
                    "When using `Contract.transact` from a contract factory you "
                    "must provide a `to` address with the transaction"
                )
            else:
                raise ValueError(
                    "Please ensure that this contract instance has an address."
                )
        if "chainId" not in transact_transaction:
            transact_transaction["chainId"] = cf.web3.eth.chain_id

        if "gas" not in transact_transaction:
            tx = transaction.copy()
            if "account_key" in tx:
                tx.pop("account_key")
            gas = cf.estimateGas(tx)
            transact_transaction["gas"] = gas

        return transact_with_contract_function(
            cf.address,
            cf.web3,
            block_confirmations,
            transaction_timeout,
            cf.function_identifier,
            transact_transaction,
            cf.contract_abi,
            cf.abi,
            *cf.args,
            **cf.kwargs,
        )


@enforce_types
def transact_with_contract_function(
    address: str,
    web3: Web3,
    block_confirmations: int,
    transaction_timeout: int,
    function_name: Optional[str] = None,
    transaction: Optional[dict] = None,
    contract_abi: Optional[list] = None,
    fn_abi: Optional[dict] = None,
    *args,
    **kwargs,
) -> HexBytes:
    """
    Helper function for interacting with a contract function by sending a
    transaction. This is copied from web3 `transact_with_contract_function`
    with a few additions:
        1. If `account_key` in transaction dict, sign and send transaction via
           `web3.eth.send_raw_transaction`
        2. Otherwise, send via `web3.eth.send_transaction`
        3. Retry failed transactions (when txn_receipt.status indicates failure)
        4. Network-dependent timeout
    """
    transact_transaction = prepare_transaction(
        address,
        web3,
        fn_identifier=function_name,
        contract_abi=contract_abi,
        transaction=transaction,
        fn_abi=fn_abi,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    account_key = None
    if transaction and "account_key" in transaction:
        account_key = transaction["account_key"]
        transact_transaction.pop("account_key")

    if account_key:
        raw_tx = Wallet(
            web3,
            private_key=account_key,
            block_confirmations=Integer(block_confirmations),
            transaction_timeout=Integer(transaction_timeout),
        ).sign_tx(transact_transaction)
        logging.debug(
            f"sending raw tx: function: {function_name}, tx hash: {raw_tx.hex()}"
        )
        txn_hash = web3.eth.send_raw_transaction(raw_tx)
    else:
        txn_hash = web3.eth.send_transaction(transact_transaction)

    chain_id = get_chain_id(web3)
    block_number_poll_interval = BLOCK_NUMBER_POLL_INTERVAL[chain_id]
    wait_for_transaction_receipt_and_block_confirmations(
        web3,
        txn_hash,
        block_confirmations,
        block_number_poll_interval,
        transaction_timeout,
    )
    return txn_hash
