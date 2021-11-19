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
Finally, open tokenspice/tokenspice.ini and set: `ARTIFACTS_PATH = ../contracts/artifacts/`, and `ADDRESSES_PATH = ../contracts/addresses/`

- Note that these paths are in the _contracts_ repo, not the _tokenspice_ repo!
- Now, TokenSPICE knows where to find each contract (address.json file)
- And, it knows what each contract's interface is (*.json files).

## Locations

Status quo locations of oceanv3 and v4 artifacts. Ideally the v3 ones will mirror the v4 ones. (But one step at a time.)

 What                             | v3               | v4
 ----                             | ----             | ----
 **Models (py wrappers of ABIs)** | `web3engine/`    | `assets/netlists/oceanv4/models/`
 **Agents**                       | `assets/agents/` | General across >1 netlist (non-EVM, EVM base classes): `assets/agents/`, EVM: `assets/netlists/oceanv4/agents/`
 **General Web3 contracts utils** | `web3tools/`     | `assets/netlists/oceanv4/web3tools/` |

## Testing

Let's test! Open a new terminal and:

```console
#if needed, activate env't
source venv/bin/activate

#run test
pytest assets/netlists/oceanv4/models/test/test_btoken.py::test_OCEAN
```