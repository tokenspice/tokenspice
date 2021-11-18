#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests
from enforce_typing import enforce_types
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from assets.netlists.oceanv4.web3tools.constants import ENV_GAS_PRICE
from assets.netlists.oceanv4.web3tools.contract_utils import (
    get_contract_definition,
    get_contracts_addresses,
    load_contract,
)
from assets.netlists.oceanv4.web3tools.wallet import Wallet
from assets.netlists.oceanv4.web3tools.contract import CustomContractFunction
from web3 import Web3
from web3._utils.events import get_event_data
from web3._utils.filters import construct_event_filter_params
from web3._utils.threads import Timeout
from web3.contract import ContractEvent, ContractEvents
from web3.datastructures import AttributeDict
from web3.exceptions import MismatchedABI, ValidationError
from websockets import ConnectionClosed

logger = logging.getLogger(__name__)


class ContractBase(object):

    """Base class for all contract objects."""

    CONTRACT_NAME = None

    V3_CONTRACTS = [
        "BFactory",
        "FixedRateExchange",
        "DTFactory",
        "Dispenser",
        "Metadata",
    ]

    @enforce_types
    def __init__(self, web3: Web3, address: Optional[str]) -> None:
        """Initialises Contract Base object."""
        self.name = self.contract_name
        assert (
            self.name
        ), "contract_name property needs to be implemented in subclasses."

        self.web3 = web3
        self.contract = load_contract(self.web3, self.name, address)
        assert not address or (
            self.contract.address == address and self.address == address
        )
        assert self.contract.caller is not None

    @enforce_types
    def __str__(self) -> str:
        """Returns contract `name @ address.`"""
        return f"{self.contract_name} @ {self.address}"

    @classmethod
    @enforce_types
    def configured_address(cls, network: str, address_file: str) -> str:
        """Returns the contract addresses"""
        addresses = get_contracts_addresses(network, address_file)
        # FIXME: temporary solution, will need to pass in the version
        # or detect it somehow

        # key = "v3" if cls.CONTRACT_NAME in cls.V3_CONTRACTS else "v4"
        # addresses = addresses[key]

        return addresses.get(cls.CONTRACT_NAME) if addresses else None

    @property
    @enforce_types
    def contract_name(self) -> str:
        """Returns the contract name"""
        return self.CONTRACT_NAME

    @property
    @enforce_types
    def address(self) -> str:
        """Return the ethereum address of the solidity contract deployed in current network."""
        return self.contract.address

    @property
    @enforce_types
    def events(self) -> ContractEvents:
        """Expose the underlying contract's events."""
        return self.contract.events

    @property
    @enforce_types
    def function_names(self) -> List[str]:
        """Returns the list of functions in the contract"""
        return list(self.contract.functions)

    @staticmethod
    @enforce_types
    def to_checksum_address(address: str) -> ChecksumAddress:
        """
        Validate the address provided.

        :param address: Address, hex str
        :return: address, hex str
        """
        return Web3.toChecksumAddress(address)

    @staticmethod
    @enforce_types
    def get_tx_receipt(
        web3: Web3, tx_hash: Union[str, HexBytes], timeout: Optional[int] = 120
    ) -> Optional[AttributeDict]:
        """
        Get the receipt of a tx.

        :param tx_hash: hash of the transaction
        :param timeout: int in seconds to wait for transaction receipt
        :return: Tx receipt
        """
        try:
            return web3.eth.wait_for_transaction_receipt(
                HexBytes(tx_hash), timeout=timeout
            )
        except ValueError as e:
            logger.error(f"Waiting for transaction receipt failed: {e}")
            return None
        except Timeout as e:
            logger.info(f"Waiting for transaction receipt may have timed out: {e}.")
            return None
        except ConnectionClosed as e:
            logger.info(
                f"ConnectionClosed error waiting for transaction receipt failed: {e}."
            )
            raise
        except Exception as e:
            logger.info(f"Unknown error waiting for transaction receipt: {e}.")
            raise

    @enforce_types
    def is_tx_successful(self, tx_hash: str) -> bool:
        """Check if the transaction is successful.

        :param tx_hash: hash of the transaction
        :return: bool
        """
        receipt = self.get_tx_receipt(self.web3, tx_hash)
        return bool(receipt and receipt.status == 1)

    @enforce_types
    def get_event_signature(self, event_name: str) -> str:
        """
        Return signature of event definition to use in the call to eth_getLogs.

        The event signature is used as topic0 (first topic) in the eth_getLogs arguments
        The signature reflects the event name and argument types.

        :param event_name:
        :return:
        """
        try:
            e = getattr(self.events, event_name)
        except MismatchedABI:
            e = None

        if not e:
            raise ValueError(
                f"Event {event_name} not found in {self.CONTRACT_NAME} contract."
            )

        abi = e().abi
        types = [param["type"] for param in abi["inputs"]]
        sig_str = f'{event_name}({",".join(types)})'
        return Web3.keccak(text=sig_str).hex()

    @enforce_types
    def subscribe_to_event(
        self,
        event_name: str,
        timeout: int,
        event_filter: Optional[dict] = None,
        callback: Optional[Callable] = None,
        timeout_callback: Optional[Callable] = None,
        args: Optional[list] = None,
        wait: Optional[bool] = False,
        from_block: Optional[Union[str, int]] = "latest",
        to_block: Optional[Union[str, int]] = "latest",
    ) -> None:
        """
        Create a listener for the event `event_name` on this contract.

        :param event_name: name of the event to subscribe, str
        :param timeout:
        :param event_filter:
        :param callback:
        :param timeout_callback:
        :param args:
        :param wait: if true block the listener until get the event, bool
        :param from_block: int or None
        :param to_block: int or None
        :return: event if blocking is True and an event is received, otherwise returns None
        """
        from ocean_lib.web3_internal.event_listener import EventListener

        return EventListener(
            self.web3,
            self.CONTRACT_NAME,
            self.address,
            event_name,
            args,
            filters=event_filter,
            from_block=from_block,
            to_block=to_block,
        ).listen_once(
            callback, timeout_callback=timeout_callback, timeout=timeout, blocking=wait
        )

    @enforce_types
    def send_transaction(
        self,
        fn_name: str,
        fn_args: Any,
        from_wallet: Wallet,
        transact: Optional[dict] = None,
    ) -> str:
        """Calls a smart contract function.

        :param fn_name: str the smart contract function name
        :param fn_args: tuple arguments to pass to function above
        :param from_wallet:
        :param transact: dict arguments for the transaction such as from, gas, etc.
        :return: hex str transaction hash
        """
        contract_fn = getattr(self.contract.functions, fn_name)(*fn_args)
        contract_function = CustomContractFunction(contract_fn)
        _transact = {
            "from": from_wallet.address,
            "account_key": from_wallet.key,
            "chainId": self.web3.eth.chain_id,
        }

        gas_price = os.environ.get(ENV_GAS_PRICE, None)
        if gas_price:
            _transact["gasPrice"] = gas_price

        if transact:
            _transact.update(transact)

        return contract_function.transact(
            _transact,
            from_wallet.block_confirmations.value,
            from_wallet.transaction_timeout.value,
        ).hex()

    @enforce_types
    def get_event_argument_names(self, event_name: str) -> Tuple:
        """Finds the event arguments by `event_name`.

        :param event_name: str Name of the event to search in the `contract`.
        :return: `event.argument_names` if event is found or None
        """
        event = getattr(self.contract.events, event_name, None)
        if event:
            return event().argument_names

    @classmethod
    @enforce_types
    def deploy(cls, web3: Web3, deployer_wallet: Wallet, *args) -> str:
        """
        Deploy the DataTokenTemplate and DTFactory contracts to the current network.

        :param web3:
        :param deployer_wallet: Wallet instance

        :return: smartcontract address of this contract
        """

        _json = get_contract_definition(cls.CONTRACT_NAME)

        _contract = web3.eth.contract(abi=_json["abi"], bytecode=_json["bytecode"])
        built_tx = _contract.constructor(*args).buildTransaction(
            {"from": deployer_wallet.address}
        )
        if "chainId" not in built_tx:
            built_tx["chainId"] = web3.eth.chain_id

        if "gas" not in built_tx:
            built_tx["gas"] = web3.eth.estimate_gas(built_tx)

        raw_tx = deployer_wallet.sign_tx(built_tx)
        logging.debug(
            f"Sending raw tx to deploy contract {cls.CONTRACT_NAME}, signed tx hash: {raw_tx.hex()}"
        )
        tx_hash = web3.eth.send_raw_transaction(raw_tx)

        return cls.get_tx_receipt(web3, tx_hash, timeout=60).contractAddress

    # can not enforce types since this goes through ContractEvent with Subscriptable Generics
    def get_event_log(
        self,
        event_name: str,
        from_block: int,
        to_block: int,
        filters: Optional[Dict[str, str]],
        chunk_size: Optional[int] = 1000,
    ) -> List[Any]:
        """Retrieves the first event log which matches the filters parameter criteria.
        It processes the blocks order backwards.

        :param event_name: str
        :param from_block: int
        :param to_block: int
        :param filters:
        :param chunk_size: int
        """
        event = getattr(self.events, event_name)

        chunk = chunk_size
        _to = to_block
        _from = _to - chunk + 1

        all_logs = []
        error_count = 0
        _from = max(_from, from_block)
        while _to >= from_block:
            try:
                logs = self.getLogs(
                    event, argument_filters=filters, fromBlock=_from, toBlock=_to
                )
                all_logs.extend(logs)
                if len(all_logs) >= 1:
                    break
                _to = _from - 1
                _from = max(_to - chunk + 1, from_block)
                error_count = 0
                if (to_block - _to) % 1000 == 0:
                    print(
                        f"    Searched blocks {_from}-{_to}. {event_name} event not yet found."
                    )
            except requests.exceptions.ReadTimeout as err:
                print(f"ReadTimeout ({_from}, {_to}): {err}")
                error_count += 1

            if error_count > 1:
                break

        return all_logs

    # can not enforce types since this goes through ContractEvent with Subscriptable Generics
    def get_event_logs(
        self,
        event_name: str,
        from_block: int,
        to_block: int,
        filters: Optional[Dict[str, str]] = None,
        chunk_size: Optional[int] = 1000,
    ) -> List[AttributeDict]:
        """
        Fetches the list of event logs between the given block numbers.
        :param event_name: str
        :param from_block: int
        :param to_block: int
        :param filters:
        :param chunk_size: int
        :return: List of event logs. List will have the structure as below.
        ```Python
            [AttributeDict({
                'args': AttributeDict({}),
                'event': 'LogNoArguments',
                'logIndex': 0,
                'transactionIndex': 0,
                'transactionHash': HexBytes('...'),
                'address': '0xF2E246BB76DF876Cef8b38ae84130F4F55De395b',
                'blockHash': HexBytes('...'),
                'blockNumber': 3
                }),
            AttributeDict(...),
            ...
            ]
        ```
        """
        event = getattr(self.events, event_name)

        chunk = chunk_size
        _from = from_block
        _to = _from + chunk - 1

        all_logs = []
        error_count = 0
        _to = min(_to, to_block)
        while _from <= to_block:
            try:
                logs = self.getLogs(
                    event, argument_filters=filters, fromBlock=_from, toBlock=_to
                )
                all_logs.extend(logs)
                _from = _to + 1
                _to = min(_from + chunk - 1, to_block)
                error_count = 0
                if (_from - from_block) % 1000 == 0:
                    print(
                        f"    Searched blocks {_from}-{_to}. {len(all_logs)} {event_name} events detected so far."
                    )
            except requests.exceptions.ReadTimeout as err:
                print(f"ReadTimeout ({_from}, {_to}): {err}")
                error_count += 1

            if error_count > 1:
                break

        return all_logs

    # can not enforce types since this goes through ContractEvent with Subscriptable Generics
    @staticmethod
    def getLogs(
        event: ContractEvent,
        argument_filters: Optional[Dict[str, Any]] = None,
        fromBlock: Optional[int] = None,
        toBlock: Optional[int] = None,
        blockHash: Optional[HexBytes] = None,
        from_all_addresses: Optional[bool] = False,
    ):
        """Get events for this contract instance using eth_getLogs API.

        This is a stateless method, as opposed to createFilter.
        It can be safely called against nodes which do not provide
        eth_newFilter API, like Infura nodes.
        If there are many events,
        like ``Transfer`` events for a popular token,
        the Ethereum node might be overloaded and timeout
        on the underlying JSON-RPC call.
        Example - how to get all ERC-20 token transactions
        for the latest 10 blocks:

        ```python
            from = max(mycontract.web3.eth.block_number - 10, 1)
            to = mycontract.web3.eth.block_number
            events = mycontract.events.Transfer.getLogs(fromBlock=from, toBlock=to)
            for e in events:
                print(e["args"]["from"],
                    e["args"]["to"],
                    e["args"]["value"])
        ```
        The returned processed log values will look like:

        ```python
            (
                AttributeDict({
                 'args': AttributeDict({}),
                 'event': 'LogNoArguments',
                 'logIndex': 0,
                 'transactionIndex': 0,
                 'transactionHash': HexBytes('...'),
                 'address': '0xF2E246BB76DF876Cef8b38ae84130F4F55De395b',
                 'blockHash': HexBytes('...'),
                 'blockNumber': 3
                }),
                AttributeDict(...),
                ...
            )
        ```

        See also: :func:`web3.middleware.filter.local_filter_middleware`.
        :param event: the ContractEvent instance with a web3 instance
        :param argument_filters:
        :param fromBlock: block number or "latest", defaults to "latest"
        :param toBlock: block number or "latest". Defaults to "latest"
        :param blockHash: block hash. blockHash cannot be set at the
          same time as fromBlock or toBlock
        :param from_all_addresses: True = return logs from all addresses
          False = return logs originating from event.address
        :yield: Tuple of :class:`AttributeDict` instances
        """

        if not event or not event.web3:
            raise TypeError(
                "This method can be only called on an event which has a web3 instance."
            )
        abi = event._get_event_abi()

        if argument_filters is None:
            argument_filters = dict()

        _filters = dict(**argument_filters)

        blkhash_set = blockHash is not None
        blknum_set = fromBlock is not None or toBlock is not None
        if blkhash_set and blknum_set:
            raise ValidationError(
                "blockHash cannot be set at the same" " time as fromBlock or toBlock"
            )

        # Construct JSON-RPC raw filter presentation based on human readable Python descriptions
        # Namely, convert event names to their keccak signatures
        address = event.address if not from_all_addresses else None
        _, event_filter_params = construct_event_filter_params(
            abi,
            event.web3.codec,
            contract_address=address,
            argument_filters=_filters,
            fromBlock=fromBlock,
            toBlock=toBlock,
        )

        if blockHash is not None:
            event_filter_params["blockHash"] = blockHash

        # Call JSON-RPC API
        logs = event.web3.eth.get_logs(event_filter_params)

        # Convert raw binary data to Python proxy objects as described by ABI
        return tuple(get_event_data(event.web3.codec, abi, entry) for entry in logs)
