## About oceanv4 Netlist

Starts with Ocean V3, then makes staking safer via one-sided AMM bots. WIP.

<img src="images/model-new1.png" width="100%">

[GSlides for the above image](https://docs.google.com/presentation/d/14BB50dkGXTcPjlbrZilQ3WYnFLDetgfMS1BKGuMX8Q0/edit#slide=id.gac81e1e848_0_8)

# Installation

## Prerequisites

- Linux/MacOS
- Python 3.8.5+
- Node 17.1.0+. [Upgrade instrs](https://askubuntu.com/a/480642)

## Run blockchain node

Whereas oceanv3 netlist uses truffle to deploy, oceanv4 uses [hardhat](https://hardhat.org/getting-started/). Hardhat has its own test chain, _not_ ganache. So the instructions are a bit different.

Open a new terminal, and:
```console
#Grab the contracts code from main
git clone https://github.com/oceanprotocol/contracts

#Switch to oceanv4 branch
git checkout v4main
```

One-time install:
```console
npm install
```

Node 17.x has an updated openssl that's a breaking change [[Reference](https://stackoverflow.com/a/69671888)]. To avoid problems in the forthcoming `npx` call, do:
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

## Deploy smart contracts

Open a new terminal, and:

```console
cd contracts

#compile the contracts
npx hardhat compile

#set envvars
export NODE_OPTIONS=--openssl-legacy-provider
export NETWORK_RPC_URL=http://127.0.0.1:8545/
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
export ADDRESS_FILE=addresses/address.json

#deploy compiled bytecode to chain
npx hardhat run scripts/deploy-contracts.js
```

## Point TokenSPICE to the deployed contracts
Finally, open tokenspice/tokenspice.ini and set: `ARTIFACTS_PATH = contracts/artifacts/`, and `ADDRESSES_PATH = contracts/addresses/`

- Now, TokenSPICE knows where to find each contract (address.json file)
- And, it knows what each contract's interface is (*.json files).

## Testing it

Here are relative locations of V3 and V4 ocean artifacts. They will likely change; as they do, please update here.

| What    | v3             | v4               |
| ----    | ----           | ----             |
|     |            |              |
| **Drivers** | `web3engine/`    | `drivers_oceanv4/` |
| **Agents**  | `assets/agents/` | `assets/agents/`, `assets/netlists/oceanv4/v4Agents/` |
| **Netlist** | `assets/netlists/oceanv3/netlist.py` | `assets/netlists/oceanv4/netlist.py` |
| **web3tools** | `web3tools/`    | `drivers_oceanv4/` |

Let's test! Open a new terminal and:

```console
#clone repo
git clone https://github.com/oceanprotocol/tokenspice.git
cd tokenspice

#create a virtual environment
python3 -m venv venv

#activate env't
source venv/bin/activate

#install dependencies. Install wheel first to avoid errors.
pip install wheel
pip install -r requirements.txt

#run test
pytest drivers_oceanv4/test/test_btoken.py::test_OCEAN
```