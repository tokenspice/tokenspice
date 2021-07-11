**WARNING: this is WIP code. Prototype, not fully functional, etc. Keep your expectations low. But maybe parts are useful to some:)**

# 🐠 TokenSPICE: EVM Agent-Based Token Simulator

TokenSPICE can be used to help design, tune, and verify tokenized ecosystems in an overall Token Engineering (TE) flow.

TokenSPICE simulates tokenized ecosystems using an agent-based approach.

Each "agent" is a class. Has a wallet, and does work to earn $. One models the system by wiring up agents, and tracking metrics (kpis). Agents may be written in pure Python, or with an EVM-based backend.

A "netlist" defines what you simulate, and how. It wires up a collection of agents to interact in a given way. You can write your own netlists to simulate whatever you like. The `assets/netlists` directory has examples.

TokenSPICE was meant to be simple. It makes no claims on "best". Maybe you'll find it useful.

[Documentation](https://www.notion.so/TokenSPICE2-Docs-b6fc0b91269946eb9f7deaa020d81e9a).

# Contents

- [🏗 Initial Setup](#-initial-setup)
- [🏄 Do Simulations, Make Changes](#-do-simulations-make-changes)
- [🐟 Updating Envt](#-updating-envt)
- [🦑 Netlists and Custom Simulations](#-netlists-and-custom-simulations)
- [🐡 Backlog](#-backlog)
  - [Kanban Board](https://github.com/oceanprotocol/tokenspice/projects/1?add_cards_query=is%3Aopen)
- [🐋 Benefits of EVM Agent Simulation](#-benefits-of-evm-agent-simulation)
- [🏛 License](#-license)

# 🏗 Initial Setup

## Set up environment

Open a new terminal and:
```console
#ensure brownie's *not* installed. It causes problems
pip uninstall eth-brownie

#clone repo
git clone https://github.com/oceanprotocol/tokenspice.git tokenspice
cd tokenspice

#make sure we're not in env't; remove old env'ts
conda deactivate
conda remove --name tokenspiceenv --all

#create a python-anaconda env't in location ~/anaconda3/envs/tokenspiceenv
conda env create -f environment.yml

#activate env't
conda activate tokenspiceenv
```

## Get Ganache running

Open a new terminal and:
```console
cd tokenspice

#active env't
conda activate tokenspiceenv

#run ganache
./ganache.py
```

Note: you could run ganache directly, but then you have to add many special arguments. The script above does that for you.

## Deploy the smart contracts to ganache

Open a separate terminal.


```console
#Grab the contracts code from main, *OR* (see below)
git clone https://github.com/oceanprotocol/contracts

#OR grab from a branch. Here's Alex's V4.1 prototype branch
git clone --branch feature/1mm-prototype_alex https://github.com/oceanprotocol/contracts
```

Then, deploy. In that same terminal:
```console
cd contracts

#one-time install
npm i

#compile .sol, deploy to ganache, update contracts/artifacts/*.json
npm run deploy
```

Finally, open `tokenspice/tokenspice.ini` and set `ARTIFACTS_PATH = contracts/artifacts`.
* Now, TokenSPICE knows where to find each contract on ganache (address.json file)
* And, it knows what each contract's interface is (*.json files).


## Test one EVM-based test

```console
conda activate tokenspiceenv
pytest web3engine/test/test_btoken.py 
```

## First usage of tsp

First, add pwd to bash path.
```console
export PATH=$PATH:.
```

`tsp` is the command-line module. To see help, call it with no args.
```console
tsp
```

## Run simulation

Here's an example on a supplied netlist `w3sl_noevm.py`.

Simulate the netlist, storing results to `outdir_csv`.
```console
tsp run assets/netlists/w3sl_noevm.py outdir_csv outdir_csv
```

Output plots to `outdir_png`, and view them.
```console
tsp plot outdir_csv outdir_png
eog outdir_png
```

# 🏄 Do Simulations, Make Changes

## Do Once, At Session Start

**Start chain.** Open a new terminal and:
```console
cd ~/code/tokenspice
conda activate tokenspiceenv
./ganache.py
```

**Deploy contracts.** Open a new terminal and:
```console
cd ~/code/contracts
npm run deploy
```

## Do >=1 Times in a Session

**Update simulation code.** Open a new terminal. In it:
```console
cd ~/code/tokenspice
conda activate tokenspiceenv
./emacs <path/foo.py>
#then change foo.py in editor
```

**Run tests.** In the same terminal as before:
```console
#run a single pytest-based test
pytest tests/test_foo.py::test_foobar

#run a single pytest-based test file
pytest tests/test_foo.py

#run all tests in engine/ directory
pytest engine/

#run all tests except web3engine/ (slow)
pytest --ignore=web3engine

#run all tests
pytest

#run static type-checking. Dynamic is automatic.
mypy --config-file mypy.ini ./
```

## Test that everything is working

```console
conda activate tokenspiceenv
pytest
```

**Commit changes.**
```console
git add <changed filename>
git status -s [[check status]]
git commit -m <my commit message>
git push

#or

git status -s [[check status]]
git commit -am <my commit message>
git push
```

# 🐟 Updating Envt

You don't need this info at the beginning, but it's good to know about as you make changes.

To change dependencies, first update `environment.yml`. Then:
```console
#make sure env't is active
conda activate tokenspiceenv

#main update. The 'prune' part gets rid of unused pkgs
conda env update --name tokenspiceenv --file environment.yml --prune
```

Leave environment:
```console
conda deactivate
```

Delete environment:
```console
conda remove --name tokenspiceenv --all
```

# 🦑 Netlists and Custom Simulations

## About Agents 

- All agents are written in Python
- Each Agent has an AgentWallet, which holds a Web3Wallet. The Web3Wallet holds a private key and creates TXs. 
- Some agents may wrap smart contracts deployed to EVM (eg BPool).

## Changing Sim Structure & Parameters

The **netlist** defines what you simulate, and how.

Sample netlists, given below, can be run out-of-the-box.

Or run your own custom simulation, by changing the netlist. You can change:
- Simulation run parameters
- What metrics (KPIs) to log, later called by `tsp plot`
- System-level structure & parameters - how agents are connected
- Individual agent structure & parameters - each agent instance. To change agent structure, you'll need to change its module (py or sol code). Unit tests are recommended.

## Sample Netlists

Netlists live at `assets/netlists/`.

### W3SL Netlist

W3SL = Web3 Sustainability Loop
 The original version was tuned for the [Web3 Sustainability Loop](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). However you can rewire the "netlist" of "agents" to simulate whatever you like. 

(FIXME add images - see tokenspice0.1)

### Ocean V3 Netlist

System-level design is W3SL. But now higher fidelity is added to the "data ecosystem" part. This is in order to better [Ocean Market](https://market.oceanprotocol.com) publishing, pool creation, staking, and data consumption.

The actual netlist is WIP.

<img src="images/model-status-quo.png" width="100%">

### Ocean V4 Netlist

Starts with Ocean V3, then makes staking safer via one-sided AMM bots. WIP.

<img src="images/model-new1.png" width="100%">

[GSlides for the above images](https://docs.google.com/presentation/d/14BB50dkGXTcPjlbrZilQ3WYnFLDetgfMS1BKGuMX8Q0/edit#slide=id.gac81e1e848_0_8)

# 🐡 Backlog

**[Kanban Board](https://github.com/oceanprotocol/tokenspice/projects/1?add_cards_query=is%3Aopen)**

### Context

* Intro to SPICE & TokenSPICE [[Gslides - short](https://docs.google.com/presentation/d/167nbvrQyr6vdvTE6exC1zEA3LktrPzbR08Cg5S1sVDs)] [[Gslides - long](https://docs.google.com/presentation/d/1yUrU7AI702zpRZve6CCR830JSXrpPmfg00M5x9ndhvE)]
* TE for Ocean V3 [[slides](http://trent.st/content/20201209%20TE%20for%20Ocean%20Protocol%20V3.pdf)] [[video](https://www.youtube.com/watch?v=ztnIf9gCsNI&ab_channel=TokenEngineering)] [[Gslides](https://docs.google.com/presentation/d/1DmC6wfyl7ZMjuB-h3Zbfy--xFuYSt3tGACpgfJH9ZFk/edit)], TE Community Workshop, Dec 9, 2020
* TE for Ocean V4.1 [[slides](http://trent.st/content/20210521%20Ocean%20Market%20Balancer%20Simulations%20For%20TE%20Academy.pdf)] [[video](https://www.youtube.com/watch?v=TDG53PTbqhQ&ab_channel=TokenEngineering)] [[GSlides](https://docs.google.com/presentation/d/1JfFi9hT4Lf3UQKfCXGDhA27YPpPcWsXU7YArfRGAmMQ/edit#slide=id.p1)], TE Academy, May 21, 2021

### Done so far:
- Wrote Ocean Market V4.1 prototype smart contracts
- Drew schematics for V3 & V4.1
- Adapted TokenSPICE code
  - Run EVM end-to-end via ganache
  - Lets third-parties deploy to ganache, then uses at their ABIs
  - ABIs are wrapped as classes, which are inside agents.
  - Already include: Ocean datatokens, Ocean datatoken factory, Ocean friendly fork of Balancer AMM, Balancer AMM factory, etc. Have Unit tests for all.
  - Started writing Python-level agent behaviors
- **Be able to specify a netlist and run, without having to fork** [#30](https://github.com/oceanprotocol/tokenspice/issues/30)

### Roadmap - Near Term

This work is geared towards verifying & tuning Ocean V4.1, which updates Ocean smart contracts for better IDOs through one-sided market makers and more.

1. **Get *some* overall loop running that includes at least one EVM agent** [#34](https://github.com/oceanprotocol/tokenspice/issues/34)
2. **Improve Continuous Integration** - various issues, see kanban 
3. **Finish + verify Ocean V3 agents** [#28](https://github.com/oceanprotocol/tokenspice/issues/28). AKA: System identification: high-fidelity model of Ocean V3 (w/ Balancer V1); fit the model to observed on-chain dynamics
4. **Finish + verify Ocean V4.1 agents** [#29](https://github.com/oceanprotocol/tokenspice/issues/29). AKA: Verification: high-fidelity model of Ocean V4 (w/ Balancer V2) base design, and the efficacy of each proposed mechanism.
5. **Design space exploration**: tuning of Ocean V4.1 (w/ Balancer V2 design). Manual or optimization-based.

### Roadmap - Longer Term

6. System identification: high-fidelity model of whole Balancer V1 ecosystem; fit the model to observed on-chain dynamics (up to when V2 released). Bring in uncontrollable variables (probabilistic & worst-case).
7. System identification: high-fidelity model of whole Balancer V1 & V2 ecosystem; fit the model to observed on-chain dynamics
8. Design space exploration: tuning of Balancer V2 Strategies to minimize IL and other objectives & constraints. Account for uncontrollable variables (probabilistic & worst-case).
10. Open-ended design space exploration: evolve solidity or EVM bytecode, go nuts. AI DAOs that own themselves. This will be fun:). But one step at a time.

And much more - it's largely up to the community. For example, it would be cool to have a [machinations.io](https://machinations.io/)-like interface:)

# 🐋 Benefits of EVM Agent Simulation

TokenSPICE 2 and other EVM agent-based simulators have these benefits:
- Faster and less error prone, because the model = the Solidity code. Don’t have to port any existing Solidity code into Python, just wrap it. Don’t have to write lower-fidelity equations.
- Enables rapid iterations of writing Solidity code -> simulating -> changing Solidity code -> simulating. At both the parameter level and the structural level. 
- Can quickly integrate Balancer V2 code. Then extend to model other AMMs. And other DeFi code. Etc etc.
- Plays well with other pure Python agents. Each agent can wrap Solidity, or be pure Python. 
- Super high fidelity simulations, since it uses the actual code itself. Enables modeling of uncontrollable variables, both random (probabilistic) ones and worst-case ones. 
- Can build higher-level CAD tools, that have TokenSPICE 2 in the loop: 
  - 3-sigma verification - verification of random variables, including Monte Carlo analysis
  - Worst-case analysis - verification across worst-case condition
  - Corner extraction - finding representative “corners” -- a small handful of points in uncontrollable variable space to simulate against for rapid design-space exploration
  - Local optimization - wiggle controllable params to optimize for objectives & constraints
  - Global optimization - “”, with affordances to not get stuck
  - Synthesis - “” but wiggle code structure itself in addition to parameters
  - Variation-aware synthesis - all of the above at once. This isn’t easy! But it’s possible. Example: use MOJITO (http://trent.st/mojito/), but use TokenSPICE 2 (not SPICE) and Solidity building blocks (not circuit ones) 
- Mental model is general enough to extend to Vyper, LLL, and direct EVM bytecode. Can extend to non-EVM blockchain, and multi-chain scenarios. Can extend to work with hierarchical building blocks. 
- Can also do real-time analysis / optimization / etc against live chains: grab the latest chain’s snapshot into ganache, run a local analysis / optimization etc for a few seconds or minutes, then do transaction(s) on the live chain. This can lead to trading systems, failure monitoring, more.

In short, there's a lot of promise. But, the code is young! There's a lot of software engineering work to be done. This can evolve into something very exciting:)

# 🏛 License

Copyright ((C)) 2021 Ocean Protocol Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

