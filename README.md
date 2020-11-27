# TokenSPICE-EVM : Token Simulator with Python or EVM agents
TokenSPICE simulates tokenized ecosystems using an agent-based approach. It can be used to help design, tune, and verify tokenized ecosystems in an overall Token Engineering (TE) flow.

Agents may be written in pure Python, or with an EVM-based backend. (The [original](https://github.com/oceanprotocol/tokenspice) TokenSPICE was only pure Python.)

This TokenSPICE is tuned to model [Ocean Market](https://market.oceanprotocol.com). The original TokenSPICE was tuned for the ["Web3 Sustainability Loop"](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). However you can rewire the "netlist" of "agents" to simulate whatever you like. 

TokenSPICE was meant to be simple. It definitely makes no claims on "best" for anything. Maybe you'll find it useful.

# A. Quickstart

## Get going from scratch: set up environment
```
git clone https://github.com/oceanprotocol/tokenspice.git
cd tokenspice
conda deactivate  [[make sure we're not in env't]]
conda remove --name tokenspiceenv --all [[remove any old env'ts]]
conda env create -f environment.yml [[create a python-anaconda env't in location ~/anaconda3/envs/tokenspiceenv]]
conda activate tokenspiceenv [[activate env't]]
cp sample_tokenspice.conf ~/tokenspice.conf [[set up config file]]
python -m unittest [[test that everything is working]]
```

## Do a first run

To orient you, check out the command-line help. This is what's possible.
```
./help.py 
```

The rest of this section walks you through how to run your first simulation and view results. 

1. Open `~/tokenspice.conf` and set `safety = False`. That way we run faster:) 

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

## Understand how it works

Here's a starting point for understanding how TokenSPICE works. 

Here's the block diagram as presented for broader public consumption. While it says Ocean, the system-level design is really quite general (Web3 Sustainability Loop).

<img src="images/block-diagram-simpler-for-public.png" width="70%">

That diagram glossed over some details. Here is a more accurate block diagram. 

<img src="images/block-diagram-actual.png" width="70%">

The plots show many key performance indicators (KPIs) and other variables changing over time. Here's how they affect each other.

<img src="images/variables-being-modeled.png" width="100%">

We have slightly fancier models for growth rate and for token supply schedule. The details are [here](images/model-growth-rate.png) and [here](images/model-supply-schedule.png), respectively.

Model scope and limitations:
- TokenSPICE is currently modeling the Web3 Sustainability Loop, or equivalently, Ocean's system level design. 
- It does not attempt to model Ocean Market dynamics or the Balancer AMM at any level of fidelity. 
- Nor does it model staking in Ocean Market or elsewhere. Staking can have a big positive impact on token price.

To learn more:
- "The Web3 Sustainability Loop" blog post [[ref](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e)] is a good first external reference
- Then, "Ocean Token Model" blog post [[ref](https://blog.oceanprotocol.com/ocean-token-model-3e4e7af210f9)] adds a bit more fidelity.
- The Ocean Whitepaper [[ref](https://oceanprotocol.com/tech-whitepaper.pdf)] has more fidelity yet.
- Finally, we encourage taking a look at the code here! A good starting point is to see `SimEngine`'s loop, which calls `SimState`'s update, which calls each `Agent`'s update.

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

