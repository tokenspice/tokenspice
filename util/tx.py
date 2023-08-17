"""tx utilities"""
import brownie
from brownie.network import chain


def txdict(from_account) -> dict:
    """Return a tx dict that includes priority_fee and max_fee for EIP1559"""
    priority_fee, max_fee = _fees()
    return {
        "from": from_account,
        "priority_fee": priority_fee,
        "max_fee": max_fee,
    }


def transferETH(from_account, to_account, amount):
    """
    Transfer ETH accounting for priority_fee and max_fee, for EIP1559.
    Returns a TransactionReceipt instance.
    """
    priority_fee, max_fee = _fees()
    return from_account.transfer(
        to_account, amount, priority_fee=priority_fee, max_fee=max_fee
    )


def _fees() -> tuple:
    assert brownie.network.is_connected()
    priority_fee = chain.priority_fee
    max_fee = chain.base_fee + 2 * chain.priority_fee
    return (priority_fee, max_fee)
