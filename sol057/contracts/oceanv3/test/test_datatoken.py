import brownie

import sol057.contracts.oceanv3.oceanv3util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT057

accounts = brownie.network.accounts
account0, account1 = accounts[0], accounts[1]
address0, address1 = account0.address, account1.address


def test_direct():
    dtfactory = sol057.contracts.oceanv3.oceanv3util.DTFactory()

    tx = dtfactory.createToken(
        "foo_blob", "datatoken1", "DT1", toBase18(100.0), {"from": account0}
    )
    dt_address = tx.events["TokenCreated"]["newTokenAddress"]
    dt = BROWNIE_PROJECT057.DataTokenTemplate.at(dt_address)
    dt.mint(address0, toBase18(100.0), {"from": account0})

    # functionality inherited from btoken
    assert dt.address == dt_address
    assert dt.name() == "datatoken1"
    assert dt.symbol() == "DT1"
    assert dt.decimals() == 18
    assert dt.balanceOf(address0) == toBase18(100.0)
    dt.transfer(address1, toBase18(50.0), {"from": account0})
    assert dt.allowance(address0, address1) == 0
    dt.approve(address1, toBase18(1.0), {"from": account0})
    assert dt.allowance(address0, address1) == toBase18(1.0)

    # functionality for just datatoken
    assert dt.blob() == "foo_blob"


def test_via_util():
    dt = sol057.contracts.oceanv3.oceanv3util.newDatatoken(
        "foo_blob", "datatoken1", "DT1", toBase18(100.0), account0
    )
    dt.mint(address0, toBase18(100.0), {"from": account0})
    assert dt.name() == "datatoken1"
    assert dt.symbol() == "DT1"
    assert dt.decimals() == 18
    assert dt.balanceOf(address0) == toBase18(100.0)
    assert dt.blob() == "foo_blob"
