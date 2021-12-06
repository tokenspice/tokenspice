import brownie

# import sol080.contracts.oceanv4.oceanv4util
from util.base18 import toBase18
from util.constants import BROWNIE_PROJECT080, GOD_ACCOUNT, OPF_ACCOUNT
# from util.globaltokens import OCEAN_address

account0 = brownie.network.accounts[0]
address0 = account0.address

OPF_ADDRESS = OPF_ACCOUNT.address

accounts = brownie.network.accounts

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
