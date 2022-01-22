#!/usr/bin/env python

import argparse
import os

import eth_utils

from util.configutil import confFileValue

# Argument parsing for hiding ganache.py in background
parser = argparse.ArgumentParser()
parser.add_argument(
    "--run-in-background",
    action="store_true",
    help="Run ganache on background for further use of current terminal.",
)
args = parser.parse_args()

# Port in ganache_url must match ganache-cli call
port_number = "8545"
ganache_url = confFileValue("general", "GANACHE_URL")
assert port_number in ganache_url

# get ganache-cli going, populating accounts found in conf file

# grab private keys
alice_private_key = confFileValue("ganache", "TEST_PRIVATE_KEY1")
bob_private_key = confFileValue("ganache", "TEST_PRIVATE_KEY2")
factory_deployer_private_key = confFileValue("ganache", "FACTORY_DEPLOYER_PRIVATE_KEY")

# launch ganache-cli and give each private account 100 eth.
amount_eth = 100
amount_wei = eth_utils.to_wei(amount_eth, "ether")

ganache_command = f'ganache-cli --port {port_number} --gasLimit 10000000000 --gasPrice 1 ---hardfork istanbul --account="{alice_private_key},{amount_wei}" --account="{bob_private_key},{amount_wei}" --account="{factory_deployer_private_key},{amount_wei}"'  # pylint: disable=line-too-long

#add 7 more accounts, for 10 total. Private keys were chosen arbitrarily.
for private_key in [
        "0x69a0315f0a6932ca52d5b1ad9ce31b2fef7de658f8da625a6d97f4dbb3ba22c1",
        "0x2c06b48c205efccc3506430212630a11bcc99cad1994452898e5df63985eda10",
        "0xd890fedd404c6f49daf4be91cd720df22786e1d35d579b8372cc531eed80a267",
        "0x9da43e9603043299cd6c5aecec69b7713342496f3465caaadbee5db955f18010",
        "0x53a2a4124387132ceae955edb80f13aa549f2e956d3f8aae0383412a3c765a93",
        "0x1803ea57835da6f03f8b43458482f65f280600c278947fe0eaf78c5d7d260c81",
        "0xb13f2706716d269a9639f2eb99d38ba8aaef0e210d1b35a2e40e3e8b62ab76f9"]:
    ganache_command += f' --account="{private_key},{amount_wei}"'
    
if args.run_in_background:
    os.system(ganache_command + "&")
else:
    os.system(ganache_command)
