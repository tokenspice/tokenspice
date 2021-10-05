# Higher-Level Tools

TokenSPICE lends itself well to having tools built on top for design entry, verification, design space exploration, and more. 

Here are some such tools, largely inspired by tools from circuit land. 
- Each tool can have just a backend, or both a backend and frontend. A frontend with good UX can make a huge difference. 
- Each tool can be applied for the initial design, before deployment. And, they can be used in real-time against *live chains*, for real-time verification, optimization, etc. How: grab the latest chain’s snapshot into ganache, run a local verification etc for a few seconds or minutes, then do transaction(s) on the live chain. This can lead to trading systems, failure monitoring, more.

## Design entry tools

- Schematic editor - be able to input netlists by editing a schematic. [[Examples from circuit land](https://www.google.com/search?q=spice+schematic+editor&sxsrf=ALeKk01lEnlL27hPsWzA_sBTOoxQLAlUJg:1626253838940&source=lnms&tbm=isch&sa=X&ved=2ahUKEwinnInTm-LxAhUNnYsKHe0mA1wQ_AUoAXoECAEQAw&biw=1600&bih=721#imgrc=TUv3yDrlTDLNVM)]. [[Example from video game land: machinations.io](https://machinations.io/)]
- Waveform viewer - build on `tsp.do_plot` with more a interactive tool. [[Examples from circuit land](https://www.google.com/search?q=spice+waveform+viewer&sxsrf=ALeKk02nY3U9rkOZuz58PNXWjoFY4MCcUQ:1626255741604&source=lnms&tbm=isch&sa=X&ved=2ahUKEwj9zareouLxAhXm-ioKHW0MCtgQ_AUoAXoECAEQAw&biw=1600&bih=721)]

## Verification tools

- System identification - auto-extract a TokenSPICE netlist from raw blockchain info. To make it more tractable, use a parameterized netlist and Solidity code where possible. Ie "whitebox" not "blackbox".
- Corner extraction - finding representative “corners” -- a small handful of points in random variable or worst-case variable space to simulate against. Enables rapid design-space exploration, because each you only simulate each design on corners.
- Worst-case verification - verification across worst-case variables. E.g. via global optimization across worst-case variables. E.g. global synthesis across worst-case variables and agent python structures.
- 3-sigma verification - verification across random variables. E.g. via Monte Carlo analysis where all samples are drawn from the random variables' pdf, and each sample is simulated.
- High-sigma verification - verification across random variables, where catastrophic failure happens rarely, e.g. 1 in a million times (4.5 sigma) or 1 in a billion (6 sigma). E.g. using tricks from "rare event estimation" literature or [this book](https://www.amazon.com/Variation-Aware-Design-Custom-Integrated-Circuits/dp/146142268X).
- Behavioral modeling - auto-extract a lower-fidelity / faster-simulating TokenSPICE netlist from a higher-fidelity TokenSPICE netlist & simulation run, with minimal loss of error. 

## Design Space Exploration tools

- Sensitivity analysis - locally perterb design variables.
- Sweep analysis - sweep design variables one at a time. Ignore interactions.
- Fast sweep analysis - sweep across all design variables including interactions, but without combinatorial explosion via model-in-the-loop
- Local optimization - search across design variables to optimize for objectives & constraints
- Global optimization - search across all design variables, with affordances to not get stuck
- Synthesis - search design variables *and structure*. E.g. Evolve solidity or EVM bytecode. AI DAOs that own themselves. Go nuts:)
- Variation-aware synthesis - all of the above at once. This isn’t easy! But it’s possible. Example: use MOJITO (http://trent.st/mojito/), but use TokenSPICE (not SPICE) and Solidity building blocks (not circuit ones) 
