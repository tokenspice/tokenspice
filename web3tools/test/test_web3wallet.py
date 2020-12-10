import web3
from web3tools import web3util, web3wallet

def test_randomWeb3Wallet():
    wallet1 = web3wallet.randomWeb3Wallet()
    wallet2 = web3wallet.randomWeb3Wallet()
    assert wallet1.address != wallet2.address
    assert wallet1.private_key != wallet2.private_key

def test_Web3Wallet():
    private_key_str = '0x9c75ed156c45b5a365bde30dc8871e9c6d2b5dc08a7b47572e0354afb859cb15'
    wallet1 = web3wallet.Web3Wallet(private_key=private_key_str)
    
    wallet2 = web3wallet.Web3Wallet(private_key=private_key_str)
    
    assert wallet1.address == wallet2.address
    assert wallet1.private_key == wallet2.private_key
    assert wallet1.account.private_key == wallet2.account.private_key

def test_ETHbalance1():
    _web3 = web3util.get_web3()
    network = web3util.get_network()
    
    private_key = web3util.confFileValue(network, 'TEST_PRIVATE_KEY1')
    wallet = web3wallet.Web3Wallet(private_key)
    assert wallet.ETH_base() > 1.0 #should have got ETH from ganache startup
    assert wallet.ETH_base() == _web3.eth.getBalance(wallet.address)
    
def test_ETHbalance2():
    _web3 = web3util.get_web3()
    
    wallet = web3wallet.randomWeb3Wallet() #should have 0 ETH
    assert wallet.ETH_base() == _web3.eth.getBalance(wallet.address)

def testSendEth():
    _web3 = web3util.get_web3()
    network = web3util.get_network()

    #wallet1 should have got ETH from ganache startup (see deploy.py)
    private_key1 = web3util.confFileValue(network, 'TEST_PRIVATE_KEY1')
    wallet1 = web3wallet.Web3Wallet(private_key1)
    orig_bal1_base = wallet1.ETH_base()
    print("orig bal1 = %s" % web3util.fromBase18(orig_bal1_base))
    assert orig_bal1_base > web3util.toBase18(1.0)

    #wallet2 should have 0 ETH
    wallet2 = web3wallet.randomWeb3Wallet()
    orig_bal2_base = wallet2.ETH_base()
    print("orig bal2 = %s" % web3util.fromBase18(orig_bal2_base))
    assert orig_bal2_base == 0

    #wallet1 gives wallet2 1.0 ETH
    sent_base = web3util.toBase18(1.0)
    wallet1.sendEth(wallet2.address, sent_base)
    
    new_bal1_base = wallet1.ETH_base()
    new_bal2_base = wallet2.ETH_base()
    print("new bal1 = %s" % web3util.fromBase18(new_bal1_base))
    print("new bal2 = %s" % web3util.fromBase18(new_bal2_base))
    assert new_bal2_base == sent_base
    assert (orig_bal1_base - sent_base*1.1) < new_bal1_base < (orig_bal1_base - sent_base)
    


#=======================================================================
#tests still missing:
# _get_nonce()
# sign_tx()
# sign()
# buildAndSendTx()

