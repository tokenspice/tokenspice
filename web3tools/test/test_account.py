from web3tools import account

def test_Account():
    private_key_str = '0x9c75ed156c45b5a365bde30dc8871e9c6d2b5dc08a7b47572e0354afb859cb15'
    
    account1 = account.Account(private_key=private_key_str)
    account2 = account.Account(private_key=private_key_str)

    assert account1.private_key == account2.private_key
    assert account1.address == account2.address
    assert account1.keysStr() == account2.keysStr()
    

def test_randomPrivateKey():
    private_key1 = account.randomPrivateKey()
    assert len(private_key1) == 32
                      
    private_key2 = account.randomPrivateKey()
    assert len(private_key2) == 32
    
    assert private_key1 != private_key2

def test_privateKeyToAddress():
    private_key1 = account.randomPrivateKey()
    
    address1 = account.Account(private_key=private_key1).address
    address2 = account.privateKeyToAddress(private_key1)
    
    assert address1 == address2
