#!/usr/bin/env python

import eth_utils
import os

from web3tools.web3util import confFileValue

ganache_url = confFileValue('general', 'GANACHE_URL')

###add 'ganache' as a live network to brownie
os.system('brownie networks list|grep ganache > /tmp/networks.tmp')
with open ('/tmp/networks.tmp','r') as myfile:
    s = str(myfile.readlines())
    if 'ganache' not in s:
        chainid = '1234'  # arbitrary, just can't be duplicate
        os.system(f'brownie networks add Ethereum ganache host={ganache_url} chainid={chainid}')

###the rest of this gets ganache-cli going, populating accounts found in ~/tokenspice.ini

# grab private keys
alice_private_key = confFileValue('ganache', 'TEST_PRIVATE_KEY1')
bob_private_key = confFileValue('ganache', 'TEST_PRIVATE_KEY2')
factory_deployer_private_key = confFileValue('ganache', 'FACTORY_DEPLOYER_PRIVATE_KEY')

# launch ganache-cli and give each private account 100 eth. Port must match that of ganache_url
amount_eth = 100
amount_wei = eth_utils.to_wei(amount_eth, 'ether')
os.system(
    f'ganache-cli --port 8545 --gasLimit 10000000000 --gasPrice 1 ---hardfork istanbul --account="{alice_private_key},{amount_wei}" --account="{bob_private_key},{amount_wei}" --account="{factory_deployer_private_key},{amount_wei}"')
