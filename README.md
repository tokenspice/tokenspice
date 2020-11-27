**WARNING: this is WIP code. Pre-alpha blah blah.**

# TokenSPICE : Token Simulator with Python or EVM agents

TokenSPICE simulates tokenized ecosystems using an agent-based approach.

Agents may be written in pure Python, or with an EVM-based backend. (The [original version](https://github.com/oceanprotocol/tokenspice) was pure Python.)

TokenSPICE can be used to help design, tune, and verify tokenized ecosystems in an overall Token Engineering (TE) flow.

It's currently tuned to model [Ocean Market](https://market.oceanprotocol.com). The original version was tuned for the [Web3 Sustainability Loop](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). However you can rewire the "netlist" of "agents" to simulate whatever you like. 

TokenSPICE was meant to be simple. It definitely makes no claims on "best" for anything. Maybe you'll find it useful.

# Flow for experiments

1. Update controllables/uncontrollables/metrics. Change .sol, .py, etc
   - Debug using pytest for everything. (It imports old unittest stuff)

2. (if needed) recompile & deploy sol code. Leverage what the team already built.
   - HOW: cd ~/code/contracts; npm i; npm run compile; npm run deploy
   - Then, deployed contract addresses are at: ./artifacts/address.json; ABIs in that dir too
3. TokenSPICE "run_1" or "run_n", output csvs
4. TokenSPICE "plot_1" or "plot_n", output pngs
5. Analyze results
6. Goto 1

# TokenSPICE Design

### Top-level agent architecture

- All agents inherit BaseAgent
- Controllable agents use EVM.
- Uncontrollable agents use pure Python. But each has EOA.
   - Therefore the core dynamics are still on-chain
       
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

# A. Setup

## Set up environment
```
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

Open a separate terminal and cd into the project directory.

Activate the conda env't:
```console
conda activate tokenspiceenv
```

Then run ganache:
```console
./ganache.py
```

Note: you could run ganache directly, but then you have to add many special arguments. The script above does that for you.

## Deploy the smart contracts to ganache

Open a separate terminal.

Grab the contracts code (main, or a branch)
```console
git clone https://github.com/oceanprotocol/contracts
# OR
git clone --branch feature/1mm-prototype_alex https://github.com/oceanprotocol/contracts
```

Then, deploy. Here's how:
```console
cd contracts
npm i
npm run deploy
```

This will compile the .sol and deploy them to ganache chain. Then it will update contracts/artifacts/*.json files. 

Open `tokenspice.ini' and set ARTIFACTS_PATH = `<contracts_dir>/artifacts'.

Now, for each contract, TokenSPICE knows where to find it on ganache (address.json file) and what its interface is (*.json).


## Test one EVM-based test

```console
pytest test/test_btoken.py
```

## Test that everything is working

```console
pytest
```

## Do a first simulation run

To orient you, check out the command-line help. This is what's possible.
```
./help.py 
```

The rest of this section walks you through how to run your first simulation and view results. 

1. Open `~/tokenspice.ini` and set `safety = False`. That way we run faster:) 

2. Kick off a simulation run. The command below will run for 10 simulated years, save run results to `outdir_csv` directory, and send stdout and stderr to `out.txt` file.  
```
rm -rf outdir_csv; ./run_1.py 10 outdir_csv 1>out.txt 2>&1 & 
```

3. You can observe the run while it's in action, with the following command. When it's done year 10, press ctrl-c.
```
tail -f out.txt
```
 
4. Create plots from the run results. The command below grabs results from `outdir_csv` directory, then creates & stores image files `outdir_png` directory.
```
rm -rf outdir_png; ./plot_1.py outdir_csv outdir_png
```

5. View the images. The following command lets you cycle through viewing all the images in a directory.
```
eog outdir_png
```

Congratulations! You've just gone through a full simulation run & viewing of results.

Note that the results will have small numbers. That's on purpose: the parameters are initially set with super-conservative values. It's up to you to change them and play with them:) More on that in section C.

# B. Coming Back, Winding Down, etc.

So you know, here are the mechanics to have new sessions, wind down, etc. You don't need to repeat them right now. But keep them in your back pocket for when you return.

## New session, change some code
```
cd tokenspice
git pull [[sync repo]]
conda activate tokenspiceenv  [[activate env't]]
conda env update --name tokenspiceenv --file environment.yml --prune [[update the env't, get rid of unused pkgs]]
[[change file(s)]]
git add <changed filename>
git status -s [[check status]]
git commit -m "<my commit message>"
git push
```

## Wind down
```
conda deactivate  [[leave env't]]
```

## To fully remove environment
```
conda remove --name tokenspiceenv --all
```

# C. Diving Deeper

OK, let's play around more! We can change parameters or structure. Let's start with parameters.

## Play with different parameters

The parameters are initially set with super-conservative values. Not reflective of reality. 

Here's where to change parameters:
- `engine/SimStrategy.py` - the whole file is parameters
- `util/constants.py` - same thing
- `engine/SimState.py` - where "magic number" is given 
- simulation time when invoking the run. E.g. run for 20 years or 150 years.

So, try playing with different parameter values and see what the results are. 

Just follow the same flow as part A. You can use different output directories for each setting if you like. Or simply store the resulting images into a slide deck as you go (that's a workflow I like).

## Play with different structures

Up until now, we've only played with parameters. But TokenSPICE is allows for change in the structure too. 

The file `engine/SimState.py` is the "netlist" that wires up "agents". Each agent "does its thing" on each time step. The main result is that the agent may update its wallet (holds USD and OCEAN), or another internal state variable of the agent.

Many Agents are defined in agents.py, and some in their own .py file. You can change an existing agent behavior, change the netlist, or create your agents and netlists. 

If you make changes here, it's a great idea to write unit tests to make sure your agent behaves how you expect. You'll find that TokenSPICE has more than a few unit tests:) That's not by accident, it helps us to feel confident in the simulation results.

Before making changes, we recommend having a better understanding of how the system works. Which brings us to...

# Models

## Status quo model

<img src="images/model-status-quo.png" width="100%">

## New model 1

<img src="images/model-new1.png" width="100%">

[Gslides](https://docs.google.com/presentation/d/14BB50dkGXTcPjlbrZilQ3WYnFLDetgfMS1BKGuMX8Q0/edit#slide=id.p1)

# A Final Word, or Two

1. Be careful not to read *too* much into any model. As George Box said, "all models are wrong, but some are useful."

2. Have fun!

# License

Copyright ((C)) 2020 Ocean Protocol Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

