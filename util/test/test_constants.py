import brownie

# running this includes:
#   brownie.network.connect("development")
from util.constants import *

def test_network_connected():
    assert brownie.network.is_connected()

def test_have_accounts():
    # by default, brownie should have 10 accounts
    assert brownie.network.accounts
