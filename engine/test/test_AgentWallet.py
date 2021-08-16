from enforce_typing import enforce_types
import pytest

from engine.AgentWallet import *
from engine.test.conftest import _DT_INIT, _DT_STAKE 
from web3engine import bfactory, bpool, datatoken

#=======================================================================
#__init__ related
@enforce_types
def test_initFromPrivateKey():
    private_key = '0xbbfbee4961061d506ffbb11dfea64eba16355cbf1d9c29613126ba7fec0aed5d'
    address = '0x66aB6D9362d4F35596279692F0251Db635165871'
    
    w = AgentWallet(private_key=private_key)
    assert w._address == address
    assert w._web3wallet.address == address
    assert w._web3wallet.private_key == private_key

@enforce_types
def test_initRandomPrivateKey():
    w1 = AgentWallet()
    w2 = AgentWallet()
    assert w1._address != w2._address
    assert w1._web3wallet.private_key != w2._web3wallet.private_key

@enforce_types
def test_gotSomeETHforGas():
    w = AgentWallet()
    assert w.ETH() > 0.0    

@enforce_types
def testInitiallyEmpty():
    w = AgentWallet()

    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0

@enforce_types
def testInitiallyFilled():
    w = AgentWallet(USD=1.2, OCEAN=3.4)

    assert w.USD() == 1.2
    assert w.OCEAN() == 3.4

#=======================================================================
#USD-related
@enforce_types
def testUSD():
    w = AgentWallet()

    w.depositUSD(13.25)
    assert w.USD() == 13.25

    w.depositUSD(1.00)
    assert w.USD() == 14.25

    w.withdrawUSD(2.10)
    assert w.USD() == 12.15

    w.depositUSD(0.0)
    w.withdrawUSD(0.0)
    assert w.USD() == 12.15

    assert w.totalUSDin() == (13.25+1.0)

    with pytest.raises(AssertionError):
        w.depositUSD(-5.0)

    with pytest.raises(AssertionError):
        w.withdrawUSD(-5.0)

    with pytest.raises(ValueError):
        w.withdrawUSD(1000.0)

@enforce_types
def testFloatingPointRoundoff_USD():
    w = AgentWallet(USD=2.4)
    w.withdrawUSD(2.4000000000000004) #should not get ValueError
    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0

@enforce_types
def test_transferUSD():
    w1 = AgentWallet(USD=10.0)
    w2 = AgentWallet(USD=1.0)

    w1.transferUSD(w2, 2.0)

    assert w1.USD() == 10.0-2.0
    assert w2.USD() == 1.0+2.0
    
#=======================================================================
#OCEAN-related
@enforce_types
def testOCEAN():
    w = AgentWallet()

    w.depositOCEAN(13.25)
    assert w.OCEAN() == 13.25

    w.depositOCEAN(1.00)
    assert w.OCEAN() == 14.25

    w.withdrawOCEAN(2.10)
    assert w.OCEAN() == 12.15

    w.depositOCEAN(0.0)
    w.withdrawOCEAN(0.0)
    assert w.OCEAN() == 12.15

    assert w.totalOCEANin() == (13.25+1.0)

    with pytest.raises(AssertionError):
        w.depositOCEAN(-5.0)

    with pytest.raises(AssertionError):
        w.withdrawOCEAN(-5.0)

    with pytest.raises(ValueError):
        w.withdrawOCEAN(1000.0)
        
@enforce_types
def testFloatingPointRoundoff_OCEAN():
    w = AgentWallet(OCEAN=2.4)
    w.withdrawOCEAN(2.4000000000000004) #should not get ValueError
    assert w.USD() == 0.0
    assert w.OCEAN() == 0.0

@enforce_types
def test_transferOCEAN():
    w1 = AgentWallet(OCEAN=10.0)
    w2 = AgentWallet(OCEAN=1.0)

    w1.transferOCEAN(w2, 2.0)

    assert w1.OCEAN() == (10.0-2.0)
    assert w2.OCEAN() == (1.0+2.0)
    
#===================================================================
#ETH-related
@enforce_types
def testETH1():
    #super-basic test for ETH
    w = AgentWallet()
    assert isinstance(w.ETH(), float)
    
@enforce_types
def testETH2():
    #TEST_PRIVATE_KEY1 should get initialized with ETH when ganache starts
    network = web3util.get_network()
    private_key = web3util.confFileValue(network, 'TEST_PRIVATE_KEY1')
    w = AgentWallet(private_key=private_key)
    assert w.ETH() > 1.0

