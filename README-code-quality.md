## Code Quality Tests

### 7.2 Code quality tests

Use [codacy-analysis-cli](https://github.com/codacy/codacy-analysis-cli).

First, install once. In a new console:

```console
curl -L https://github.com/codacy/codacy-analysis-cli/archive/master.tar.gz | tar xvz
cd codacy-analysis-cli-* && sudo make install
```

In main console (with venv on):

```console
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

Finally, you can [go here](https://app.codacy.com/gh/tokenspice/tokenspice/dashboard?branch=main) to see results of remotely-run tests. (You may need special permissions.)
