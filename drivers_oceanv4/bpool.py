#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import typing
from typing import Optional, Tuple

from enforce_typing import enforce_types
from eth_utils import remove_0x_prefix
from drivers_oceanv4 import balancer_constants
from drivers_oceanv4.btoken import BToken
from drivers_oceanv4.currency import from_wei
from drivers_oceanv4.wallet import Wallet
from web3.datastructures import AttributeDict
from web3.main import Web3

logger = logging.getLogger(__name__)


class BPool(BToken):
    CONTRACT_NAME = "BPool"

    @enforce_types
    def __str__(self) -> str:
        """Formats with attributes as key, value pairs."""
        s = []
        s += ["BPool:"]
        s += [f"  pool_address={self.address}"]
        s += [f"  controller address = {self.getController()}"]
        s += [f"  isPublicSwap = {self.isPublicSwap()}"]
        s += [f"  isFinalized = {self.isFinalized()}"]

        swap_fee = from_wei(self.getSwapFee())
        s += ["  swapFee = %.2f%%" % (swap_fee * 100)]

        s += [f"  numTokens = {self.getNumTokens()}"]
        cur_addrs = self.getCurrentTokens()
        cur_symbols = [BToken(self.web3, addr).symbol() for addr in cur_addrs]
        s += [f"  currentTokens (as symbols) = {', '.join(cur_symbols)}"]

        if self.isFinalized():
            final_addrs = self.getFinalTokens()
            final_symbols = [BToken(self.web3, addr).symbol() for addr in final_addrs]
            s += [f"  finalTokens (as symbols) = {final_symbols}"]

        s += ["  is bound:"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            s += [f"    {symbol}: {self.isBound(addr)}"]

        s += ["  weights (fromBase):"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            denorm_w = from_wei(self.getDenormalizedWeight(addr))
            norm_w = from_wei(self.getNormalizedWeight(addr))
            s += [f"    {symbol}: denorm_w={denorm_w}, norm_w={norm_w} "]

        total_denorm_w = from_wei(self.getTotalDenormalizedWeight())
        s += [f"    total_denorm_w={total_denorm_w}"]

        s += ["  balances (fromBase):"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            balance = self.getBalance(addr)
            dec = BToken(self.web3, addr).decimals()
            s += [f"    {symbol}: {from_wei(balance, dec)}"]

        return "\n".join(s)

    @enforce_types
    def setup(
        self,
        data_token: str,
        data_token_amount: int,
        data_token_weight: int,
        base_token: str,
        base_token_amount: int,
        base_token_weight: int,
        swap_fee: int,
        from_wallet: Wallet,
    ) -> str:

        tx_id = self.send_transaction(
            "setup",
            (
                data_token,
                data_token_amount,
                data_token_weight,
                base_token,
                base_token_amount,
                base_token_weight,
                swap_fee,
            ),
            from_wallet,
            {"gas": balancer_constants.GASLIMIT_BFACTORY_NEWBPOOL},
        )

        return tx_id

    # ============================================================
    # reflect BPool Solidity methods: everything at Balancer Interfaces "BPool"
    # docstrings are adapted from Balancer API
    # https://docs.balancer.finance/smart-contracts/api

    # ==== View Functions
    @enforce_types
    def isPublicSwap(self) -> bool:
        return self.contract.caller.isPublicSwap()

    @enforce_types
    def isFinalized(self) -> bool:
        """Returns true if state is finalized.

        The `finalized` state lets users know that the weights, balances, and
        fees of this pool are immutable. In the `finalized` state, `SWAP`,
        `JOIN`, and `EXIT` are public. `CONTROL` capabilities are disabled.
        (https://docs.balancer.finance/smart-contracts/api#access-control)
        """
        return self.contract.caller.isFinalized()

    @enforce_types
    def isBound(self, token_address: str) -> bool:
        """Returns True if the token is bound.

        A bound token has a valid balance and weight. A token cannot be bound
        without valid parameters which will enable e.g. `getSpotPrice` in terms
        of other tokens. However, disabling `isSwapPublic` will disable any
        interaction with this token in practice (assuming there are no existing
        tokens in the pool, which can always `exitPool`).
        """
        return self.contract.caller.isBound(token_address)

    @enforce_types
    def getNumTokens(self) -> int:
        """
        How many tokens are bound to this pool.
        """
        return self.contract.caller.getNumTokens()

    @enforce_types
    def getCurrentTokens(self) -> typing.List[str]:
        """@return -- list of [token_addr:str]"""
        return self.contract.caller.getCurrentTokens()

    @enforce_types
    def getFinalTokens(self) -> typing.List[str]:
        """@return -- list of [token_addr:str]"""
        return self.contract.caller.getFinalTokens()

    @enforce_types
    def getDenormalizedWeight(self, token_address: str) -> int:
        return self.contract.caller.getDenormalizedWeight(token_address)

    @enforce_types
    def getTotalDenormalizedWeight(self) -> int:
        return self.contract.caller.getTotalDenormalizedWeight()

    @enforce_types
    def getNormalizedWeight(self, token_address: str) -> int:
        """
        The normalized weight of a token. The combined normalized weights of
        all tokens will sum up to 1. (Note: the actual sum may be 1 plus or
        minus a few wei due to division precision loss)
        """
        return self.contract.caller.getNormalizedWeight(token_address)

    @enforce_types
    def getBalance(self, token_address: str) -> int:
        return self.contract.caller.getBalance(token_address)

    @enforce_types
    def getSwapFee(self) -> int:
        return self.contract.caller.getSwapFee()

    @enforce_types
    def getController(self) -> str:
        """
        Get the "controller" address, which can call `CONTROL` functions like
        `rebind`, `setSwapFee`, or `finalize`.
        """
        return self.contract.caller.getController()

    # ==== Controller Functions

    @enforce_types
    def setSwapFee(self, swapFee: int, from_wallet: Wallet) -> str:
        """
        Caller must be controller. Pool must NOT be finalized.
        """
        return self.send_transaction("setSwapFee", (swapFee,), from_wallet)

    @enforce_types
    def setController(self, manager_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("setController", (manager_address,), from_wallet)

    @enforce_types
    def setPublicSwap(self, public: bool, from_wallet: Wallet) -> str:
        """
        Makes `isPublicSwap` return `_publicSwap`. Requires caller to be
        controller and pool not to be finalized. Finalized pools always have
        public swap.
        """
        return self.send_transaction("setPublicSwap", (public,), from_wallet)

    @enforce_types
    def finalize(self, from_wallet: Wallet) -> str:
        """
        This makes the pool **finalized**. This is a one-way transition. `bind`,
        `rebind`, `unbind`, `setSwapFee` and `setPublicSwap` will all throw
        `ERR_IS_FINALIZED` after pool is finalized. This also switches
        `isSwapPublic` to true.
        """
        return self.send_transaction("finalize", (), from_wallet)

    @enforce_types
    def bind(
        self, token_address: str, balance: int, weight: int, from_wallet: Wallet
    ) -> str:
        """
        Binds the token with address `token`. Tokens will be pushed/pulled from
        caller to adjust match new balance. Token must not already be bound.
        `balance` must be a valid balance and denorm must be a valid denormalized
        weight. `bind` creates the token record and then calls `rebind` for
        updating pool weights and token transfers.

        Possible errors:
        -`ERR_NOT_CONTROLLER` -- caller is not the controller
        -`ERR_IS_BOUND` -- T is already bound
        -`ERR_IS_FINALIZED` -- isFinalized() is true
        -`ERR_ERC20_FALSE` -- ERC20 token returned false
        -`ERR_MAX_TOKENS` -- Only 8 tokens are allowed per pool
        -unspecified error thrown by token
        """
        return self.send_transaction(
            "bind", (token_address, balance, weight), from_wallet
        )

    @enforce_types
    def rebind(
        self, token_address: str, balance: int, weight: int, from_wallet: Wallet
    ) -> str:
        """
        Changes the parameters of an already-bound token. Performs the same
        validation on the parameters.
        """
        return self.send_transaction(
            "rebind", (token_address, balance, weight), from_wallet
        )

    @enforce_types
    def unbind(self, token_address: str, from_wallet: Wallet) -> str:
        """
        Unbinds a token, clearing all of its parameters. Exit fee is charged
        and the remaining balance is sent to caller.
        """
        return self.send_transaction("unbind", (token_address,), from_wallet)

    @enforce_types
    def gulp(self, token_address: str, from_wallet: Wallet) -> str:
        """
        This syncs the internal `balance` of `token` within a pool with the
        actual `balance` registered on the ERC20 contract. This is useful to
        wallet for airdropped tokens or any tokens sent to the pool without
        using the `join` or `joinSwap` methods.

        As an example, pools that contain `COMP` tokens can have the `COMP`
        balance updated with the rewards sent by Compound (https://etherscan.io/tx/0xeccd42bf2b8a180a561c026717707d9024a083059af2f22c197ee511d1010e23).
        In order for any airdrop balance to be gulped, the token must be bound
        to the pool. So if a shared pool (which is immutable) does not have a
        given token, any airdrops in that token will be locked in the pool
        forever.
        """
        return self.send_transaction("gulp", (token_address,), from_wallet)

    # ==== Price Functions

    @enforce_types
    def getSpotPrice(self, tokenIn_address: str, tokenOut_address: str) -> int:
        return self.contract.caller.getSpotPrice(tokenIn_address, tokenOut_address)

    @enforce_types
    def getSpotPriceSansFee(self, tokenIn_address: str, tokenOut_address: str) -> int:
        return self.contract.caller.getSpotPriceSansFee(
            tokenIn_address, tokenOut_address
        )

    # ==== Trading and Liquidity Functions

    @enforce_types
    def joinPool(
        self, poolAmountOut: int, maxAmountsIn: typing.List[int], from_wallet: Wallet
    ) -> str:
        """
        Join the pool, getting `poolAmountOut` pool tokens. This will pull some
        of each of the currently trading tokens in the pool, meaning you must
        have called `approve` for each token for this pool. These values are
        limited by the array of `maxAmountsIn` in the order of the pool tokens.
        """
        return self.send_transaction(
            "joinPool", (poolAmountOut, maxAmountsIn), from_wallet
        )

    @enforce_types
    def exitPool(
        self, poolAmountIn: int, minAmountsOut: typing.List[int], from_wallet: Wallet
    ) -> str:
        """
        Exit the pool, paying `poolAmountIn` pool tokens and getting some of
        each of the currently trading tokens in return. These values are
        limited by the array of `minAmountsOut` in the order of the pool tokens.
        """
        return self.send_transaction(
            "exitPool", (poolAmountIn, minAmountsOut), from_wallet
        )

    @enforce_types
    def swapExactAmountIn(
        self,
        tokenIn_address: str,
        tokenAmountIn: int,
        tokenOut_address: str,
        minAmountOut: int,
        maxPrice: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Trades an exact `tokenAmountIn` of `tokenIn` taken from the caller by
        the pool, in exchange for at least `minAmountOut` of `tokenOut` given
        to the caller from the pool, with a maximum marginal price of
        `maxPrice`.

        Returns `(tokenAmountOut`, `spotPriceAfter)`, where `tokenAmountOut`
        is the amount of token that came out of the pool, and `spotPriceAfter`
        is the new marginal spot price, ie, the result of `getSpotPrice` after
        the call. (These values are what are limited by the arguments; you are
        guaranteed `tokenAmountOut >= minAmountOut` and
        `spotPriceAfter <= maxPrice)`.
        """
        return self.send_transaction(
            "swapExactAmountIn",
            (tokenIn_address, tokenAmountIn, tokenOut_address, minAmountOut, maxPrice),
            from_wallet,
        )

    @enforce_types
    def swapExactAmountOut(
        self,
        tokenIn_address: str,
        maxAmountIn: int,
        tokenOut_address: str,
        tokenAmountOut: int,
        maxPrice: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "swapExactAmountOut",
            (tokenIn_address, maxAmountIn, tokenOut_address, tokenAmountOut, maxPrice),
            from_wallet,
        )

    @enforce_types
    def joinswapExternAmountIn(
        self,
        tokenIn_address: str,
        tokenAmountIn: int,
        minPoolAmountOut: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Pay `tokenAmountIn` of token `tokenIn` to join the pool, getting
        `poolAmountOut` of the pool shares.
        """
        return self.send_transaction(
            "joinswapExternAmountIn",
            (tokenIn_address, tokenAmountIn, minPoolAmountOut),
            from_wallet,
        )

    @enforce_types
    def joinswapPoolAmountOut(
        self,
        tokenIn_address: str,
        poolAmountOut: int,
        maxAmountIn: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Specify `poolAmountOut` pool shares that you want to get, and a token
        `tokenIn` to pay with. This costs `maxAmountIn` tokens (these went
        into the pool).
        """
        return self.send_transaction(
            "joinswapPoolAmountOut",
            (tokenIn_address, poolAmountOut, maxAmountIn),
            from_wallet,
        )

    @enforce_types
    def exitswapPoolAmountIn(
        self,
        tokenOut_address: str,
        poolAmountIn: int,
        minAmountOut: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Pay `poolAmountIn` pool shares into the pool, getting `tokenAmountOut`
        of the given token `tokenOut` out of the pool.
        """
        return self.send_transaction(
            "exitswapPoolAmountIn",
            (tokenOut_address, poolAmountIn, minAmountOut),
            from_wallet,
        )

    @enforce_types
    def exitswapExternAmountOut(
        self,
        tokenOut_address: str,
        tokenAmountOut: int,
        maxPoolAmountIn: int,
        from_wallet: Wallet,
    ) -> str:
        """
        Specify `tokenAmountOut` of token `tokenOut` that you want to get out
        of the pool. This costs `poolAmountIn` pool shares (these went into
        the pool).
        """
        return self.send_transaction(
            "exitswapExternAmountOut",
            (tokenOut_address, tokenAmountOut, maxPoolAmountIn),
            from_wallet,
        )

    # ==== Balancer Pool as ERC20
    @enforce_types
    def totalSupply(self) -> int:
        return self.contract.caller.totalSupply()

    @enforce_types
    def balanceOf(self, whom_address: str) -> int:
        return self.contract.caller.balanceOf(whom_address)

    @enforce_types
    def allowance(self, src_address: str, dst_address: str) -> int:
        return self.contract.caller.allowance(src_address, dst_address)

    @enforce_types
    def approve(self, dst_address: str, amt: int, from_wallet: Wallet) -> str:
        return self.send_transaction("approve", (dst_address, amt), from_wallet)

    @enforce_types
    def transfer(self, dst_address: str, amt: int, from_wallet: Wallet) -> str:
        return self.send_transaction("transfer", (dst_address, amt), from_wallet)

    @enforce_types
    def transferFrom(
        self, src_address: str, dst_address: str, amt: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom", (dst_address, src_address, amt), from_wallet
        )

    # ===== Calculators
    @enforce_types
    def calcSpotPrice(
        self,
        tokenBalanceIn: int,
        tokenWeightIn: int,
        tokenBalanceOut: int,
        tokenWeightOut: int,
        swapFee: int,
    ) -> int:
        """Returns spotPrice."""
        return self.contract.caller.calcSpotPrice(
            tokenBalanceIn, tokenWeightIn, tokenBalanceOut, tokenWeightOut, swapFee
        )

    @enforce_types
    def calcOutGivenIn(
        self,
        tokenBalanceIn: int,
        tokenWeightIn: int,
        tokenBalanceOut: int,
        tokenWeightOut: int,
        tokenAmountIn: int,
        swapFee: int,
    ) -> int:
        """Returns tokenAmountOut."""
        return self.contract.caller.calcOutGivenIn(
            tokenBalanceIn,
            tokenWeightIn,
            tokenBalanceOut,
            tokenWeightOut,
            tokenAmountIn,
            swapFee,
        )

    @enforce_types
    def calcInGivenOut(
        self,
        tokenBalanceIn: int,
        tokenWeightIn: int,
        tokenBalanceOut: int,
        tokenWeightOut: int,
        tokenAmountOut: int,
        swapFee: int,
    ) -> int:
        """Returns tokenAmountIn."""
        return self.contract.caller.calcInGivenOut(
            tokenBalanceIn,
            tokenWeightIn,
            tokenBalanceOut,
            tokenWeightOut,
            tokenAmountOut,
            swapFee,
        )

    @enforce_types
    def calcPoolOutGivenSingleIn(
        self,
        tokenBalanceIn: int,
        tokenWeightIn: int,
        poolSupply: int,
        totalWeight: int,
        tokenAmountIn: int,
        swapFee: int,
    ) -> int:
        """Returns poolAmountOut."""
        return self.contract.caller.calcPoolOutGivenSingleIn(
            tokenBalanceIn,
            tokenWeightIn,
            poolSupply,
            totalWeight,
            tokenAmountIn,
            swapFee,
        )

    @enforce_types
    def calcSingleInGivenPoolOut(
        self,
        tokenBalanceIn: int,
        tokenWeightIn: int,
        poolSupply: int,
        totalWeight: int,
        poolAmountOut: int,
        swapFee: int,
    ) -> int:
        """Returns tokenAmountIn."""
        return self.contract.caller.calcSingleInGivenPoolOut(
            tokenBalanceIn,
            tokenWeightIn,
            poolSupply,
            totalWeight,
            poolAmountOut,
            swapFee,
        )

    @enforce_types
    def calcSingleOutGivenPoolIn(
        self,
        tokenBalanceOut: int,
        tokenWeightOut: int,
        poolSupply: int,
        totalWeight: int,
        poolAmountIn: int,
        swapFee: int,
    ) -> int:
        """Returns tokenAmountOut."""
        return self.contract.caller.calcSingleOutGivenPoolIn(
            tokenBalanceOut,
            tokenWeightOut,
            poolSupply,
            totalWeight,
            poolAmountIn,
            swapFee,
        )

    @enforce_types
    def calcPoolInGivenSingleOut(
        self,
        tokenBalanceOut: int,
        tokenWeightOut: int,
        poolSupply: int,
        totalWeight: int,
        tokenAmountOut: int,
        swapFee: int,
    ) -> int:
        """Returns poolAmountIn."""
        return self.contract.caller.calcPoolInGivenSingleOut(
            tokenBalanceOut,
            tokenWeightOut,
            poolSupply,
            totalWeight,
            tokenAmountOut,
            swapFee,
        )

    # ===== Events
    @enforce_types
    def get_liquidity_logs(
        self,
        event_name: str,
        from_block: int,
        to_block: Optional[int] = None,
        user_address: Optional[str] = None,
        this_pool_only: bool = True,
    ) -> Tuple:
        """
        :param event_name: str, one of LOG_JOIN, LOG_EXIT, LOG_SWAP
        """
        topic0 = self.get_event_signature(event_name)
        to_block = to_block or "latest"
        topics = [topic0]

        if user_address:
            assert Web3.isChecksumAddress(user_address)
            topics.append(
                f"0x000000000000000000000000{remove_0x_prefix(user_address).lower()}"
            )
        event = getattr(self.events, event_name)
        argument_filters = {"topics": topics}
        logs = self.getLogs(
            event(),
            argument_filters=argument_filters,
            fromBlock=from_block,
            toBlock=to_block,
            from_all_addresses=not this_pool_only,
        )
        return logs

    @enforce_types
    def get_join_logs(
        self,
        from_block: int,
        to_block: Optional[int] = None,
        user_address: Optional[str] = None,
        this_pool_only: bool = True,
    ) -> Tuple[AttributeDict]:
        return self.get_liquidity_logs(
            "LOG_JOIN", from_block, to_block, user_address, this_pool_only
        )

    @enforce_types
    def get_exit_logs(
        self,
        from_block: int,
        to_block: Optional[int] = None,
        user_address: Optional[str] = None,
        this_pool_only: bool = True,
    ) -> Tuple[AttributeDict]:
        return self.get_liquidity_logs(
            "LOG_EXIT", from_block, to_block, user_address, this_pool_only
        )

    @enforce_types
    def get_swap_logs(
        self,
        from_block: int,
        to_block: Optional[int] = None,
        user_address: Optional[str] = None,
        this_pool_only: bool = True,
    ) -> Tuple[AttributeDict]:
        return self.get_liquidity_logs(
            "LOG_SWAP", from_block, to_block, user_address, this_pool_only
        )
