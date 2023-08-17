import brownie

from util.tx import txdict


def test_txdict():
    if not brownie.network.is_connected():
        brownie.network.connect("development")

    from_account = "foo_account"
    d = txdict(from_account)
    assert set(d.keys()) == set(["priority_fee", "max_fee", "from"])
    assert d["from"] == from_account
