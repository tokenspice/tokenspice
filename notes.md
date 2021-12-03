BROWNIE_PROJECT080 = project.Sol080Project

GOD_ACCOUNT = network.accounts[9]

GOD_ADDRESS = GOD_ACCOUNT.address


# BFactory
BFactory.deploy requires
- addr
- addr _opfCollector
- addr _preCreatedPool,
- {'from': Account}

From ocean.py

```python
bfactory_address = get_bfactory_address(config.address_file, web3=web3)
bfactory = BFactory(web3, bfactory_address)

pool_address = bfactory.newBPool(from_wallet=alice_wallet)
pool = BPool(web3, pool_address)
assert isinstance(pool, BPool)
```

# [Market workflow](https://github.com/oceanprotocol/ocean.py/blob/v4main/READMEs/marketplace-flow.md)

# test_datatoken
done


# ERC721Factory








