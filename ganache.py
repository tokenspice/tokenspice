#! ./venv/bin/python3

from brownie._config import CONFIG
import eth_utils
import os

from ocean_lib.ocean.util import GANACHE_URL, confFileValue

network = 'ganache'

###add 'ganache' as a live network to brownie. We'll use this for deploy.py, quickstarts, debugging
chainid = '1234'  # arbitrary, just can't be duplicate
if 'ganache' not in CONFIG.networks:
    os.system(f'brownie networks add Ethereum ganache host={GANACHE_URL} chainid={chainid}')

###the rest of this gets ganache-cli going, populating accounts found in ~/ocean.conf

# grab private keys
alice_private_key = confFileValue(network, 'TEST_PRIVATE_KEY1')
bob_private_key = confFileValue(network, 'TEST_PRIVATE_KEY2')
factory_deployer_private_key = confFileValue(network, 'FACTORY_DEPLOYER_PRIVATE_KEY')

# launch ganache-cli and give each private account 100 eth. Port must match that of GANACHE_URL
amount_eth = 100
amount_wei = eth_utils.to_wei(amount_eth, 'ether')
os.system(
    f'ganache-cli --port 8545 --gasLimit 10000000000 --gasPrice 1 ---hardfork istanbul --account="{alice_private_key},{amount_wei}" --account="{bob_private_key},{amount_wei}" --account="{factory_deployer_private_key},{amount_wei}"')
