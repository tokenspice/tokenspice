# Higher-Level Tools

TokenSPICE lends itself well to having tools built on top for design entry, verification, design space exploration, and more. 

Here are some such tools, largely inspired by tools from circuit land. 
- Each tool can have just a backend, or both a backend and frontend. A frontend with good UX can make a huge difference. 
- Each tool can be applied for the initial design, before deployment. And, they can be used in real-time against *live chains*, for real-time verification, optimization, etc. How: grab the latest chain’s snapshot into ganache, run a local verification etc for a few seconds or minutes, then do transaction(s) on the live chain. This can lead to trading systems, failure monitoring, more.

## Design entry tools

- Schematic editor - be able to input netlists by editing a schematic. Examples:
  - [Circuits](https://www.google.com/search?q=spice+schematic+editor&sxsrf=ALeKk01lEnlL27hPsWzA_sBTOoxQLAlUJg:1626253838940&source=lnms&tbm=isch&sa=X&ved=2ahUKEwinnInTm-LxAhUNnYsKHe0mA1wQ_AUoAXoECAEQAw&biw=1600&bih=721#imgrc=TUv3yDrlTDLNVM)
  - [Videogames: machinations.io](https://machinations.io/)
  - [System Dynamics](https://systemdynamics.org/what-is-system-dynamics/): [stock and flow diagrams](https://www.google.com/search?q=stock+and+flow+diagram&sxsrf=AOaemvK9W36reEyVfw54RGs3JmLiwZbTDQ:1643101186893&source=lnms&tbm=isch&sa=X&ved=2ahUKEwj358v0xMz1AhUXSPEDHZU7CwkQ_AUoAXoECAEQAw&cshid=1643101212647476&biw=1514&bih=934&dpr=1) in [Stella](https://www.iseesystems.com/store/products/stella-professional.aspx) and [Vensim](https://vensim.com/) (commercial); [full sw list](https://en.wikipedia.org/wiki/Comparison_of_system_dynamics_software)
  - [Data pipelines via StreamSets](https://streamsets.com/learn/data-pipelines/)
- Auto schematic import - input a netlist, auto-generate a schematic visually. Uses optimization etc.
- Waveform viewer - build on `tsp.do_plot` with more a interactive tool. [Examples from circuits](https://www.google.com/search?q=spice+waveform+viewer&sxsrf=ALeKk02nY3U9rkOZuz58PNXWjoFY4MCcUQ:1626255741604&source=lnms&tbm=isch&sa=X&ved=2ahUKEwj9zareouLxAhXm-ioKHW0MCtgQ_AUoAXoECAEQAw&biw=1600&bih=721).

## Verification tools

Base tools:
- Corner simulation tool - simulate at pre-specified "corners". Corners are a small handful of points in random variable or worst-case variable space to simulate against. Enables rapid design-space exploration, because each you only simulate each design on corners
- Worst-case verification - verification across worst-case variables. E.g. via global optimization across worst-case variables. E.g. global synthesis across worst-case variables and agent python structures. Include corner extraction feature.
- 3-sigma verification - verification across random variables. E.g. via Monte Carlo analysis where all samples are drawn from the random variables' pdf, and each sample is simulated. Be able to simulate across >=1 worst-case corners; include stastitical extraction feature.

Advanced tools:
- High-sigma verification - verification across random variables, where catastrophic failure happens rarely, e.g. 1 in a million times (4.5 sigma) or 1 in a billion (6 sigma). E.g. using tricks from "rare event estimation" literature or [this book](https://www.amazon.com/Variation-Aware-Design-Custom-Integrated-Circuits/dp/146142268X). Be able to simulate across >=1 worst-case corners; include stastitical extraction feature.
- System identification - auto-extract a TokenSPICE netlist from raw blockchain info. To make it more tractable, use a parameterized netlist and Solidity code where possible. Ie "whitebox" not "blackbox".
- Behavioral modeling - auto-extract a lower-fidelity / faster-simulating TokenSPICE netlist from a higher-fidelity TokenSPICE netlist & simulation run, with minimal loss of error. 
- Mixed-signal verification - include digital verification in the loop. Example: replace ganache with [hevm](https://fv.ethereum.org/2020/07/28/symbolic-hevm-release), which does fuzzing etc on Solidity.

## Design Space Exploration tools

Base tools:
- Sensitivity analysis - locally perterb design variables.
- Sweep analysis - sweep design variables one at a time. Ignore interactions.

Advanced tools:
- Fast sweep analysis - sweep across all design variables including interactions, but without combinatorial explosion via model-in-the-loop
- Local optimization - search across design variables to optimize for objectives & constraints
- Global optimization - search across all design variables, with affordances to not get stuck

Extra-advanced tools:
- Synthesis - search design variables *and structure*. E.g. Evolve solidity or EVM bytecode. AI DAOs that own themselves. Go nuts:)
- Variation-aware synthesis - all of the above at once. This isn’t easy! But it’s possible. Example: use MOJITO (http://trent.st/mojito/), but use TokenSPICE (not SPICE) and Solidity building blocks (not circuit ones) 

## More "Larger" Ideas for TokenSPICE

- "tsp publish" - publish sim results to Ocean
- Use Ocean to manage IP: contracts, agents, netlists, results. Or, using brownie pm? Result: TokenSPICE itself becomes super small, just an engine
- TokenSPICE inputs SPICE netlists. Pros: well-defined, battle-tested, built-in hierarchy, IP mgmt hooks, specifications of time series, compact, interoperability with SPICE tools.
- How to build / test the "SPICE format" and IP ideas: Make MOJITO work at the same time 
- Deploy to pypi. Make it easy to install separately
- Trading system using TokenSPICE predictions
