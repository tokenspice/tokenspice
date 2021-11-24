# scheduler Netlist

Has these agents:

- VestingFunderAgent - creates a VestingWalletAgent, specifies beneficiary, fills it with funds
- VestingWalletAgent -- a smart contract robot that vests over time
- VestingBeneficiaryAgent - designated to receive the funds. Pings for release.

