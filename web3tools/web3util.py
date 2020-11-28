import configparser

import eth_account
import json
import os
import typing
from web3 import Web3
from util import constants
from web3tools.account import privateKeyToAddress
from web3tools.wallet import Wallet

def get_infura_url(infura_id):
    network = get_network()
    return f"wss://{network}.infura.io/ws/v3/{infura_id}"

def get_web3():
    return Web3(get_web3_provider())

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
    """Given e.g. 'DTFactory', returns './engine/evm/DTFactory.json' """
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
                                 
def buildAndSendTx(function,
                   from_wallet: Wallet,
                   gaslimit: int = constants.GASLIMIT_DEFAULT,
                   num_wei: int = 0):
    assert isinstance(from_wallet.address, str)
    assert isinstance(from_wallet.private_key, str)

    web3 = from_wallet.web3
    nonce = web3.eth.getTransactionCount(from_wallet.address)
    network = get_network()
    gas_price = int(confFileValue(network, 'GAS_PRICE'))
    tx_params = {
        "from": from_wallet.address,
        "value": num_wei,
        "nonce": nonce,
        "gas": gaslimit,
        "gasPrice": gas_price,
    }

    tx = function.buildTransaction(tx_params)
    signed_tx = web3.eth.account.sign_transaction(
        tx, private_key=from_wallet.private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    if tx_receipt['status'] == 0:  # did tx fail?
        raise Exception("The tx failed. tx_receipt: {tx_receipt}")
    return (tx_hash, tx_receipt)

    
