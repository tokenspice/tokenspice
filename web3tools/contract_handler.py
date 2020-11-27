#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
import os

from web3 import Web3
from web3.contract import ConciseContract

from ocean_lib.web3_internal.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class ContractHandler(object):
    """
    Manages loading contracts and also keeps a cache of loaded contracts.

    Example:
        contract = ContractHandler.get('DTFactory')
        concise_contract = ContractHandler.get_concise_contract('DTFactory')

    """
    _contracts = dict()
    artifacts_path = None

    @staticmethod
    def get_contracts_addresses(network:str, address_file:str):
        with open(address_file) as f:
            addresses = json.load(f)
        return addresses[network]

    @staticmethod
    def set_artifacts_path(artifacts_path):
        if artifacts_path and artifacts_path != ContractHandler.artifacts_path:
            ContractHandler.artifacts_path = artifacts_path
            ContractHandler._contracts.clear()

    @staticmethod
    def _get(name, address=None):
        if address:
            return ContractHandler._contracts.get((name, address)) or ContractHandler._load(name, address)
        return ContractHandler._contracts.get(name) or ContractHandler._load(name, address)

    @staticmethod
    def get(name, address=None):
        """
        Return the Contract instance for a given name.

        :param name: Contract name, str
        :param address: hex str -- address of smart contract
        :return: Contract instance
        """
        return ContractHandler._get(name, address)[0]

    @staticmethod
    def get_concise_contract(name, address=None):
        """
        Return the Concise Contract instance for a given name.

        :param name: str -- Contract name
        :param address: hex str -- address of smart contract
        :return: Concise Contract instance
        """
        return ContractHandler._get(name, address)[1]

    @staticmethod
    def _set(name, contract):
        ContractHandler._contracts[(name, contract.address)] = (contract, ConciseContract(contract))
        ContractHandler._contracts[name] = ContractHandler._contracts[(name, contract.address)]

    @staticmethod
    def set(name, contract):
        """
        Set a Contract instance for a contract name.

        :param name: Contract name, str
        :param contract: Contract instance
        """
        ContractHandler._set(name, contract)

    @staticmethod
    def has(name, address=None):
        """
        Check if a contract is the ContractHandler contracts.

        :param name: Contract name, str
        :param address: hex str -- address of smart contract
        :return: True if the contract is there, bool
        """
        if address:
            return (name, address) in ContractHandler._contracts
        return name in ContractHandler._contracts

    @staticmethod
    def _load(contract_name, address=None):
        """Retrieve the contract instance for `contract_name` that represent the smart
        contract in the ethereum network.

        :param contract_name: str name of the solidity smart contract.
        :param address: hex str -- address of smart contract
        :return: web3.eth.Contract instance
        """
        assert ContractHandler.artifacts_path is not None, 'artifacts_path should be already set.'
        contract_definition = ContractHandler.read_abi_from_file(
            contract_name, ContractHandler.artifacts_path)

        if not address and 'address' in contract_definition:
            address = contract_definition.get('address')
            assert address, 'Cannot find contract address in the abi file.'
            address = Web3.toChecksumAddress(address)

        abi = contract_definition['abi']
        bytecode = contract_definition['bytecode']
        contract = Web3Provider.get_web3().eth.contract(address=address, abi=abi, bytecode=bytecode)
        ContractHandler._set(contract_name, contract)
        return ContractHandler._contracts[(contract_name, address)]

    @staticmethod
    def read_abi_from_file(contract_name, abi_path):
        path = None
        contract_name = contract_name + '.json'
        names = os.listdir(abi_path)
        # :HACK: temporary workaround to handle an extra folder that contain the artifact files.
        if len(names) == 1 and names[0] == '*':
            abi_path = os.path.join(abi_path, '*')

        for name in os.listdir(abi_path):
            if name.lower() == contract_name.lower():
                path = os.path.join(abi_path, contract_name)
                break

        if path:
            with open(path) as f:
                return json.loads(f.read())

        return None
