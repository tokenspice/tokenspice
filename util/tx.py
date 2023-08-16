"""tx utilities"""
import brownie
from brownie.network import chain

def txdict(from_account) -> dict:
    assert brownie.network.is_connected()
    
    # need to specify priority_fee and max_fee because EIP1559
    priority_fee = chain.priority_fee
    max_fee = chain.base_fee + 2 * chain.priority_fee
    return {
        "priority_fee": priority_fee,
        "max_fee": max_fee,
        "from": from_account,
    }
