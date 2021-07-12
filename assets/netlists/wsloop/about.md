## About Wsloop Netlist

Wsloop = Web3 Sustainability Loop. [Here's the original article](https://blog.oceanprotocol.com/the-web3-sustainability-loop-b2a4097a36e). 

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
