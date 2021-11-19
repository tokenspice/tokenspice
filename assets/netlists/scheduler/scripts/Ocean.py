import brownie
import eth_account 
import eth_keys
import eth_utils

class Ocean:
    def __init__(self, config):
        network  = config['network']
        brownie.network.connect(network)

        private_key = config['privateKey']
        self.account = self.accountFromKey(private_key)

    def __del__(self):
        """Need to shut down the connection on destruct, otherwise errors"""
        if brownie is not None and brownie.network.is_connected():
            brownie.network.disconnect()

    def accountFromKey(self, private_key):
        return brownie.network.accounts.add(private_key=private_key)
        
    def createDatatoken(self, blob):
        """@return -- brownie-style datatoken contract"""
        try:
            project = brownie.project.load('.', name="MyProject") #for brownie project dir
        except brownie.exceptions.ProjectNotFound:
            project = brownie.project.load('./assets/netlists/scheduler', name="MyProject") #for tsp dir
        return project.Datatoken.deploy(
                "TST", "Test Token", blob, 18, 1e24,{'from' : self.account})
            
        return returnval
                
def privateKeyToAccount(private_key):
    return eth_account.Account().privateKeyToAccount(private_key)

def printAccountInfo(web3, account_descr_s, private_key):
    print(f"Account {account_descr_s}:")
    print(f"  private key: {private_key}")

    private_key_bytes = eth_utils.decode_hex(private_key)
    private_key_object = eth_keys.keys.PrivateKey(private_key_bytes)
    public_key = private_key_object.public_key
    print(f"  public key: {public_key}")
    
    account = eth_account.Account().privateKeyToAccount(private_key)
    print(f"  address: {account.address}")
    
    balance_wei = web3.eth.getBalance(account.address)
    balance_eth = web3.fromWei(balance_wei, 'ether')
    print(f"  balance: {balance_wei} Wei ({balance_eth} Ether)")

def printAccountsInfo(web3, private_keys):
    for i, private_key in enumerate(private_keys):
        account_descr_s = str(i+1)
        printAccountInfo(web3, account_descr_s, private_key)

def chooseGasPrice(network):
    if network == 'rinkeby':
        return int(1e9)
    elif network == 'mainnet':
        return int(9e9)
    else:
        raise ValueError(f"can't handle gas price for network '{network}'")
