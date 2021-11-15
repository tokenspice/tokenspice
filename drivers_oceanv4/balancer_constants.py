#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
Contains `Balancer` related constants for
- `GASLIMIT_BFACTORY_NEWBPOOL`
- `BCONST_BONE`
- `BCONST_MIN_WEIGHT`
- `BCONST_MAX_WEIGHT`
- `BCONST_MAX_TOTAL_WEIGHT`
- `BCONST_MIN_BALANCE`
- `INIT_WEIGHT_DT`
- `INIT_WEIGHT_OCEAN`
- `DEFAULT_SWAP_FEE`
"""
from drivers_oceanv4.currency import to_wei

# ref: https://bankless.substack.com/p/how-to-create-your-own-balancer-pool
GASLIMIT_BFACTORY_NEWBPOOL = 5000000  # from ref above
GASLIMIT_BFACTORY_NEWMPOOL = 5000000  # from ref above

# from contracts/BConst.sol
# FIXME: grab info directly from contract
BCONST_BONE = 10 ** 18
BCONST_MIN_WEIGHT = BCONST_BONE  # Enforced in BPool.sol
BCONST_MAX_WEIGHT = BCONST_BONE * 50  # ""
BCONST_MAX_TOTAL_WEIGHT = BCONST_BONE * 50  # ""
BCONST_MIN_BALANCE = int(BCONST_BONE / 10 ** 12)  # "". value is 10**6

INIT_WEIGHT_DT = to_wei(9)
INIT_WEIGHT_OCEAN = to_wei(1)
DEFAULT_SWAP_FEE = to_wei("0.015")  # 1.5%
