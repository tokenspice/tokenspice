# Code Quality Tests

## Table of Contents

- [Style Guide](#style-guide)
- [Remote Tests](#remote-tests)
- [Local Install](#local-install)
- [Local Tests](#local-tests)
- [Local Fixes](#local-fixes)

## Style Guide

We strive to follow:
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) Style Guide, [PEP 20](https://www.python.org/dev/peps/pep-0020/) The Zen of Python, [PEP 484](https://www.python.org/dev/peps/pep-0484/) Type Hints, [PEP 257](https://www.python.org/dev/peps/pep-0257/) Docstring conventions, and [Google-docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) with types
- Overall: strive for a good balance of compact, readable, and specific. Types can in docs can be skipped if they are type hints in the function declaration.

```python
def myfunction(param1, param2):
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        address: str -- Eth address
        agents: set of Agent -- 
        agent_ages: dict of {agent_name:str : agent_age:int} -- agent's ages
	completed: list of int --

    Returns:
        bool: Success if True
    """
```

## Remote Tests

[Codacy](https://www.codacy.com) is automatically run _remotely_ for each commit of each PR.
- **[Here's the Codacy TokenSPICE dashboard](https://app.codacy.com/gh/tokenspice/tokenspice/dashboard?branch=main)**, including links to tests. To access this, you need special permissions; ask Trent.
- **[These "Code Patterns" settings](https://app.codacy.com/gh/tokenspice/tokenspice/patterns/list)** specify what checks are run vs ignored.

## Local Install

To iterate quickly, we run Codacy _locally_ with [codacy-analysis-cli](https://github.com/codacy/codacy-analysis-cli).

First, install the cli. In a new console:

```console
cd tokenspice

curl -L https://github.com/codacy/codacy-analysis-cli/archive/master.tar.gz | tar xvz
cd codacy-analysis-cli-* && sudo make install
```

## Local Tests

We want the local tests to be the same as remote; otherwise we'd end up fixing things we don't care about. 

To replicate the remote settings locally, you need to [specify](https://github.com/codacy/codacy-analysis-cli#project-token) the "Project API Token" listed [here](https://app.codacy.com/gh/tokenspice/tokenspice/settings/integrations). Here's an example. 
```console
#set env't
source venv/bin/activate

#run codacy tests. We can specify a sub-directory
codacy-analysis-cli analyze --project-token Fk29iaf3sdp4JDSKpjp9rw --project tokenspice --directory ~/code/tokenspice

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


## Local Fixes

There are a couple approaches to making fixes:
1. Use automated tools like [`black`](https://pypi.org/project/black/)
2. Manually

We recommend to start with (1), then clean the rest with (2).

Usage of black on one file:
```console
black netlists/simplepool/test/test_netlist.py
```

It will output:
```console
reformatted netlists/simplepool/test/test_netlist.py
All done! ✨ 🍰 ✨
1 file reformatted.
```

For maximum productivity, use black on everything:
```console
black ./
```


