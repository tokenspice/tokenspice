#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from enforce_typing import enforce_types
from eth_account.messages import SignableMessage
from assets.netlists.oceanv4.web3tools.constants import BLOCK_NUMBER_POLL_INTERVAL
from assets.netlists.oceanv4.web3tools.wallet import Wallet
from assets.netlists.oceanv4.web3tools.web3_overrides_utils import (
    wait_for_transaction_receipt_and_block_confirmations,
)
from web3.datastructures import AttributeDict
from web3.main import Web3


@enforce_types
def sign_hash(msg_hash: SignableMessage, wallet: Wallet) -> str:
    """
    This method use `personal_sign`for signing a message. This will always prepend the
    `\x19Ethereum Signed Message:\n32` prefix before signing.

    :param msg_hash:
    :param wallet: Wallet instance
    :return: signature
    """
    s = wallet.sign(msg_hash)
    return s.signature.hex()


@enforce_types
def send_ether(from_wallet: Wallet, to_address: str, amount: int) -> AttributeDict:
    if not Web3.isChecksumAddress(to_address):
        to_address = Web3.toChecksumAddress(to_address)

    web3 = from_wallet.web3
    chain_id = web3.eth.chain_id
    tx = {
        "from": from_wallet.address,
        "to": to_address,
        "value": amount,
        "chainId": chain_id,
    }
    tx["gas"] = web3.eth.estimate_gas(tx)
    raw_tx = from_wallet.sign_tx(tx)
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    block_confirmations = from_wallet.block_confirmations.value
    block_number_poll_interval = BLOCK_NUMBER_POLL_INTERVAL[chain_id]
    transaction_timeout = from_wallet.transaction_timeout.value
    wait_for_transaction_receipt_and_block_confirmations(
        web3,
        tx_hash,
        block_confirmations,
        block_number_poll_interval,
        transaction_timeout,
    )
    return web3.eth.get_transaction_receipt(tx_hash)


@enforce_types
def cancel_or_replace_transaction(
    from_wallet: Wallet,
    nonce_value: Optional[Union[str, int]] = None,
    gas_price: Optional[int] = None,
    gas_limit: Optional[int] = None,
) -> AttributeDict:
    web3 = from_wallet.web3
    chain_id = web3.eth.chain_id
    tx = {
        "from": from_wallet.address,
        "to": from_wallet.address,
        "value": 0,
        "chainId": chain_id,
    }
    gas = gas_limit if gas_limit is not None else web3.eth.estimate_gas(tx)
    tx["gas"] = gas + 1
    raw_tx = from_wallet.sign_tx(tx, fixed_nonce=nonce_value, gas_price=gas_price)
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    block_confirmations = from_wallet.block_confirmations.value
    block_number_poll_interval = BLOCK_NUMBER_POLL_INTERVAL[chain_id]
    transaction_timeout = from_wallet.transaction_timeout.value
    wait_for_transaction_receipt_and_block_confirmations(
        web3,
        tx_hash,
        block_confirmations,
        block_number_poll_interval,
        transaction_timeout,
    )
    return web3.eth.get_transaction_receipt(tx_hash)
