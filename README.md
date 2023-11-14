<img src="images/tokenspice-banner-thin.png" width="100%">

# TokenSPICE: EVM Agent-Based Token Simulator

<div align="center">

<!-- Pytest and MyPy Badges -->
<img alt="Pytest Unit Testing" src="https://github.com/tokenspice/tokenspice/actions/workflows/pytest.yml/badge.svg">
<img alt="MyPy Static Type Checking" src="https://github.com/tokenspice/tokenspice/actions/workflows/mypy.yml/badge.svg">

<!-- Codacy Badges -->
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/1a5fde6940b246e1b0f927f96d05a285)](https://www.codacy.com/gh/tokenspice/tokenspice/dashboard?utm_source=github.com&utm_medium=referral&utm_content=tokenspice/tokenspice&utm_campaign=Badge_Coverage)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/1a5fde6940b246e1b0f927f96d05a285)](https://www.codacy.com/gh/tokenspice/tokenspice/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tokenspice/tokenspice&amp;utm_campaign=Badge_Grade)
  
</div>

⚠ _Note: as of mid 2023, this codebase is not being maintained. It might work, it might not. If you find a bug, feel free to report it, but do not expect it to be fixed. If you do a PR where tests pass, we're happy to merge it. And feel free to fork this repo and change it as you wish (including bug fixes)._

TokenSPICE simulates tokenized ecosystems via an agent-based approach, with EVM in-the-loop.

It can help in [Token](https://blog.oceanprotocol.com/towards-a-practice-of-token-engineering-b02feeeff7ca) [Engineering](https://www.tokenengineering.org) flows, to design, tune, and verify tokenized ecosystems. It's young but promising. We welcome you to contribute! 👋

- TokenSPICE simulates by simply running a loop. At each iteration, each _agent_ in the _netlist_ takes a step. That's it! [Simple is good.](https://www.goodreads.com/quotes/7144975-i-apologize-for-such-a-long-letter---i-didn-t)
- A netlist wires up a collection of agents to interact in a given way. Each agent is a class. It has an Ethereum wallet, and does work to earn money. Agents may be written in pure Python, or with an EVM-based backend.
- One models a system by writing a netlist and tracking metrics (KPIs). One can write their own netlists and agents to simulate whatever they like. The [netlists](https://github.com/tokenspice/tokenspice/tree/main/netlists) directory has examples.

# Contents

- [🏗 Initial Setup](#-initial-setup)
- [🏄 Running, Debugging](#-running-debugging)
- [🦑 Agents and Netlists](#-agents-and-netlists)
- [🐟 Updating Envt](#-updating-envt)
- [🐡 Backlog](#-backlog)
- [🐋 Benefits of EVM Agent Simulation](#-benefits-of-evm-agent-simulation)
- [🦈 Resources](#-resources)
- [🏛 License](#-license)

# 🏗 Initial Setup

## Prerequisites

- Linux/MacOS
- Python 3.8.5+
- solc 0.8.0+ [[Instructions](https://docs.soliditylang.org/en/v0.8.9/installing-solidity.html)]
- ganache. To install: `npm install ganache --global`
- nvm 16.13.2, _not_ nvm 17. To install: `nvm install 16.13.2; nvm use 16.13.2`. [[Details](https://github.com/tokenspice/tokenspice/issues/165)]

## Install TokenSPICE

Open a new terminal and:
```console
#clone repo
git clone https://github.com/tokenspice/tokenspice
cd tokenspice

#create a virtual environment
python3 -m venv venv

#activate env
source venv/bin/activate

#install dependencies
pip install -r requirements.txt

#install brownie packages (you can ignore FileExistsErrors)
./brownie-install.sh
```

**Potential issues & workarounds**

- Issue: Brownie doesn't support Python 3.11 yet. Workaround: before "install dependencies" step above, run `pip install vyper==0.3.7 --ignore-requires-python` and `sudo apt-get install python3.11-dev`
- Issue: MacOS might flag "Unsupported architecture". Workaround: install including ARCHFLAGS: `ARCHFLAGS="-arch x86_64" pip install -r requirements.txt`

## Run Ganache

From "Prerequisites", you should have Ganache installed.

Open a new console and go to tokenspice directory. Then:
```console
source venv/bin/activate
./ganache.py
```

This will start a Ganache chain, and populate 9 accounts.


## TokenSPICE CLI

`tsp` is the command-line interface for TokenSPICE.

Open a new console and go to tokenspice directory. Then:
```console
source venv/bin/activate

#add pwd to bash path
export PATH=$PATH:.

#see tsp help
tsp
```

## Compile the contracts

NOTE: if you have a directory named `contracts` from before, which is side-by-side with your `tokenspice` directory, you'll get [issues](https://github.com/tokenspice/tokenspice/issues/160). To avoid this, rename or move that contracts directory.

From the same terminal:
```console
#install 3rd party libs, then call "brownie compile" in sol057/ and sol080/
tsp compile
```

TokenSPICE sees smart contracts as classes. How:
- When it starts, it calls `brownie.project.load('./sol057', name="MyProject")` to load the ABIs in `./sol057/build/`. Similar for `sol080`.
- That's enough info to treat each contract in `sol057/contracts/` as a _class_. Then, call `deploy()` on it to create a new _object_.


# 🏄 Running, Debugging

## Testing

From terminal:
```console
#run single test. It uses brownie, which auto-starts Ganache local blockchain node.
pytest sol057/contracts/simpletoken/test/test_Simpletoken.py::test_transfer

#run all of a directory's tests
pytest sol057/contracts/simpletoken/test

#run all unit tests
pytest

#run static type-checking. By default, uses config mypy.ini. Note: pytest does dynamic type-checking.
mypy ./

#run linting on code style
pylint *

#auto-fix some pylint complaints
black ./
```

**[Go here](README-code-quality.md)** for details on linting / style.

## Simulating with TokenSPICE

From terminal:
```console
#run simulation, sending results to 'outdir_csv' (clear dir first, to be sure)
rm -rf outdir_csv; tsp run netlists/scheduler/netlist.py outdir_csv
```

You'll see an output like:
```text
Arguments: NETLIST=netlists/...
Launching 'ganache-cli --accounts 10 --hardfork ...
mnemonic: 'sausage bunker giant drum ...
INFO:master:Begin.
INFO:master:SimStrategy={OCEAN_funded=5.0, duration_seconds=157680000, ...}
INFO:master:Tick=0 (0.0 h, 0.0 d, 0.0 mo, 0.0 y); timestamp=1642844072; OCEAN_vested=0, ...
INFO:master:Tick=3 (2160.0 h, 90.0 d, 3.0 mo, 0.2 y); timestamp=1650620073; OCEAN_vested=0.0, ...
INFO:master:Tick=6 (4320.0 h, 180.0 d, 6.0 mo, 0.5 y); timestamp=1658396073; OCEAN_vested=0.0, ...
INFO:master:Tick=9 (6480.0 h, 270.0 d, 9.0 mo, 0.7 y); timestamp=1666172074; OCEAN_vested=0.0, ...
INFO:master:Tick=12 (8640.0 h, 360.0 d, 12.0 mo, 1.0 y); timestamp=1673948074; OCEAN_vested=0.0, ...
INFO:master:Tick=15 (10800.0 h, 450.0 d, 15.0 mo, 1.2 y); timestamp=1681724074; OCEAN_vested=0.232876 ...
```

Now, let's view the results visually. In the same terminal:
```console
#create output plots in 'outdir_png' (clear dir first, to be sure)
rm -rf outdir_png; tsp plot netlists/scheduler/netlist.py outdir_csv outdir_png

#view plots
eog outdir_png
```

To see the blockchain txs apart from the other logs: open a _new_ terminal and:
```console
#activate env't
cd tokenspice
source venv/bin/activate

#run ganache
export PATH=$PATH:.
tsp ganache
```

Now, from your original terminal:
```console
#run the sim. It will auto-connect to ganache
rm -rf outdir_csv; tsp run netlists/scheduler/netlist.py outdir_csv
```

For longer runs (eg wsloop), we can log to a file while watching the console in real-time:

```console
#run the sim in the background, logging to out.txt
rm -rf outdir_csv; tsp run netlists/wsloop/netlist.py outdir_csv > out.txt 2>&1 &

#monitor in real-time
tail -f out.txt
```

To kill a sim in the background:
```console
#find the background process
ps ax |grep "tsp run"

#example result:
#223429 pts/4    Rl     0:02 python ./tsp run netlists/wsloop/netlist.py outdir_csv

#to kill it:
kill 223429
```

## Debugging from Brownie Console

Brownie console is a Python console, with some extra Brownie goodness, so that we can interactively play with Solidity contracts as Python classes, and deployed Solidity contracts as Python objects.

From terminal:
```
#brownie needs a directory with ./contracts/. Go to one.
cd sol057/

#start console
brownie console
```

In brownie console:
```python
>>> st = Simpletoken.deploy("DT1", "Simpletoken 1", 18, Wei('100 ether'), {'from': accounts[0], "priority_fee": chain.priority_fee, "max_fee": chain.base_fee + 2 *
 chain.priority_fee})
Transaction sent: 0x9d20d3239d5c8b8a029f037fe573c343efd9361efd4d99307e0f5be7499367ab
  Gas price: 0.0 gwei   Gas limit: 6721975
  Simpletoken.constructor confirmed - Block: 1   Gas used: 601010 (8.94%)
  Simpletoken deployed at: 0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87

>>> st.symbol()
'DT1'

>>> st.balanceOf(accounts[0])/1e18

>>> dir(st)
[abi, address, allowance, approve, balance, balanceOf, bytecode, decimals, decode_input, get_method, get_method_object, info, name, selectors, signatures, symbol, topics, totalSupply, transfer, transferFrom, tx]
```

# 🦑 Agents and Netlists

## Agents Basics

Agents are defined at `agents/`. Agents are in a separate directory than netlists, to facilitate reuse across many netlists.

All agents are written in Python. Some may include EVM behavior (more on this later).

Each Agent has an [`AgentWallet`](https://github.com/tokenspice/tokenspice/blob/main/engine/AgentWallet.py), which holds a [`Web3Wallet`](https://github.com/tokenspice/tokenspice/blob/main/web3tools/web3wallet.py). The `Web3Wallet` holds a private key and creates transactions (txs).

## Netlists Basics

The netlist defines what you simulate, and how.

Netlists are defined at `netlists/`. You can reuse existing netlists or create your own.

## What A Netlist Definition Must Hold

TokenSPICE expects a netlist module (in a netlist.py file) that defines these specific classes and functions:

- `SimStrategy` class: simulation run parameters
- `KPIs` class and `netlist_createLogData()` function: what metrics to log during the run
- `netlist_plotInstructions()` function: how to plot the metrics after the run
- `SimState` class: system-level structure & parameters, i.e. how agents are instantiated and connected. It imports agents defined in `agents/*Agent.py`. Some agents use EVM. You can add and edit Agents to suit your needs.

## How to Implement Netlists

There are two practical ways to specify `SimStrategy`, `KPIs`, and so on for netlist.py:

1. **For simple netlists.** Have just one file (`netlist.py`) to hold all the code for each class and method given above. This is appropriate for simple netlists, like [simplegrant](https://github.com/tokenspice/tokenspice/blob/main/netlists/simplegrant/about.md) (just Python) and [simplepool](https://github.com/tokenspice/tokenspice/blob/main/netlists/simplepool/about.md) (Python+EVM).

2. **For complex netlists.** Have one or more _separate files_ for each class and method given above, such as `netlists/NETLISTX/SimStrategy.py`. Then, import them all into `netlist.py` file to unify their scope to a single module (`netlist`). This allows for arbitrary levels of netlist complexity. The [wsloop](https://github.com/tokenspice/tokenspice/blob/main/netlists/wsloop/about.md) netlist is a good example. It models the [Web3 Sustainability Loop](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e), which is inspired by the Amazon flywheel and used by [Ocean](https://www.oceanprotocol.com), [Boson](https://www.bosonprotocol.io/) and others as their system-level token design.

## Agent.takeStep() method

The class `SimState` defines which agents are used. Some agents even spawn other agents. Each agent object is stored in the `SimState.agents` object, a dict with  some added querying abilities. Key `SimState` methods to access this object are `addAgent(agent)`, `getAgent(name:str)`, `allAgents()`, and `numAgents()`. [`SimStateBase`](https://github.com/tokenspice/tokenspice/blob/main/engine/SimStateBase.py) has details.

Every iteration of the engine make a call to each agent's `takeStep()` method. The implementation of [`GrantGivingAgent.takeStep()`](https://github.com/tokenspice/tokenspice/blob/main/agents/GrantGivingAgent.py) is shown below. Lines 26–33 determine whether it should disburse funds on this tick. Lines 35–37 do the disbursal if appropriate.
There are no real constraints on how an agent's `takeStep()` is implemented. This which gives great TokenSPICE flexibility in agent-based simulation. For example, it can loop in EVM, like we show later.

<img src="images/takestep.png" width="100%">

## Netlist Examples
Here are some existing netlists.

- [simplegrant](netlists/simplegrant/about.md) - granter plus receiver, that's all. No EVM.
- [simplepool](netlists/simplepool/about.md) - publisher that periodically creates new pools. EVM.
- [scheduler](netlists/scheduler/about.md) - scheduled vesting from a wallet. EVM. 
- [wsloop](netlists/wsloop/about.md) - Web3 Sustainability Loop. No EVM.
- [oceanv3](netlists/oceanv3/about.md) - Ocean Market V3 - initial design. EVM.
- [oceanv4](netlists/oceanv4/about.md) - Ocean Market V4 - solves rug pulls. EVM.

To learn more about how TokenSPICE netlists are structured, we refer you to the [simplegrant](netlists/simplegrant/about.md) (pure Python) and [simplepool](netlists/simplepool/about.md) (Python+EVM) netlists, which each have more thorough explainers. 

# 🐡 Backlog

Larger things we'd like to see:
- **[Higher-level tools](README-tools.md)** that use TokenSPICE, including design entry, verification, design space exploration, and more. 
- Improvements to TokenSPICE itself in the form of faster simulation speed, improved UX, and more.

See this board: https://github.com/orgs/tokenspice/projects/1/views/1


# 🐋 Benefits of EVM Agent Simulation

TokenSPICE and other EVM agent simulators have these benefits:
- Faster and less error prone, because the model = the Solidity code. Don’t have to port any existing Solidity code into Python, just wrap it. Don’t have to write lower-fidelity equations.
- Enables rapid iterations of writing Solidity code -> simulating -> changing Solidity code -> simulating. 
- Super high fidelity simulations, since it uses the actual code itself. Enables modeling of design, random and worst-case variables.
- Mental model is general enough to extend to Vyper, LLL, and direct EVM bytecode. Can extend to non-EVM blockchain, and multi-chain scenarios. 
- Opportunity for real-time analysis / optimization / etc against *live chains*: grab the latest chain’s snapshot into ganache, run a local analysis / optimization etc for a few seconds or minutes, then do transaction(s) on the live chain. This can lead to trading systems, failure monitoring, more.

# 🦈 Resources

Here are further resources.

* [TokenSPICE medium posts](https://medium.com/tokenspice), starting with ["Introducing TokenSPICE"](https://medium.com/tokenspice/introducing-tokenspice-fb4dac98bcf9) 
* Intro to SPICE & TokenSPICE [[Gslides - short](https://docs.google.com/presentation/d/167nbvrQyr6vdvTE6exC1zEA3LktrPzbR08Cg5S1sVDs)] [[Gslides - long](https://docs.google.com/presentation/d/1yUrU7AI702zpRZve6CCR830JSXrpPmfg00M5x9ndhvE)]
* TE for Ocean V3 [[GSlides](https://docs.google.com/presentation/d/1DmC6wfyl7ZMjuB-h3Zbfy--xFuYSt3tGACpgfJH9ZFk/edit)] [[video](https://www.youtube.com/watch?v=ztnIf9gCsNI&ab_channel=TokenEngineering)] , TE Community Workshop, Dec 9, 2020
* TE for Ocean V4 [[GSlides](https://docs.google.com/presentation/d/1JfFi9hT4Lf3UQKfCXGDhA27YPpPcWsXU7YArfRGAmMQ/edit#slide=id.p1)] [[slides](http://trent.st/content/20210521%20Ocean%20Market%20Balancer%20Simulations%20For%20TE%20Academy.pdf)] [[video](https://www.youtube.com/watch?v=TDG53PTbqhQ&ab_channel=TokenEngineering)] , TE Academy, May 21, 2021

History:
- TokenSPICE was [initially built to model](https://github.com/tokenspice/tokenspice0.1) the [Web3 Sustainability Loop](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). It's now been generalized to support EVM, on arbitary netlists. 
- Most initial work was by [trentmc](https://github.com/trentmc) ([Ocean Protocol](https://www.oceanprotocol.com)); [several more contributors](https://github.com/tokenspice/tokenspice/graphs/contributors) have joined since 👪👨‍👩‍👧‍👧

Art:
- [TokenSPICE logos](https://github.com/tokenspice/art/blob/main/README.md)
- Fishnado image sources (CC): [[1](https://www.flickr.com/photos/robinhughes/404457553)] [[2](https://commons.wikimedia.org/wiki/File:Fish_Tornado_(226274841).jpeg)]

Other links:
- Twitter: [@tokenspice](https://twitter.com/tokenspice)
- Medium: [@tokenspice](https://medium.com/tokenspice)

# 🏛 License

The license is MIT. [Details](LICENSE)

<img src="images/fishnado2-crop.jpeg" width="100%">
