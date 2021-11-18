#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import namedtuple
from pathlib import Path
from typing import Any, List, Optional

# import 
from contracts import artifacts
from enforce_typing import enforce_types
from eth_account.account import Account
from eth_account.messages import encode_defunct
from eth_keys import keys
from eth_utils import big_endian_to_int, decode_hex
from hexbytes.main import HexBytes
from assets.netlists.oceanv4.web3tools.constants import DEFAULT_NETWORK_NAME, NETWORK_NAME_MAP
from assets.netlists.oceanv4.web3tools.signature import SignatureFix
from web3.main import Web3

Signature = namedtuple("Signature", ("v", "r", "s"))

logger = logging.getLogger(__name__)


@enforce_types
def generate_multi_value_hash(types: List[str], values: List[str]) -> HexBytes:
    """
    Return the hash of the given list of values.
    This is equivalent to packing and hashing values in a solidity smart contract
    hence the use of `soliditySha3`.

    :param types: list of solidity types expressed as strings
    :param values: list of values matching the `types` list
    :return: bytes
    """
    assert len(types) == len(values)
    return Web3.solidityKeccak(types, values)


@enforce_types
def prepare_prefixed_hash(msg_hash: str) -> HexBytes:
    """

    :param msg_hash:
    :return:
    """
    return generate_multi_value_hash(
        ["string", "bytes32"], ["\x19Ethereum Signed Message:\n32", msg_hash]
    )


@enforce_types
def to_32byte_hex(val: int) -> str:
    """

    :param val:
    :return:
    """
    return Web3.toBytes(val).rjust(32, b"\0")


@enforce_types
def split_signature(signature: Any) -> Signature:
    """

    :param web3:
    :param signature: signed message hash, hex str
    :return:
    """
    assert len(signature) == 65, (
        f"invalid signature, " f"expecting bytes of length 65, got {len(signature)}"
    )
    v = Web3.toInt(signature[-1])
    r = to_32byte_hex(int.from_bytes(signature[:32], "big"))
    s = to_32byte_hex(int.from_bytes(signature[32:64], "big"))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


@enforce_types
def private_key_to_address(private_key: str) -> str:
    return Account.from_key(private_key).address


@enforce_types
def private_key_to_public_key(private_key: str) -> str:
    private_key_bytes = decode_hex(private_key)
    private_key_object = keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key


@enforce_types
def get_network_name(
    chain_id: Optional[int] = None, web3: Optional[Web3] = None
) -> str:
    """
    Return the network name based on the current ethereum chain id.

    Return `ganache` for every chain id that is not mapped.

    :param chain_id: Chain id, int
    :param web3: Web3 instance
    """
    if not chain_id:
        if not web3:
            return DEFAULT_NETWORK_NAME.lower()
        else:
            chain_id = get_chain_id(web3)
    return NETWORK_NAME_MAP.get(chain_id, DEFAULT_NETWORK_NAME).lower()


@enforce_types
def get_chain_id(web3: Web3) -> int:
    """
    Return the ethereum chain id calling the `web3.eth.chain_id` method.

    :param web3: Web3 instance
    :return: Chain id, int
    """
    return int(web3.eth.chain_id)


@enforce_types
def ec_recover(message: str, signed_message: str) -> str:
    """
    This method does not prepend the message with the prefix `\x19Ethereum Signed Message:\n32`.
    The caller should add the prefix to the msg/hash before calling this if the signature was
    produced for an ethereum-prefixed message.

    :param message:
    :param signed_message:
    :return:
    """
    v, r, s = split_signature(Web3.toBytes(hexstr=signed_message))
    signature_object = SignatureFix(vrs=(v, big_endian_to_int(r), big_endian_to_int(s)))
    return Account.recoverHash(message, signature=signature_object.to_hex_v_hacked())


@enforce_types
def personal_ec_recover(message: str, signed_message: str) -> str:
    prefixed_hash = encode_defunct(text=message)
    return ec_recover(prefixed_hash, signed_message)


@enforce_types
def get_ether_balance(web3: Web3, address: str) -> int:
    """
    Get balance of an ethereum address.

    :param address: address, bytes32
    :return: balance, int
    """
    return web3.eth.get_balance(address, block_identifier="latest")


@enforce_types
def get_artifacts_path() -> str:
    return str(Path(artifacts.__file__).parent.expanduser().resolve())
