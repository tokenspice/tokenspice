# #
# # Copyright 2021 Ocean Protocol Foundation
# # SPDX-License-Identifier: Apache-2.0
# #
# import logging

# from enforce_typing import enforce_types
# from assets.netlists.oceanv4.web3tools.contract_base import ContractBase
# from assets.netlists.oceanv4.web3tools.wallet import Wallet
# from web3.datastructures import AttributeDict
# from web3.logs import DISCARD


# class DTFactory(ContractBase):
#     CONTRACT_NAME = "DTFactory"
#     FIRST_BLOB = "https://example.com/dataset-1"

#     @enforce_types
#     def verify_data_token(self, dt_address: str) -> bool:
#         """Checks that a token was registered."""
#         log = self.get_token_registered_event(
#             from_block=0, to_block=self.web3.eth.block_number, token_address=dt_address
#         )
#         return bool(log and log.args.tokenAddress == dt_address)

#     @enforce_types
#     def get_token_registered_event(
#         self, from_block: int, to_block: int, token_address: str
#     ) -> [AttributeDict]:
#         """Retrieves event log of token registration."""
#         filter_params = {"tokenAddress": token_address}
#         logs = self.get_event_log(
#             "TokenRegistered",
#             from_block=from_block,
#             to_block=to_block,
#             filters=filter_params,
#         )

#         return logs[0] if logs else None

#     @enforce_types
#     def get_token_minter(self, token_address: str) -> str:
#         """Retrieves token minter.

#         This function will be deprecated in the next major release.
#         It's only kept for backwards compatibility."""
#         from ocean_lib.models.data_token import DataToken  # isort:skip

#         dt = DataToken(self.web3, address=token_address)

#         return dt.contract.caller.minter()

#     @enforce_types
#     def get_token_address(self, transaction_id: str) -> str:
#         """Gets token address using transaction id."""
#         tx_receipt = self.get_tx_receipt(self.web3, transaction_id)
#         if not tx_receipt:
#             logging.warning(
#                 f"Cannot get the transaction receipt for tx {transaction_id}."
#             )
#             return ""
#         logs = self.events.TokenRegistered().processReceipt(tx_receipt, errors=DISCARD)
#         if not logs:
#             logging.warning(f"No logs were found for tx {transaction_id}.")
#             return ""
#         return logs[0].args.tokenAddress

#     # ============================================================
#     # reflect DataToken Solidity methods
#     @enforce_types
#     def createToken(
#         self, blob: str, name: str, symbol: str, cap: int, from_wallet: Wallet
#     ) -> str:
#         return self.send_transaction(
#             "createToken", (blob, name, symbol, cap), from_wallet
#         )

from enforce_typing import enforce_types
import warnings

from assets.netlists.oceanv4.web3tools import web3util, web3wallet

@enforce_types
class DTFactory:
    def __init__(self):
        name = self.__class__.__name__
        abi = web3util.abi(name)
        web3 = web3util.get_web3()
        contract_address = web3util.contractAddress(name)
        self.contract = web3.eth.contract(contract_address, abi=abi)
        
    @property
    def address(self):
        return self.contract.address
        
    #============================================================
    #reflect DTFactory Solidity methods
    def createToken(self, blob:str, name:str, symbol:str, cap_base:int,
                    from_wallet: web3wallet.Web3Wallet) -> str:        
        f = self.contract.functions.createToken(blob, name, symbol, cap_base)
        (tx_hash, tx_receipt) = web3wallet.buildAndSendTx(f, from_wallet)

        warnings.filterwarnings("ignore") #ignore unwarranted warning up next
        # rich_logs = getattr(self.contract.events, 'TokenCreated')().processReceipt(tx_receipt)
        # import ipdb
        # ipdb.set_trace()
        # token_address = rich_logs[0]['args']['newTokenAddress'] 
        token_address = getattr(self.contract.events, 'TokenCreated')().address
        warnings.resetwarnings()

        return token_address

