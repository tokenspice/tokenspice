**WARNING: this is WIP code. Prototype, not fully functional, etc. Keep your expectations low. But maybe parts are useful to some:)**

# 🐠 TokenSPICE: EVM Agent-Based Token Simulator

TokenSPICE can be used to help design, tune, and verify tokenized ecosystems in an overall Token Engineering (TE) flow.

TokenSPICE simulates tokenized ecosystems using an agent-based approach.

Each “agent” is a class. Has a wallet, and does work to earn $. One models the system by wiring up agents, and tracking metrics (kpis). Agents may be written in pure Python, or with an EVM-based backend. (The [original version](https://github.com/oceanprotocol/tokenspice0.1) was pure Python. This repo supersedes the original.)

It's currently tuned to model [Ocean Market](https://market.oceanprotocol.com). The original version was tuned for the [Web3 Sustainability Loop](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). However you can rewire the "netlist" of "agents" to simulate whatever you like. Simply fork it and get going.

TokenSPICE was meant to be simple. It definitely makes no claims on "best" for anything. Maybe you'll find it useful.

[Documentation](https://www.notion.so/TokenSPICE2-Docs-b6fc0b91269946eb9f7deaa020d81e9a).

# Contents

- [🏗 Initial Setup](#-initial-setup)
- [🐟 Updating Envt](#-updating-envt)
- [🏄 Do Simulations, Make Changes](#-do-simulations-make-changes)
- [🦑 TokenSPICE Design](#-tokenspice-design)
- [🐡 Backlog](#-backlog)
  - [Kanban Board](https://github.com/oceanprotocol/tokenspice2/projects/1?add_cards_query=is%3Aopen)
- [🐋 Benefits of EVM Agent Simulation](#-benefits-of-evm-agent-simulation)
- [🏛 License](#-license)

# 🏗 Initial Setup

## Set up environment

Open a new terminal and:
```console
#ensure brownie's *not* installed. It causes problems
pip uninstall eth-brownie

#clone repo
git clone https://github.com/oceanprotocol/tokenspice2.git tokenspice
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

## Test that everything is working

```console
conda activate tokenspiceenv
pytest
```

## Linting

Run linting, aka static type-checking by:

```console
mypy --config-file mypy.ini ./
```

Note: TokenSPICE also uses the `enforce_types` library for *dynamic* type-checking. 

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

**Change sim settings as needed.**
- To run faster: open `tokenspice.ini` and set `safety = False`. 

**Run simulation.** Here, we run a 10-day sim, storing to `outdir_csv`. Observe the results while running. See `help.py` for more options.
```console
rm -rf outdir_csv; ./run_1.py 10 outdir_csv 1>out.txt 2>&1 &
tail -f out.txt

Create plots from run results, and store them in `outdir_png`. Then view the images.
```console
rm -rf outdir_png; ./plot_1.py outdir_csv outdir_png
eog outdir_png
#finally, maybe import pngs into GSlides 
```

Then repeat previous steps as desired.

# 🦑 TokenSPICE Design

# Architecture, Controllables, Uncontrollables, Metrics

### Top-level agent architecture

- All agents inherit BaseAgent
- Controllable agents use EVM.
- Uncontrollable agents use pure Python. But each has EOA.
   - Therefore the core dynamics are still on-chain

### AgentWallet connects Python agents to web3 behavior

- Each Agent has an AgentWallet.
- AgentWallet is the main bridge between higher-level Python and EVM.
- Each AgentWallet holds a Web3Wallet.
- The Web3Wallet holds a private key and creates TXs.

### Controllables

Controllable agents (structure): 
- What agents: just Pool (incl. Strategies and Pool Controllers).
- The agent's state is stored on blockchain. Deployment is not in the scope of TokenSPICE right now. TokenSPICE just sees ABIs.
- PoolAgent.py wraps BPool.sol. Agent's wallet grabs values from BPool.sol
   - current design (.sol) is at oceanprotocol/contracts
   - new design (.sol) is at branch 'feature/1mm-prototype_alex'
   - how can PoolAgent see it? draw on btoken.py etc.

Controllable variables:
- Global design vars. E.g. schedule for token distribution.
- Design vars within controllable agents
       
### Uncontrollables 

Uncontrollable Agents:
- Uncontrollable agents use pure Python. But each has an Externally Owned Address (EOA) to interact w EVM. Implemented inside Wallet.
- What agents: 
   - Status quo design: Publisher, Dataconsumer, Stakerspeculator
   - New design 1: Publisher, Dataconsumer, Staker, Speculator

Uncontrollable Variables (Env & rnd structure & params)
- Global rndvars & envvars. 
- Rndvars and envvars within controllable agents
- Rndvars and envvars within uncontrollable agents
- Ranges for envvars, and parameters for rndvar pdfs, are in constants.py, etc.


### Metrics
- These are what's output by SimEngine.py into the CSV, then plotted
- In the future, we could get fancier by leveraging TheGraph. 


## Changing Sim Parameters

The parameters are initially set with super-conservative values. Not reflective of reality. 

Here's where to change parameters:
- `engine/SimStrategy.py` - the whole file is parameters
- `util/constants.py` - same thing
- `engine/SimState.py` - where "magic number" is given 
- simulation time when invoking the run. E.g. run for 20 years or 150 years.

So, try playing with different parameter values and see what the results are. 

## Changing Sim Structures

TokenSPICE allows for change in the structure too. 

The file `engine/SimState.py` is the "netlist" that wires up "agents". Each agent "does its thing" on each time step. The main result is that the agent may update its wallet (holds USD and OCEAN), or another internal state variable of the agent.

Many Agents are defined in agents.py, and some in their own .py file. You can change an existing agent behavior, change the netlist, or create your agents and netlists. 

If you make changes here, it's a great idea to write unit tests to make sure your agent behaves how you expect. You'll find that TokenSPICE has more than a few unit tests:) That's not by accident, it helps us to feel confident in the simulation results.

Before making changes, we recommend having a better understanding of how the system works. Which brings us to...

## Schematics - Ocean V3 & V4.1

Ultimately we aim for TokenSPICE to allow arbitary netlists. Since TokenSPICE already has good fundamentals (python, agent-based, EVM), then allowing this isn't magical or difficult, it just needs some dedicated software engineering. See backlog below for details. 

In the meantime, it's hardcoded for the Web3 Sustainability Loop, with higher fidelity added to the "ecosystem" box; for Ocean this is the "data marketplaces ecosystem". Here are the schematics for that ecosystem, for Ocean V3 and Ocean V4.1. This is what TokenSPICE is wired to model. (But beware: things aren't fully wired up! Right now it's using the old agents without any EVM.)

### Ocean V3 Model

<img src="images/model-status-quo.png" width="100%">

### Ocean V4.1 Model

Ocean V4.0 makes Ocean more flexible. Ocean V4.1 is "Better Staking / IDOs". Our focus is V4.1. 

<img src="images/model-new1.png" width="100%">

[GSlides for the above images](https://docs.google.com/presentation/d/14BB50dkGXTcPjlbrZilQ3WYnFLDetgfMS1BKGuMX8Q0/edit#slide=id.gac81e1e848_0_8)

# 🐡 Backlog

**[Kanban Board](https://github.com/oceanprotocol/tokenspice2/projects/1?add_cards_query=is%3Aopen)**

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

### Roadmap - Near Term

This work is geared towards verifying & tuning Ocean V4.1, which updates Ocean smart contracts for better IDOs through one-sided market makers and more.

1. **Get *some* overall loop running that includes at least one EVM agent** [#34](https://github.com/oceanprotocol/tokenspice2/issues/34)
1. **Be able to specify a netlist and run, without having to fork** [#30](https://github.com/oceanprotocol/tokenspice2/issues/30)
2. **Improve Continuous Integration** - various issues, see kanban 
3. **Finish + verify Ocean V3 agents** [#28](https://github.com/oceanprotocol/tokenspice2/issues/28). AKA: System identification: high-fidelity model of Ocean V3 (w/ Balancer V1); fit the model to observed on-chain dynamics
4. **Finish + verify Ocean V4.1 agents** [#29](https://github.com/oceanprotocol/tokenspice2/issues/29). AKA: Verification: high-fidelity model of Ocean V4 (w/ Balancer V2) base design, and the efficacy of each proposed mechanism.
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

