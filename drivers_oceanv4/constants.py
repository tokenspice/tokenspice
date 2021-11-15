#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
This module holds following default values for Gas price, Gas limit and more.

"""

ENV_GAS_PRICE = "GAS_PRICE"
ENV_MAX_GAS_PRICE = "MAX_GAS_PRICE"

GAS_LIMIT_DEFAULT = 1000000
MIN_GAS_PRICE = 1000000000

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
BLOB = "f8929916089218bdb4aa78c3ecd16633afd44b8aef89299160"

MAX_UINT256 = 2 ** 256 - 1

MAX_INT256 = 2 ** 255 - 1
MIN_INT256 = 2 ** 255 * -1

DEFAULT_NETWORK_NAME = "ganache"
NETWORK_NAME_MAP = {
    1: "Mainnet",
    3: "Ropsten",
    4: "Rinkeby",
    56: "BSC",
    137: "Polygon",
    246: "EnergyWeb",
    1285: "Moonriver",
    1287: "MoonbeamAlpha",
    1337: "Ganache",
    44787: "CeloAlfajores",
    80001: "Mumbai",
}

"""The interval in seconds when polling the latest block number
block_number poll interval = 1/2 average block time for a given chain"""
BLOCK_NUMBER_POLL_INTERVAL = {
    1: 6.5,
    3: 6.0,
    4: 7.5,
    56: 1.5,
    137: 1.0,
    246: 2.6,
    1285: 6.5,
    1287: 6.0,
    1337: 2.5,
    44787: 2.5,
    80001: 1.0,
}
