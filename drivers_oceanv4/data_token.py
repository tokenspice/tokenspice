#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import time
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from enforce_typing import enforce_types
from eth_utils import remove_0x_prefix
from drivers_oceanv4.requests_session import get_requests_session
from drivers_oceanv4.data_service_provider import DataServiceProvider
from drivers_oceanv4.contract_base import ContractBase
from drivers_oceanv4.currency import from_wei, pretty_ether_and_wei, to_wei
from drivers_oceanv4.wallet import Wallet
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.exceptions import MismatchedABI
from web3.logs import DISCARD
from websockets import ConnectionClosed

OrderValues = namedtuple(
    "OrderValues",
    ("consumer", "amount", "serviceId", "startedAt", "marketFeeCollector", "marketFee"),
)


class DataToken(ContractBase):
    CONTRACT_NAME = "DataTokenTemplate"

    DEFAULT_CAP = to_wei(1000)

    ORDER_STARTED_EVENT = "OrderStarted"
    ORDER_FINISHED_EVENT = "OrderFinished"

    OPF_FEE_PER_TOKEN = to_wei("0.001")  # 0.1%
    MAX_MARKET_FEE_PER_TOKEN = to_wei("0.001")  # 0.1%

    # ============================================================
    # reflect DataToken Solidity methods
    @enforce_types
    def initialize(
        self,
        name: str,
        symbol: str,
        minter_address: str,
        cap: int,
        blob: str,
        fee_collector_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (name, symbol, minter_address, cap, blob, fee_collector_address),
            from_wallet,
        )

    @enforce_types
    def mint(self, account_address: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("mint", (account_address, amount), from_wallet)

    @enforce_types
    def startOrder(
        self,
        consumer: str,
        amount: int,
        serviceId: int,
        mrktFeeCollector: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startOrder", (consumer, amount, serviceId, mrktFeeCollector), from_wallet
        )

    @enforce_types
    def finishOrder(
        self,
        orderTxId: str,
        consumer: str,
        amount: int,
        serviceId: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "finishOrder", (orderTxId, consumer, amount, serviceId), from_wallet
        )

    @enforce_types
    def proposeMinter(self, new_minter: str, from_wallet: Wallet) -> str:
        return self.send_transaction("proposeMinter", (new_minter,), from_wallet)

    @enforce_types
    def approveMinter(self, from_wallet: Wallet) -> str:
        return self.send_transaction("approveMinter", (), from_wallet)

    @enforce_types
    def blob(self) -> str:
        return self.contract.caller.blob()

    @enforce_types
    def cap(self) -> int:
        return self.contract.caller.cap()

    @enforce_types
    def isMinter(self, address: str) -> bool:
        return self.contract.caller.isMinter(address)

    @enforce_types
    def minter(self) -> str:
        return self.contract.caller.minter()

    @enforce_types
    def isInitialized(self) -> bool:
        return self.contract.caller.isInitialized()

    @enforce_types
    def calculateFee(self, amount: int, fee_per_token: int) -> int:
        return self.contract.caller.calculateFee(amount, fee_per_token)

    # ============================================================
    # reflect required ERC20 standard functions
    @enforce_types
    def totalSupply(self) -> int:
        return self.contract.caller.totalSupply()

    @enforce_types
    def balanceOf(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    @enforce_types
    def transfer(self, to: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("transfer", (to, amount), from_wallet)

    @enforce_types
    def allowance(self, owner_address: str, spender_address: str) -> int:
        return self.contract.caller.allowance(owner_address, spender_address)

    @enforce_types
    def approve(self, spender: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("approve", (spender, amount), from_wallet)

    @enforce_types
    def transferFrom(
        self, from_address: str, to_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom", (from_address, to_address, amount), from_wallet
        )

    # ============================================================
    # reflect optional ERC20 standard functions
    @enforce_types
    def datatoken_name(self) -> str:
        return self.contract.caller.name()

    @enforce_types
    def symbol(self) -> str:
        return self.contract.caller.symbol()

    @enforce_types
    def decimals(self) -> int:
        return self.contract.caller.decimals()

    # ============================================================
    # reflect non-standard ERC20 functions added by Open Zeppelin
    @enforce_types
    def increaseAllowance(
        self, spender_address: str, added_value: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "increaseAllowance", (spender_address, added_value), from_wallet
        )

    @enforce_types
    def decreaseAllowance(
        self, spender_address: str, subtracted_value: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "decreaseAllowance", (spender_address, subtracted_value), from_wallet
        )

    # ============================================================
    # Events
    @enforce_types
    def get_event_signature(self, event_name: str) -> str:
        try:
            e = getattr(self.events, event_name)
        except MismatchedABI:
            raise ValueError(
                f"Event {event_name} not found in {self.CONTRACT_NAME} contract."
            )

        abi = e().abi
        types = [param["type"] for param in abi["inputs"]]
        sig_str = f'{event_name}({",".join(types)})'
        return Web3.keccak(text=sig_str).hex()

    @enforce_types
    def get_start_order_logs(
        self,
        consumer_address: Optional[str] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
        from_all_tokens: bool = False,
    ) -> Tuple:
        topic0 = self.get_event_signature(self.ORDER_STARTED_EVENT)
        topics = [topic0]
        if consumer_address:
            topic1 = f"0x000000000000000000000000{consumer_address[2:].lower()}"
            topics = [topic0, None, topic1]

        argument_filters = {"topics": topics}

        logs = ContractBase.getLogs(
            self.events.OrderStarted(),
            argument_filters=argument_filters,
            fromBlock=from_block,
            toBlock=to_block,
            from_all_addresses=from_all_tokens,
        )
        return logs

    @enforce_types
    def get_transfer_events_in_range(
        self, from_block: Optional[int], to_block: Optional[int]
    ) -> Tuple:
        return ContractBase.getLogs(
            self.events.Transfer(), fromBlock=from_block, toBlock=to_block
        )

    @enforce_types
    def get_all_transfers_from_events(
        self, start_block: Optional[int], end_block: Optional[int], chunk: int = 1000
    ) -> tuple:
        _from = start_block
        _to = _from + chunk - 1

        transfer_records = []
        error_count = 0
        _to = min(_to, end_block)
        while _from <= end_block:
            try:
                logs = self.get_transfer_events_in_range(_from, _to)
                transfer_records.extend(
                    [
                        (
                            lg.args["from"],
                            lg.args.to,
                            lg.args.value,
                            lg.blockNumber,
                            lg.transactionHash.hex(),
                            lg.logIndex,
                            lg.transactionIndex,
                        )
                        for lg in logs
                    ]
                )
                _from = _to + 1
                _to = min(_from + chunk - 1, end_block)
                error_count = 0
                if (_from - start_block) % chunk == 0:
                    print(
                        f"    Searched blocks {_from}-{_to}. {len(transfer_records)} Transfer events detected."
                    )
            except requests.exceptions.ReadTimeout as err:
                print(f"ReadTimeout ({_from}, {_to}): {err}")
                error_count += 1

            if error_count > 1:
                break

        return transfer_records, min(_to, end_block)  # can have duplicates

    @enforce_types
    def get_transfer_event(
        self, block_number: Optional[int], sender: str, receiver: str
    ) -> Optional[AttributeDict]:
        filter_params = {"from": sender, "to": receiver}
        logs = self.get_event_logs(
            "Transfer",
            filter_args=filter_params,
            from_block=block_number - 1,
            to_block=block_number + 10,
        )
        if not logs:
            return None

        if len(logs) > 1:
            raise AssertionError(
                f"Expected a single transfer event at "
                f"block {block_number}, but found {len(logs)} events."
            )

        return logs[0]

    @enforce_types
    def verify_transfer_tx(
        self, tx_id: str, sender: str, receiver: str
    ) -> Tuple[AttributeDict, AttributeDict]:
        tx = self.web3.eth.get_transaction(tx_id)
        if not tx:
            raise AssertionError("Transaction is not found, or is not yet verified.")

        if tx["from"] != sender or tx["to"] != self.address:
            raise AssertionError(
                f"Sender and receiver in the transaction {tx_id} "
                f"do not match the expected consumer and contract addresses."
            )

        _iter = 0
        while tx["blockNumber"] is None:
            time.sleep(0.1)
            tx = self.web3.eth.get_transaction(tx_id)
            _iter = _iter + 1
            if _iter > 100:
                break

        tx_receipt = self.get_tx_receipt(self.web3, tx_id)
        if tx_receipt.status == 0:
            raise AssertionError("Transfer transaction failed.")

        logs = self.events.Transfer().processReceipt(tx_receipt, errors=DISCARD)
        transfer_event = logs[0] if logs else None
        # transfer_event = self.get_transfer_event(tx['blockNumber'], sender, receiver)
        if not transfer_event:
            raise AssertionError(
                f"Cannot find the event for the transfer transaction with tx id {tx_id}."
            )
        assert (
            len(logs) == 1
        ), f"Multiple Transfer events in the same transaction !!! {logs}"

        if (
            transfer_event.args["from"] != sender
            or transfer_event.args["to"] != receiver
        ):
            raise AssertionError(
                "The transfer event from/to do not match the expected values."
            )

        return tx, transfer_event

    # can not be type enforced due to reusage of parent function (subscripted Generics)
    def get_event_logs(
        self,
        event_name: str,
        filter_args: Optional[Dict[str, str]] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
    ) -> Union[Tuple[()], Tuple[AttributeDict]]:
        event = getattr(self.events, event_name)
        filter_params = filter_args or {}
        logs = ContractBase.getLogs(
            event(),
            argument_filters=filter_params,
            fromBlock=from_block,
            toBlock=to_block,
        )
        return logs

    @enforce_types
    def verify_order_tx(
        self,
        tx_id: str,
        did: str,
        service_id: Union[str, int],
        amount: Union[str, int],
        sender: str,
    ) -> Tuple[Any, Any, Any]:
        try:
            tx_receipt = self.get_tx_receipt(self.web3, tx_id)
        except ConnectionClosed:
            # try again in this case
            tx_receipt = self.get_tx_receipt(self.web3, tx_id)

        if tx_receipt is None:
            raise AssertionError(
                "Failed to get tx receipt for the `startOrder` transaction.."
            )

        if tx_receipt.status == 0:
            raise AssertionError("order transaction failed.")

        receiver = self.contract.caller.minter()
        event_logs = self.events.OrderStarted().processReceipt(
            tx_receipt, errors=DISCARD
        )
        order_log = event_logs[0] if event_logs else None
        if not order_log:
            raise AssertionError(
                f"Cannot find the event for the order transaction with tx id {tx_id}."
            )
        assert (
            len(event_logs) == 1
        ), f"Multiple order events in the same transaction !!! {event_logs}"

        asset_id = remove_0x_prefix(did).lower()
        assert (
            asset_id == remove_0x_prefix(self.address).lower()
        ), "asset-id does not match the datatoken id."
        if str(order_log.args.serviceId) != str(service_id):
            raise AssertionError(
                f"The asset id (DID) or service id in the event does "
                f"not match the requested asset. \n"
                f"requested: (did={did}, serviceId={service_id}\n"
                f"event: (serviceId={order_log.args.serviceId}"
            )

        target_amount = amount - self.calculateFee(amount, self.OPF_FEE_PER_TOKEN)
        if order_log.args.mrktFeeCollector and order_log.args.marketFee > 0:
            max_market_fee = self.calculateFee(amount, self.MAX_MARKET_FEE_PER_TOKEN)
            assert order_log.args.marketFee <= (max_market_fee + 5), (
                f"marketFee {order_log.args.marketFee} exceeds the expected maximum "
                f"of {max_market_fee} based on feePercentage="
                f"{from_wei(self.MAX_MARKET_FEE_PER_TOKEN)} ."
            )
            target_amount = target_amount - order_log.args.marketFee

        # verify sender of the tx using the Tx record
        tx = self.web3.eth.get_transaction(tx_id)
        if sender not in [order_log.args.consumer, order_log.args.payer]:
            raise AssertionError(
                "sender of order transaction is not the consumer/payer."
            )
        transfer_logs = self.events.Transfer().processReceipt(
            tx_receipt, errors=DISCARD
        )
        receiver_to_transfers = {}
        for tr in transfer_logs:
            if tr.args.to not in receiver_to_transfers:
                receiver_to_transfers[tr.args.to] = []
            receiver_to_transfers[tr.args.to].append(tr)
        if receiver not in receiver_to_transfers:
            raise AssertionError(
                f"receiver {receiver} is not found in the transfer events."
            )
        transfers = sorted(receiver_to_transfers[receiver], key=lambda x: x.args.value)
        total = sum(tr.args.value for tr in transfers)
        if total < (target_amount - 5):
            raise ValueError(
                f"transferred value does meet the service cost: "
                f"service.cost - fees={pretty_ether_and_wei(target_amount)}, "
                f"transferred value={pretty_ether_and_wei(total)}"
            )
        return tx, order_log, transfers[-1]

    @enforce_types
    def download(
        self, wallet: Wallet, tx_id: str, destination_folder: Union[str, Path]
    ) -> str:
        url = self.blob()
        download_url = (
            f"{url}?"
            f"consumerAddress={wallet.address}"
            f"&dataToken={self.address}"
            f"&transferTxId={tx_id}"
        )
        response = get_requests_session().get(download_url, stream=True)
        file_name = f"file-{self.address}"
        DataServiceProvider.write_file(response, destination_folder, file_name)
        return os.path.join(destination_folder, file_name)

    def _get_url_from_blob(self, int_code: int) -> Optional[str]:
        try:
            url_object = json.loads(self.blob())
        except json.decoder.JSONDecodeError:
            return None

        assert (
            url_object["t"] == int_code
        ), "This datatoken does not appear to have a direct consume url."

        return url_object.get("url")

    @enforce_types
    def get_metadata_url(self) -> str:
        # grab the metadatastore URL from the DataToken contract (@token_address)
        return self._get_url_from_blob(1)

    @enforce_types
    def get_simple_url(self) -> Optional[str]:
        return self._get_url_from_blob(0)

    @enforce_types
    def calculate_token_holders(
        self, from_block: Optional[int], to_block: Optional[int], min_token_amount: int
    ) -> List[Tuple[str, int]]:
        """Returns a list of addresses with token balances above a minimum token
        amount. Calculated from the transactions between `from_block` and `to_block`."""
        all_transfers, _ = self.get_all_transfers_from_events(from_block, to_block)
        balances_above_threshold = []
        balances = DataToken.calculate_balances(all_transfers)
        _min = min_token_amount
        balances_above_threshold = sorted(
            [(a, b) for a, b in balances.items() if b > _min],
            key=lambda x: x[1],
            reverse=True,
        )
        return balances_above_threshold

    ################
    # Helpers
    @staticmethod
    @enforce_types
    def calculate_balances(transfers: List[Tuple]) -> List[Tuple[str, int]]:
        _from = [t[0].lower() for t in transfers]
        _to = [t[1].lower() for t in transfers]
        _value = [t[2] for t in transfers]
        address_to_balance = dict()
        address_to_balance.update({a: 0 for a in _from})
        address_to_balance.update({a: 0 for a in _to})
        for i, acc_f in enumerate(_from):
            v = int(_value[i])
            address_to_balance[acc_f] -= v
            address_to_balance[_to[i]] += v

        return address_to_balance
