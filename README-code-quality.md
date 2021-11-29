# Code Quality Tests

 Contents

- [Remote](#remote)
- [Local](#local)
  - [Local Install](#local-install)
  - [Local Basic Runs](#local-basic-runs)
  - [Local Runs Like Remote](#local-runs-like-remote)

## Remote

[Codacy](https://www.codacy.com) is automatically run _remotely_ for each commit of each PR.
- **[Here's the Codacy TokenSPICE dashboard](https://app.codacy.com/gh/tokenspice/tokenspice/dashboard?branch=main)**, including links to tests. To access this, you need special permissions; ask Trent.

## Local

To iterate quickly, run Codacy _locally_ with [codacy-analysis-cli](https://github.com/codacy/codacy-analysis-cli).

### Local Install

First, install once. In a new console:

```console
curl -L https://github.com/codacy/codacy-analysis-cli/archive/master.tar.gz | tar xvz
cd codacy-analysis-cli-* && sudo make install
```

### Local Basic Runs

Here's how to run it. (See below to check the same things as remote runs.)

```console
source venv/bin/activate

#run all tools, plus Metrics and Clones data.
codacy-analysis-cli analyze --directory ~/code/tokenspice

#run tools individually
codacy-analysis-cli analyze --directory ~/code/tokenspice --tool Pylint
codacy-analysis-cli analyze --directory ~/code/tokenspice --tool Prospector
codacy-analysis-cli analyze --directory ~/code/tokenspice --tool Bandit
```

You'll get a report that looks like this.

```console
Found [Error] `No name 'valuation' in module 'util'` in SimEngine.py:8 (PyLint_E0611)
Found [Info] `Argument name "dt" doesn't conform to snake_case naming style` in AgentBase.py:97 (PyLint_C0103)
Found [Info] `Variable name "w2" doesn't conform to snake_case naming style` in test/test_AgentWallet.py:130 (PyLint_C0103)
Found [Info] `Missing method docstring` in AgentWallet.py:66 (PyLint_C0111)
Found [Error] `No name 'SimEngine' in module 'engine'` in test/test_SimEngine.py:7 (PyLint_E0611)
Found [Metrics] in SimStateBase.py:
  CC - 2
  LOC - 22
  CLOC - 9
  #methods - 7
```

(C)LOC = (Commented) Lines Of Code.

### Local Runs Like Remote

**[Here are "Code Patterns" settings](https://app.codacy.com/gh/tokenspice/tokenspice/patterns/list)**. They specify what checks are run.

To replicate the settings locally, you need to [specify](https://github.com/codacy/codacy-analysis-cli#project-token) the "Project Token" or "API Token". Here's an example. You need to provide your own token and username.
```console
codacy-analysis-cli analyze --api-token FOO --username BAR --project tokenspice
```

