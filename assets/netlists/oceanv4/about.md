## About oceanv4 Netlist

Starts with Ocean V3, then makes staking safer via one-sided AMM bots. WIP.

<img src="images/model-new1.png" width="100%">

[GSlides for the above image](https://docs.google.com/presentation/d/14BB50dkGXTcPjlbrZilQ3WYnFLDetgfMS1BKGuMX8Q0/edit#slide=id.gac81e1e848_0_8)

## Prerequisites

- Linux/MacOS
- Python 3.8.5+
- Node 17.1.0+. [Upgrade instrs](https://askubuntu.com/a/480642)

## Set up environment

Open a new terminal and:
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
```

## Get Ganache running

To deploy, oceanv3 uses truffle, and oceanv4 uses [hardhat](https://hardhat.org/getting-started/). Both deploy _to_ the ganache chain.

Open a new terminal and:
```console
#install Ganache (if you haven't yet)
npm install ganache-cli --global

#Do a workaround for a bug introduced in Node 17.0.1 in Oct 2021
export NODE_OPTIONS=--openssl-legacy-provider

#activate env't
cd tokenspice
source venv/bin/activate

#run ganache.py. It calls ganache cli and fills in many arguments for you.
./ganache.py
```

## Deploy Ocean V4 smart contracts


Open a new terminal, and:
```console
#Grab the contracts code from main
git clone https://github.com/oceanprotocol/contracts

#Switch to oceanv4 branch
git checkout v4main

#one-time install
npm install

#work around Node 17.x bug
export NODE_OPTIONS=--openssl-legacy-provider

#compile the contracts
npx hardhat compile

#set envvars
export NETWORK_RPC_URL=http://127.0.0.1:8545/
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
export ADDRESS_FILE=addresses/address.json

#Deploy compiled bytecode to ganache
npx hardhat run scripts/deploy-contracts.js --network localhost
```

## Point TokenSPICE to the deployed contracts
Finally, open tokenspice/tokenspice.ini and set: `ARTIFACTS_PATH = contracts/artifacts/`, and `ADDRESSES_PATH = contracts/addresses/`

- Now, TokenSPICE knows where to find each contract (address.json file)
- And, it knows what each contract's interface is (*.json files).

## Testing it

Status quo relative locations of V3 and V4 ocean artifacts. They will likely change; as they do, please update here.

| What    | v3             | v4               |
| ----    | ----           | ----             |
|     |            |              |
| **Drivers** | `web3engine/`    | `drivers_oceanv4/` |
| **Agents**  | `assets/agents/` | `assets/agents/`, `assets/netlists/oceanv4/v4Agents/` |
| **Netlist** | `assets/netlists/oceanv3/netlist.py` | `assets/netlists/oceanv4/netlist.py` |
| **web3tools** | `web3tools/`    | `drivers_oceanv4/` |


Ideally, the locations are the following. Once they're like this, we can merge the two tables into one.

| What    | oceanv3             | oceanv4               |
| ----    | ----           | ----             |
|     |            |              |
| **Contracts** | (don't store)   | (don't store) |
| **Models (py wrappers of ABIs)** | `assets/netlists/oceanv3/models`    | `assets/netlists/oceanv4/models/` |
| **Agents**  | General across >1 netlist (non-EVM, EVM base classes): `assets/agents/`, EVM: `assets/netlists/oceanv3/agents/`   | Pattern is like oceanv3. `assets/agents/`, `assets/netlists/oceanv4/agents/` |
| **Netlist** | `assets/netlists/oceanv3/netlist.py` | `assets/netlists/oceanv4/netlist.py` |
| **General Web3 contracts utilities** |  `assets/netlists/oceanv3/web3tools`    | `assets/netlists/oceanv4/web3tools/` |

Let's test! Open a new terminal and:

```console
#if needed, activate env't
source venv/bin/activate

#run test
pytest assets/netlists/oceanv4/models/test//test_btoken.py::test_OCEAN
```