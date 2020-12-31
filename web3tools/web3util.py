import configparser

import eth_account # type: ignore[import]
import json
import os
import typing
from web3 import Web3
from util import constants
from web3tools.account import privateKeyToAddress

def get_infura_url(infura_id):
    network = get_network()
    return f"wss://{network}.infura.io/ws/v3/{infura_id}"

_WEB3 = None
def get_web3():
    global _WEB3
    if _WEB3 is None:
        _WEB3 = Web3(get_web3_provider())
    return _WEB3

def get_web3_provider():
    assert get_network() == 'ganache', 'current implementation is ganache-only'
    url = confFileValue('general', 'GANACHE_URL')
    provider = Web3.HTTPProvider(url)
    return provider

def toBase18(amt: float) -> int:
    return toBase(amt, 18)


def toBase(amt: float, dec: int) -> int:
    """returns value in e.g. wei (taking e.g. ETH as input)"""
    return int(amt * 1*10**dec)
       

def fromBase18(num_base: int) -> float:
    return fromBase(num_base, 18)


def fromBase(num_base: int, dec: int) -> float:
    """returns value in e.g. ETH (taking e.g. wei as input)"""
    return float(num_base / (10**dec))

def abi(class_name: str):
    filename = abiFilename(class_name)
    with open(filename, 'r') as f:
        return json.loads(f.read())['abi']

def abiFilename(class_name: str) -> str:
    """Given e.g. 'DTFactory', returns './web3engine/DTFactory.json' """
    base_path = confFileValue('general', 'ARTIFACTS_PATH')
    path = os.path.join(base_path, class_name) + '.json'
    abspath = os.path.abspath(path)
    return abspath

def contractAddress(contract_name:str) -> str:
    """Given e.g. 'DTFactory', returns '0x98dea8...' """
    a = contractAddresses()
    return contractAddresses()[contract_name]

def contractAddresses():
    filename = contractAddressesFilename()
    with open(filename) as f:
        addresses = json.load(f)
    network = get_network()
    if network == 'ganache' and network not in addresses:
        network = 'development'
    assert network in addresses, \
        f"Wanted addresses at '{network}', only have them for {list(addresses.keys())}"
    return addresses[network]

def contractAddressesFilename():
    base_path = confFileValue('general', 'ARTIFACTS_PATH')
    return os.path.join(base_path, 'address.json')

def get_network():
    return confFileValue('general', 'NETWORK')

def confFileValue(section: str, key: str) -> str:
    conf = configparser.ConfigParser()
    path = os.path.expanduser(constants.CONF_FILE_PATH)
    conf.read(path)
    return conf[section][key]
