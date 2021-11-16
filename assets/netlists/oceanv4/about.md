## About oceanv4 Netlist

Starts with Ocean V3, then makes staking safer via one-sided AMM bots. WIP.

<img src="images/model-new1.png" width="100%">

[GSlides for the above image](https://docs.google.com/presentation/d/14BB50dkGXTcPjlbrZilQ3WYnFLDetgfMS1BKGuMX8Q0/edit#slide=id.gac81e1e848_0_8)

# Installation

## Prerequisites

- Linux/MacOS
- Python 3.8.5+
- Node 17.1.0+. [Upgrade instrs](https://askubuntu.com/a/480642)

## Run blockchain node, deploy smart contracts

Whereas oceanv3 netlist uses truffle to deploy, oceanv4 uses [hardhat](https://hardhat.org/getting-started/). Hardhat has its own test chain, _not_ ganache. So the instructions are a bit different.

Open a new terminal.

Get the code.
```console
#Grab the contracts code from main
git clone https://github.com/oceanprotocol/contracts

#Switch to oceanv4 branch:
git checkout v4main
```

One-time install:
```console
npm install
```

Node 17.x has an updated openssl that's a breaking change. To avoid problems in the forthcoming `npx` call, do: ([Reference](https://stackoverflow.com/a/69671888)]
```console
export NODE_OPTIONS=--openssl-legacy-provider
```

Run a local blockchain node (_not_ Ganache):
```console
npx hardhat node
```

The previous step should output something like:
```text
Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/

Accounts
========
Account #0: 0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

...

Account #19: 0x8626f6940e2eb28930efb4cef49b2d1f2c9c1199 (10000 ETH)
Private Key: 0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e
```

Now, compile the smart contracts:
```console
npx hardhat compile
```

Finally, deploy them to the blockchain node:
```console
npx hardhat run scripts/deploy-contracts.js
```
