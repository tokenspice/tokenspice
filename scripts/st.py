import os

def main():
    alice_private_key = os.getenv('OCEAN_PRIVATE_KEY1')
    bob_private_key = os.getenv('OCEAN_PRIVATE_KEY2')
    
    #Alice publishes a dataset (= publishes a datatoken contract)
    import Ocean
    config = {
        'network' : 'development', #see 'brownie network lists'
        'privateKey' : alice_private_key,
    }
    ocean = Ocean.Ocean(config)
    alice_account = ocean.accountFromKey(alice_private_key)
    token = ocean.createSimpletoken()
    dt_address = token.address
    print(dt_address)

    #Alice transfers 1 token to Bob
    bob_account = ocean.accountFromKey(bob_private_key)
    token.transfer(bob_account.address, 1)

if __name__ == '__main__':
    main()
    
