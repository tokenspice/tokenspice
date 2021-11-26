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

TokenSPICE simulates tokenized ecosystems via an agent-based approach, with EVM in-the-loop.

It can help in [Token](https://blog.oceanprotocol.com/towards-a-practice-of-token-engineering-b02feeeff7ca) [Engineering](https://www.tokenengineering.org) flows, to design, tune, and verify tokenized ecosystems. It's young but promising. We welcome you to contribute! 👋

- TokenSPICE simulates by simply running a loop. At each iteration, each _agent_ in the _netlist_ takes a step. That's it! [Simple is good.](https://www.goodreads.com/quotes/7144975-i-apologize-for-such-a-long-letter---i-didn-t)
- A netlist wires up a collection of agents to interact in a given way. Each agent is a class. It has an Ethereum wallet, and does work to earn money. Agents may be written in pure Python, or with an EVM-based backend.
- One models a system by writing a netlist and tracking metrics (KPIs). One can write their own netlists and agents to simulate whatever they like. The [netlists](https://github.com/tokenspice/tokenspice/tree/main/netlists) directory has examples.

# Contents

- [👪 Community](#-community)
- [🏗 Initial Setup](#-initial-setup)
- [🏄 Running, Debugging](#-running-debugging)
- [🦑 Agents and Netlists](#-agents-and-netlists)
- [🐟 Updating Envt](#-updating-envt)
- [🐡 Backlog](#-backlog)
  - [Kanban Board](https://github.com/tokenspice/tokenspice/projects/1)
- [🐋 Benefits of EVM Agent Simulation](#-benefits-of-evm-agent-simulation)
- [🦈 Resources](#-resources)
- [🏛 License](#-license)

# 👪 Community

- Discord: [te-tokenspice](https://discord.com/channels/701149241107808327/861621607825801216), [first time](https://discord.gg/FREcbdnUTw). 
- TokenSPICE hacking sessions: Mondays at 16.00 Berlin time. 120 min. [Zoom link](https://us02web.zoom.us/j/6985323627?pwd=YmxXaWNrdk1uSmV5bUFsaTJEWEtNZz09), Meeting ID 698 532 3627, Passcode 2021-99564. Anyone is welcome to drop in! 👋
- Twitter: [@tokenspice](https://twitter.com/tokenspice)
- Medium: [@tokenspice](https://medium.com/tokenspice)

History:
- TokenSPICE was [initially built to model](https://github.com/tokenspice/tokenspice0.1) the [Web3 Sustainability Loop](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). It's now been generalized to support EVM, on arbitary netlists. 
- Most initial work was by [trentmc](https://github.com/trentmc) ([Ocean Protocol](https://www.oceanprotocol.com)); [several more contributors](https://github.com/tokenspice/tokenspice/graphs/contributors) have joined since 👪👨‍👩‍👧‍👧

# 🏗 Initial Setup

## Prerequisites

- Linux/MacOS
- Python 3.8.5+
- solc 0.5.0+ [[Instructions](https://docs.soliditylang.org/en/v0.8.9/installing-solidity.html)]

## Install TokenSPICE

Open a new terminal and:
```console
#clone repo
git clone https://github.com/tokenspice/tokenspice
cd tokenspice

#[ONLY IF NOT MERGED YET] point to 'scheduler' branch
git checkout scheduler

#create a virtual environment
python3 -m venv venv

#activate env
source venv/bin/activate

#install dependencies. Install wheel first to avoid errors.
pip install wheel
pip install -r requirements.txt
```

## Start Ganache

Think of Ganache as local EVM blockchain network, with just one node.

If you haven't yet installed Ganache, here's how. Open a new terminal and:
```console
npm install ganache-cli --global
```

To run ganache, in the same terminal:
```
#Do a workaround for a bug introduced in Node 17.0.1 in Oct 2021
export NODE_OPTIONS=--openssl-legacy-provider

#activate env't
cd tokenspice
source venv/bin/activate

#run ganache.py. It calls ganache cli and fills in many arguments for you.
./ganache.py
```

TokenSPICE uses brownie. If ganache is running, brownie connects to it. Otherwise brownie starts ganache for its session. Recommendations:
- For unit tests, let Brownie auto-run ganache. Why: avoid brownie warnings on block height.
- For simulation runs (`tsp run`), run ganache separately. Why: avoid brownie clutter in stdout




## Compile & deploy contracts to ganache

Open a new terminal. From it:
```console
#activate env't
cd tokenspice
source venv/bin/activate

#install 3rd party contracts
brownie pm install OpenZeppelin/openzeppelin-contracts@2.1.1
```

Brownie compiles `.sol` files by calling the `solc` compiler. So, ensure that `solc` is installed and up-to-date.

The file `./brownie-config.yaml` holds compilation options. The `contracts/oceanv3` code (and `./contracts/`) need solc 0.5.7. Therefore open `brownie-config.yaml` and make sure the following lines are un-commented.
```text
compiler:
   solc:
       version: 0.5.7
```

Now, let's compile! From the same terminal:
```console
#compile everything in contracts/, including contracts/oceanv3/
brownie compile
```

It should output something like:
```text
Brownie v1.17.1 - Python development framework for Ethereum

Compiling contracts...
  Solc version: 0.8.10
  ...
Generating build data...
 - OpenZeppelin/openzeppelin-contracts@4.0.0/IERC20
 ...
 - VestingWallet057
 
Project has been compiled. Build artifacts saved at <your dir>/tokenspice/build/contracts
```

If brownie has any compile options set, e.g. if `brownie-config.yaml` has _any_ real content, then brownie will always re-compile before a `tsp` or `pytest` run. This can be time-consuming. To avoid this, comment out the lines `compiler: .. solc .. version: 0.5.7`. But be sure to un-comment them if you want a recompilation, otherwise it will compile at a higher `solc` version and give errors.

When TokenSPICE starts, it imports `util/constants.py`, and:
- it loads a project via `BROWNIE_PROJECT057 = brownie.project.load('./', name="MyProject")`. It loads the ABIs in the `build/` directory, which is enough info for brownie to start treating each contract from `contracts/` as a _class_.
- it connects to a network via: `brownie.network.connect('development')`
- now, each contract (class) can get deployed (as objects), dynamically as needed, via `BROWNIE_PROJECT057.deploy()'. The contracts don't need to get deployed up-front, nor do we need addresses of deployed contract up-front.


# 🏄 Running, Debugging

## Testing

Note: this will fail if there is a `contracts` directory side-by-side with tokenspice/. If you have such a directory, delete or move it.

From terminal:
```console
#run single test
pytest contracts/test/test_Simpletoken.py::test_transfer

#run all of a directory's tests
pytest contracts/test

#run all tests [FIXME!]
pytest

#run static type-checking. (pytest does dynamic type-checking.)
mypy --config-file mypy.ini ./
```

## TokenSPICE Command Line

Use `tsp`. From terminal:
```console
#add pwd to bash path
export PATH=$PATH:.

#see tsp help
tsp

#simulate 'scheduler' netlist, sending results to 'outdir_csv'
tsp run netlists/scheduler/netlist.py outdir_csv

#create output plots in 'outdir_png'
tsp plot netlists/scheduler/netlist.py outdir_csv outdir_png

#view plots
eog outdir_png
```

The [wsloop netlist](netlists/wsloop/about.md) is more complex. Below are sample results.

<img src="images/wsloop-example-small.png">

For runs that take more than a few seconds, it helps send stdout & stderr to a file while still monitoring the console in real-time. Here's how:

```console
#remove previous directory, then start running
rm -rf outdir_csv; tsp run netlists/wsloop/netlist.py outdir_csv > out.txt 2>&1 &

#monitor in real-time
tail -f out.txt
```

## Debugging from Brownie Console

From terminal:
```console
brownie console
```

In brownie console:
```python
>>> st = Simpletoken.deploy("DT1", "Simpletoken 1", 18, Wei('100 ether'), {'from': accounts[0]})
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
- (WIP) [oceanv3](netlists/oceanv3/about.md) - Ocean Market V3 - initial design. EVM.
- (WIP) [oceanv4](netlists/oceanv4/about.md) - Ocean Market V4 - solves rug pulls. EVM.

To learn more about how TokenSPICE netlists are structured, we refer you to the [simplegrant](netlists/simplegrant/about.md) (pure Python) and [simplepool](netlists/simplepool/about.md) (Python+EVM) netlists, which each have more thorough explainers. 

# 🐡 Backlog

**[Kanban Board](https://github.com/oceanprotocol/tokenspice/projects/1?add_cards_query=is%3Aopen)**

Some larger issues include:

- **Finish + verify Ocean V4 agents** #29. AKA: Verification: high-fidelity model of Ocean V4 (w/ Balancer V2) base design, and the efficacy of each proposed mechanism.

In the longer term, we can expect:
- Improvements to TokenSPICE itself in the form of faster simulation speed, improved UX, and more.
- **[Higher-level tools](README-tools.md)** that use TokenSPICE, including design entry, verification, design space exploration, and more. 

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
* TE for Ocean V3 [[Gslides](https://docs.google.com/presentation/d/1DmC6wfyl7ZMjuB-h3Zbfy--xFuYSt3tGACpgfJH9ZFk/edit)] [[video](https://www.youtube.com/watch?v=ztnIf9gCsNI&ab_channel=TokenEngineering)] , TE Community Workshop, Dec 9, 2020
* TE for Ocean V4 [[GSlides](https://docs.google.com/presentation/d/1JfFi9hT4Lf3UQKfCXGDhA27YPpPcWsXU7YArfRGAmMQ/edit#slide=id.p1)] [[slides](http://trent.st/content/20210521%20Ocean%20Market%20Balancer%20Simulations%20For%20TE%20Academy.pdf)] [[video](https://www.youtube.com/watch?v=TDG53PTbqhQ&ab_channel=TokenEngineering)] , TE Academy, May 21, 2021

Art:
- [TokenSPICE logos](https://github.com/tokenspice/art/blob/main/README.md)
- Fishnado image sources (CC): [[1](https://www.flickr.com/photos/robinhughes/404457553)] [[2](https://commons.wikimedia.org/wiki/File:Fish_Tornado_(226274841).jpeg)]

# 🏛 License

The license is MIT. [Details](LICENSE)

<img src="images/fishnado2-crop.jpeg" width="100%">
