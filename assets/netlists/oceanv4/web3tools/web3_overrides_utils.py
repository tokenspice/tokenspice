#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time

from enforce_typing import enforce_types
from hexbytes import HexBytes
from web3 import Web3
from web3.types import TxReceipt


@enforce_types
def wait_for_transaction_receipt_and_block_confirmations(
    web3: Web3,
    tx_hash: HexBytes,
    block_confirmations: int,
    block_number_poll_interval: float,
    transaction_timeout: int = 120,
) -> TxReceipt:
    """Wait for the transaction receipt. Then, verify the transaction receipt
    still appears in the chain after `block_confirmations` number of blocks.
    Return the transaction receipt.

    :param web3: Web3, used to query for transaction receipts and block number.
    :param tx_hash: HexBytes, the transaction hash.
    :param block_confirmations: int, number of blocks to wait before confirming
      transaction is still in chain. Larger number of block confirmations
      increases certainty that transaction has settled.
    :param block_number_poll_interval: float, amount of time between calls to
      get latest block number in seconds
    :param transaction_timeout: int, amount of time to wait for initial tx
      receipt in seconds.
    """
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, transaction_timeout)
    while web3.eth.block_number < receipt.blockNumber + block_confirmations:
        time.sleep(block_number_poll_interval)
    return web3.eth.get_transaction_receipt(tx_hash)
