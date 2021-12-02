# Code Quality: Style Guide and Tests

## Table of Contents

- [Style Guide](#style-guide)
- [On Tests](#tests)
- [Remote Tests](#remote-tests)
- [Local Tests](#local-tests)
- [Local Fixes](#local-fixes)

## Style Guide

Code and checks in TokenSPICE should strive to follow:
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) Style Guide, [PEP 20](https://www.python.org/dev/peps/pep-0020/) The Zen of Python, [PEP 484](https://www.python.org/dev/peps/pep-0484/) Type Hints, [PEP 257](https://www.python.org/dev/peps/pep-0257/) Docstring conventions
- And, most specifically, [`google` docstring convention](https://google.github.io/styleguide/pyguide.html) [[2](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)]. It's a good balance of compact, readable, and specific. Docstrings should include variable types if they are not explicitly type hints in code itself.
- pydocstyle v4.0.0 supports `google` docstring convention [[ref](http://www.pydocstyle.org/en/stable/error_codes.html#default-conventions)]. This means checks for all the errors except D203, D204, D213, D215, D400, D401, D404, D406, D407, D408, D409 and D413 . 


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

## On Tests

Ensure that the local tests are the same as remote; otherwise we'd end up fixing things we don't care about. 

Codacy supports testing across many tools at once. It's easy to run remotely. However to use locally, `codacy-cli` runs slowly and churns the CPU. There are so many unimportant tests that it obscures the important ones.

Therefore, we _only_ use pylint. It's 80% of the benefit with 20% of the effort. Setup:
- Locally: just use `pylint`, not `codacy-cli`
- Remotely: use codacy, but only pylint is used
- For both, ignore the checks D203, D204, etc as specified in the Style Guide above

## Remote Tests

[Codacy](https://www.codacy.com) is automatically run _remotely_ for each commit of each PR.
- [Here's the Codacy TokenSPICE dashboard](https://app.codacy.com/gh/tokenspice/tokenspice/dashboard?branch=main), including links to tests. To access this, you need special permissions; ask Trent.
- [These "Code Patterns" settings](https://app.codacy.com/gh/tokenspice/tokenspice/patterns/list) specify what checks are run vs ignored.

## Local Tests

Use `pylint`. [Here's a pylint tutorial.](https://pylint.pycqa.org/en/latest/tutorial.html).

Here's an example. In the terminal:
```console
pylint *
```

Pylint auto-loads `./pylintrc` and uses its options, such as ignoring D203, D204. 

Example pylint output:
```text
engine/SimEngine.py:9:0: W0611: Unused valuation imported from util (unused-import)
engine/AgentWallet.py:419:4: C0116: Missing function or method docstring (missing-function-docstring)
...
-----------------------------------
Your code has been rated at 8.07/10
```

To learn more about a complaint, some examples:
```console
pylint --help-msg=unused-import
pylint --help-msg=missing-function-docstring
```

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


