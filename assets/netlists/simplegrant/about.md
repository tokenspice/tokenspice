## About simplegrant Netlist

This netlist is a simple demonstrator, for users to gain insight into how TokenSPICE is structured.

[Here's the netlist code](netlist.py). It's just one file.

It has two agents:

- [GrantGivingAgent](../../agents/GrantGivingAgent.py) "granter1"
- [GrantTakingAgent](../../agents/GrantTakingAgent.py) "taker1"

As one might expect, granter1 gives grants to taker1 over time, until granter1 runs out of money.

