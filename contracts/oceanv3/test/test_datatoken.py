import brownie

import contracts.oceanv3.util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT

accounts = brownie.network.accounts
address0, address1 = accounts[0].address, accounts[1].address

def test_direct():
    dtfactory = contracts.oceanv3.util.DTFactory()
    
    tx = dtfactory.createToken(
        'foo_blob', 'datatoken1', 'DT1', toBase18(100.0),
        {'from': accounts[0]})
    dt_address = tx.events['TokenCreated']['newTokenAddress']
    dt = BROWNIE_PROJECT.DataTokenTemplate.at(dt_address)
    dt.mint(address0, toBase18(100.0), {'from':accounts[0]})

    #functionality inherited from btoken
    assert dt.address == dt_address
    assert dt.name() == 'datatoken1'
    assert dt.symbol() == 'DT1'
    assert dt.decimals() == 18
    assert dt.balanceOf(address0) == toBase18(100.0)
    dt.transfer(address1, toBase18(50.0), {'from': accounts[0]})
    assert dt.allowance(address0, address1) == 0
    dt.approve(address1, toBase18(1.0), {'from': accounts[0]})
    assert dt.allowance(address0, address1) == toBase18(1.0)
    
    #functionality for just datatoken
    assert dt.blob() == 'foo_blob'

def test_via_util():
    dt = contracts.oceanv3.util.newDatatoken(
        'foo_blob', 'datatoken1', 'DT1', toBase18(100.0), accounts[0])
    dt.mint(address0, toBase18(100.0), {'from':accounts[0]})
    assert dt.name() == 'datatoken1'
    assert dt.symbol() == 'DT1'
    assert dt.decimals() == 18
    assert dt.balanceOf(address0) == toBase18(100.0)
    assert dt.blob() == 'foo_blob'
    
