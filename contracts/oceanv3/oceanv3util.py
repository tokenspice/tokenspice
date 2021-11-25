import brownie
from enforce_typing import enforce_types

from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT
    
accounts = brownie.network.accounts
address0 = accounts[0].address

#===============================================================
#datatokens: template, factory, creation
@enforce_types
def templateDatatoken():
    return BROWNIE_PROJECT.DataTokenTemplate.deploy(
        "TT", "TemplateToken", address0, toBase18(1e3), "blob", address0,
        {'from' : accounts[0]})

_DTFACTORY = None
@enforce_types
def DTFactory():
    global _DTFACTORY
    if _DTFACTORY is None: 
        dt = templateDatatoken()
        _DTFACTORY = BROWNIE_PROJECT.DTFactory.deploy(
            dt.address, address0,
            {'from' : accounts[0]})
    return _DTFACTORY

@enforce_types
def dtAddressFromCreateTokenTx(tx):
    return tx.events['TokenCreated']['newTokenAddress']

@enforce_types
def newDatatoken(blob:str, name:str, symbol:str, cap:int, account):
    f = DTFactory()
    tx = f.createToken(blob, name, symbol, cap, {'from': account})
    dt_address = dtAddressFromCreateTokenTx(tx)
    dt = BROWNIE_PROJECT.DataTokenTemplate.at(dt_address)
    return dt

#===============================================================
#pools: template, factory, creation
@enforce_types
def templatePool():
    return BROWNIE_PROJECT.BPool.deploy({'from' : accounts[0]})

_BFACTORY = None
@enforce_types
def BFactory():
    global _BFACTORY
    if _BFACTORY is None: 
        pool = templatePool()
        _BFACTORY = BROWNIE_PROJECT.BFactory.deploy(
            pool.address, 
            {'from' : accounts[0]})
    return _BFACTORY

@enforce_types
def poolAddressFromNewBPoolTx(tx):
    return tx.events['BPoolCreated']['newBPoolAddress']

@enforce_types
def newBPool(account):
    bfactory = BFactory()
    tx = bfactory.newBPool({'from': account})
    pool_address = poolAddressFromNewBPoolTx(tx)
    pool = BROWNIE_PROJECT.BPool.at(pool_address)
    return pool
