import brownie

import sol057.contracts.oceanv3.oceanv3util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT057

account0 = brownie.network.accounts[0]
address0 = account0.address


def test_direct():
    tt = BROWNIE_PROJECT057.DataTokenTemplate.deploy(
        "TT",
        "TemplateToken",
        address0,
        toBase18(1e3),
        "blob",
        address0,
        {"from": account0},
    )

    dtfactory = BROWNIE_PROJECT057.DTFactory.deploy(
        tt.address, account0.address, {"from": account0}
    )

    tx = dtfactory.createToken(
        "foo_blob", "DT", "DT", toBase18(100.0), {"from": account0}
    )
    dt_address = tx.events["TokenCreated"]["newTokenAddress"]

    dt = BROWNIE_PROJECT057.DataTokenTemplate.at(dt_address)
    assert dt.address == dt_address
    assert dt.blob() == "foo_blob"


def test_via_DTFactory_util():
    dtfactory = sol057.contracts.oceanv3.oceanv3util.DTFactory()
    tx = dtfactory.createToken(
        "foo_blob", "datatoken1", "DT1", toBase18(100.0), {"from": account0}
    )

    dt_address = sol057.contracts.oceanv3.oceanv3util.dtAddressFromCreateTokenTx(tx)
    assert dt_address == tx.events["TokenCreated"]["newTokenAddress"]

    dt = BROWNIE_PROJECT057.DataTokenTemplate.at(dt_address)
    assert dt.address == dt_address
    assert dt.blob() == "foo_blob"
    assert dt.name() == "datatoken1"
    assert dt.symbol() == "DT1"


def test_via_newDatatoken_util():
    dt = sol057.contracts.oceanv3.oceanv3util.newDatatoken(
        "foo_blob", "datatoken1", "DT1", toBase18(100.0), account0
    )
    assert dt.blob() == "foo_blob"
    assert dt.name() == "datatoken1"
    assert dt.symbol() == "DT1"
