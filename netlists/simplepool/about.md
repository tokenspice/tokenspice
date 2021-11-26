# simplepool Netlist

## Overview

`simplepool` layers in EVM. [Its netlist](netlist.py) is at netlists/simplepool/netlist.py

The netlist is a single file, which defines everything needed: `SimStrategy`, `SimState`, etc.

The netlist's [`SimState`](https://github.com/tokenspice/tokenspice/blob/0826d78e0d8d6c4f3a03bf1916067fdfc77224fe/netlists/simplepool/netlist.py#L35) creates a [`PublisherAgent`](https://github.com/tokenspice/tokenspice/blob/main/agents/PublisherAgent.py) instance, which during the simulation run creates [`PoolAgent`](https://github.com/tokenspice/tokenspice/blob/main/agents/PoolAgent.py) objects.

Each `PoolAgent` holds a full-fidelity EVM Balancer as follows:

- At the top level, each `PoolAgent` Python object (an agent) holds a pool.BPool Python object (a driver to the lower level).
- One level lower, each `pool.BPool` Python object (a driver) points to a [BPool.sol](https://github.com/balancer-labs/balancer-core/blob/master/contracts/BPool.sol) contract deployment in Ganache EVM (actual contract).

You can view `pool.BPool` as a middleware driver to the contract deployed to EVM. Like all drivers, is in the `web3engine/ directory`.