#===================================================================
#datatoken and pool-related
@enforce_types
def test_DT(alice_info):
    alice_DT_amt:float = alice_info.agent_wallet.DT(alice_info.DT)
    assert alice_DT_amt == (_DT_INIT - _DT_STAKE)

@enforce_types
def test_BPT(alice_info):
    assert alice_info.agent_wallet.BPT(alice_info.pool) == 100.0

@enforce_types
def test_poolToDTaddress(alice_info):
    alice_DT, alice_pool = alice_info.DT, alice_info.pool
    assert _poolToDTaddress(alice_pool) == alice_DT.address

@enforce_types
def test_sellDT(alice_info):
    alice_agent_wallet, alice_DT, alice_pool = \
        alice_info.agent_wallet, alice_info.DT, alice_info.pool
    assert _poolToDTaddress(alice_pool) == alice_DT.address
    
    DT_before:float = alice_agent_wallet.DT(alice_DT)
    OCEAN_before:float = alice_agent_wallet.OCEAN()

    DT_sell_amt = 10.0
    alice_agent_wallet.sellDT(alice_pool, alice_DT, DT_sell_amt=DT_sell_amt)
    
    DT_after:float = alice_agent_wallet.DT(alice_DT)
    OCEAN_after:float = alice_agent_wallet.OCEAN()
        
    assert OCEAN_after > OCEAN_before
    assert DT_after == (DT_before - DT_sell_amt)

@enforce_types
def test_buyDT(alice_info):
    alice_agent_wallet, alice_DT, alice_pool = \
        alice_info.agent_wallet, alice_info.DT, alice_info.pool
    assert _poolToDTaddress(alice_pool) == alice_DT.address
    
    DT_before:float = alice_agent_wallet.DT(alice_DT)
    OCEAN_before:float = alice_agent_wallet.OCEAN()

    DT_buy_amt = 1.0
    alice_agent_wallet.buyDT(alice_pool, alice_DT, DT_buy_amt=DT_buy_amt, max_OCEAN_allow=OCEAN_before)
    
    DT_after:float = alice_agent_wallet.DT(alice_DT)
    OCEAN_after:float = alice_agent_wallet.OCEAN()
        
    assert OCEAN_after < OCEAN_before
    assert DT_after == (DT_before + DT_buy_amt)    

@enforce_types
def test_stakeOCEAN(alice_info):
    alice_agent_wallet, alice_pool = alice_info.agent_wallet, alice_info.pool
    
    BPT_before:float = alice_agent_wallet.BPT(alice_pool)
    OCEAN_before:float = alice_agent_wallet.OCEAN()
    
    alice_agent_wallet.stakeOCEAN(OCEAN_stake=20.0, pool=alice_pool)
    
    OCEAN_after:float = alice_agent_wallet.OCEAN()
    BPT_after:float = alice_agent_wallet.BPT(alice_pool)
    assert OCEAN_after == (OCEAN_before - 20.0)
    assert BPT_after > BPT_before

@enforce_types
def test_unstakeOCEAN(alice_info):
    alice_agent_wallet, alice_pool = alice_info.agent_wallet, alice_info.pool
    
    BPT_before:float = alice_agent_wallet.BPT(alice_pool)
    
    alice_agent_wallet.unstakeOCEAN(BPT_unstake=20.0, pool=alice_pool)
    
    BPT_after:float = alice_agent_wallet.BPT(alice_pool)
    assert BPT_after == (BPT_before - 20.0)

    
#===================================================================
#str-related
@enforce_types
def testStr():
    w = AgentWallet()        
    assert "AgentWallet" in str(w)

#===================================================================
#burn-related
@enforce_types
def testBurnWallet():
    w = BurnWallet()
    assert w._address == constants.BURN_ADDRESS


    
#===================================================================
#helps testing


def _poolToDTaddress(pool:bpool.BPool) -> str:
    """Return the address of the datatoken of this pool.
    Don't make this public because it has strong assumptions:
    assumes 2 tokens; assumes one token is OCEAN; assumes other is DT
    """
    cur_addrs = pool.getCurrentTokens()
    assert len(cur_addrs) == 2, "this method currently assumes 2 tokens"
    OCEAN_addr = globaltokens.OCEAN_address()
    assert OCEAN_addr in cur_addrs, "this method expects one token is OCEAN"
    DT_addr = [addr for addr in cur_addrs if addr != OCEAN_addr][0]
    return DT_addr
