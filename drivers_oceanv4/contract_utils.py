#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import importlib
import json
import logging
import os
from typing import Any, Dict, Optional

# import artifacts  # noqa
from contracts import artifacts
from enforce_typing import enforce_types
from jsonsempai import magic  # noqa: F401
from web3.contract import Contract
from web3.main import Web3
from pathlib import Path
import configparser
from util import constants


logger = logging.getLogger(__name__)



def abi(class_name: str):
    filename = abiFilename(class_name)
    with open(filename, 'r') as f:
        return json.loads(f.read())['abi']

def abiFilename(class_name: str) -> str:
    """Given e.g. 'DTFactory', returns './artifacts/contracts/v3/V3DTFactory.sol/V3DTFactory.json`. It searches through subdirectories to find the path.
    """
    target_file = class_name + '.json'
    base_path = confFileValue('general', 'ARTIFACTS_PATH')
    paths = [path for path in Path(base_path).rglob(target_file)]
    path = str(paths[0])
    abspath = os.path.abspath(path)
    return abspath

@enforce_types
def get_contract_definition(contract_name: str) -> Dict[str, Any]:
    """Returns the abi JSON for a contract name."""
    try:
        # import ipdb
        # ipdb.set_trace()
        # return importlib.import_module(abiFilename(contract_name)).__dict__
        with open(abiFilename(contract_name), 'r') as f:
            return json.loads(f.read())
    except ModuleNotFoundError:
        raise TypeError("Contract name does not exist in artifacts.")


@enforce_types
def load_contract(web3: Web3, contract_name: str, address: Optional[str]) -> Contract:
    """Loads a contract using its name and address."""
    contract_definition = get_contract_definition(contract_name)
    abi = contract_definition["abi"]
    bytecode = contract_definition["bytecode"]
    contract = web3.eth.contract(address=address, abi=abi, bytecode=bytecode)
    return contract



@enforce_types
def get_contracts_addresses(
    network: str, address_file: str
) -> Optional[Dict[str, str]]:
    """Get addresses for all contract names, per network and address_file given."""
    network_alias = {"ganache": "development"}

    if not address_file or not os.path.exists(address_file):
        return None
    with open(address_file) as f:
        addresses = json.load(f)

    network_addresses = addresses.get(network, None)
    if network_addresses is None and network in network_alias:
        network_addresses = addresses.get(network_alias[network], None)

    return network_addresses

def confFileValue(section: str, key: str) -> str:
    conf = configparser.ConfigParser()
    path = os.path.expanduser(constants.CONF_FILE_PATH)
    conf.read(path)
    return conf[section][key]
