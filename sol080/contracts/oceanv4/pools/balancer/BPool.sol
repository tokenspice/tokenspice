pragma solidity >=0.6.0;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "./BToken.sol";
import "./BMath.sol";
import "../../interfaces/ISideStaking.sol";

/**
 * @title BPool
 *
 * @dev Used by the (Ocean version) BFactory contract as a bytecode reference to
 *      deploy new BPools.
 *
 * This contract is is nearly identical to the BPool.sol contract at [1]
 *  The only difference is the "Proxy contract functionality" section
 *  given below. We'd inherit from BPool if we could, for simplicity.
 *  But we can't, because the proxy section needs to access private
 *  variables declared in BPool, and Solidity disallows this. Therefore
 *  the best we can do for now is clearly demarcate the proxy section.
 *
 *  [1] https://github.com/balancer-labs/balancer-core/contracts/.
 */
contract BPool is BMath, BToken {
    struct Record {
        bool bound; // is token bound to pool
        uint256 index; // private
        uint256 denorm; // denormalized weight
        uint256 balance;
    }

    event LOG_SWAP(
        address indexed caller,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 tokenAmountIn,
        uint256 tokenAmountOut,
        uint256 timestamp
    );

    event LOG_JOIN(
        address indexed caller,
        address indexed tokenIn,
        uint256 tokenAmountIn,
        uint256 timestamp
    );
    event LOG_SETUP(
        address indexed caller,
        address indexed baseToken,
        uint256 baseTokenAmountIn,
        uint256 baseTokenWeight,
        address indexed dataToken,
        uint256 dataTokenAmountIn,
        uint256 dataTokenWeight
    );

    event LOG_EXIT(
        address indexed caller,
        address indexed tokenOut,
        uint256 tokenAmountOut,
        uint256 timestamp
    );

    event LOG_CALL(
        bytes4 indexed sig,
        address indexed caller,
        uint256 timestamp,
        bytes data
    );

    event LOG_BPT(uint256 bptAmount);

    modifier _lock_() {
        require(!_mutex, "ERR_REENTRY");
        _mutex = true;
        _;
        _mutex = false;
    }

    modifier _viewlock_() {
        require(!_mutex, "ERR_REENTRY");
        _;
    }

    bool private _mutex;

    address private _controller; // has CONTROL role
    bool private _publicSwap; // true if PUBLIC can call SWAP functions

    address public _marketCollector;
    address public _opfCollector;
    // `setSwapFee` and `finalize` require CONTROL
    // `finalize` sets `PUBLIC can SWAP`, `PUBLIC can JOIN`
    bool private _finalized;

    address[] private _tokens;
    mapping(address => Record) private _records;
    uint256 private _totalWeight;
    ISideStaking ssContract;

    //-----------------------------------------------------------------------
    //Proxy contract functionality: begin
    bool private initialized;

    function isInitialized() external view returns (bool) {
        return initialized;
    }

    // Called prior to contract deployment
    // constructor() public {

    //     // _initialize(
    //     //     msg.sender,
    //     //     msg.sender,
    //     //     MIN_FEE,
    //     //     0,
    //     //     false,
    //     //     false,
    //     //     msg.sender,
    //     //     msg.sender
    //     // );
    // }

    // Called prior to contract initialization (e.g creating new BPool instance)
    // Calls private _initialize function. Only if contract is not initialized.
    function initialize(
        address controller,
        address factory,
        uint256[] calldata swapFees,
        bool publicSwap,
        bool finalized,
        address[2] calldata tokens,
        address[2] calldata feeCollectors
    ) external returns (bool) {
        require(!initialized, "ERR_ALREADY_INITIALIZED");
        require(controller != address(0), "ERR_INVALID_CONTROLLER_ADDRESS");
        require(factory != address(0), "ERR_INVALID_FACTORY_ADDRESS");
        require(swapFees[0] >= MIN_FEE, "ERR_MIN_FEE");
        require(swapFees[0] <= MAX_FEE, "ERR_MAX_FEE");
        return
            _initialize(
                controller,
                factory,
                swapFees,
                publicSwap,
                finalized,
                tokens,
                feeCollectors
            );
    }

    // Private function called on contract initialization.
    function _initialize(
        address controller,
        address factory,
        uint256[] memory swapFees,
        bool publicSwap,
        bool finalized,
        address[2] memory tokens,
        address[2] memory feeCollectors
    ) private returns (bool) {
        _controller = controller;
        _factory = factory;
        _swapFee = swapFees[0];

        _swapMarketFee = swapFees[1];
        _publicSwap = publicSwap;
        _finalized = finalized;
        _datatokenAddress = tokens[0];
        _basetokenAddress = tokens[1];
        _marketCollector = feeCollectors[0];
        _opfCollector = feeCollectors[1];
        initialized = true;
        ssContract = ISideStaking(_controller);
        return initialized;
    }

    //can be called only by the controller
    function setup(
        address dataTokenAddress,
        uint256 dataTokenAmount,
        uint256 dataTokenWeight,
        address baseTokenAddress,
        uint256 baseTokenAmount,
        uint256 baseTokenWeight
    ) external {
        require(msg.sender == _controller, "ERR_INVALID_CONTROLLER");
        require(
            dataTokenAddress == _datatokenAddress,
            "ERR_INVALID_DATATOKEN_ADDRESS"
        );
        require(
            baseTokenAddress == _basetokenAddress,
            "ERR_INVALID_BASETOKEN_ADDRESS"
        );
        // other inputs will be validated prior
        // calling the below functions
        // bind data token
        bind(dataTokenAddress, dataTokenAmount, dataTokenWeight);
        emit LOG_JOIN(
            msg.sender,
            dataTokenAddress,
            dataTokenAmount,
            block.timestamp
        );

        // bind base token
        bind(baseTokenAddress, baseTokenAmount, baseTokenWeight);
        emit LOG_JOIN(
            msg.sender,
            baseTokenAddress,
            baseTokenAmount,
            block.timestamp
        );
        // finalize
        finalize();
        emit LOG_SETUP(msg.sender, baseTokenAddress, baseTokenAmount, baseTokenWeight,
            dataTokenAddress, dataTokenAmount, dataTokenWeight
        );
    }

    //Proxy contract functionality: end
    //-----------------------------------------------------------------------

    function isPublicSwap() external view returns (bool) {
        return _publicSwap;
    }

    function isFinalized() external view returns (bool) {
        return _finalized;
    }

    function isBound(address t) external view returns (bool) {
        return _records[t].bound;
    }

    function getNumTokens() external view returns (uint256) {
        return _tokens.length;
    }

    function getCurrentTokens()
        external
        view
        _viewlock_
        returns (address[] memory tokens)
    {
        return _tokens;
    }

    function getFinalTokens()
        public
        view
        _viewlock_
        returns (address[] memory tokens)
    {
        require(_finalized, "ERR_NOT_FINALIZED");
        return _tokens;
    }

    function collectOPF() external {
        address[] memory tokens = getFinalTokens();
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 amount = communityFees[tokens[i]];
            communityFees[tokens[i]] = 0;
            IERC20(tokens[i]).transfer(_opfCollector, amount);
        }
    }

    function collectMarketFee(address to) external {
        require(_marketCollector == msg.sender, "ONLY MARKET COLLECTOR");

        address[] memory tokens = getFinalTokens();
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 amount = marketFees[tokens[i]];
            marketFees[tokens[i]] = 0;
            IERC20(tokens[i]).transfer(to, amount);
        }
    }

    function updateMarketFeeCollector(address _newCollector) external {
        require(_marketCollector == msg.sender, "ONLY MARKET COLLECTOR");
        _marketCollector = _newCollector;
    }

    function getDenormalizedWeight(address token)
        external
        view
        _viewlock_
        returns (uint256)
    {
        require(_records[token].bound, "ERR_NOT_BOUND");
        return _records[token].denorm;
    }

    function getTotalDenormalizedWeight()
        external
        view
        _viewlock_
        returns (uint256)
    {
        return _totalWeight;
    }

    function getNormalizedWeight(address token)
        external
        view
        _viewlock_
        returns (uint256)
    {
        require(_records[token].bound, "ERR_NOT_BOUND");
        uint256 denorm = _records[token].denorm;
        return bdiv(denorm, _totalWeight);
    }

    function getBalance(address token)
        external
        view
        _viewlock_
        returns (uint256)
    {
        require(_records[token].bound, "ERR_NOT_BOUND");
        return _records[token].balance;
    }

    function getSwapFee() external view returns (uint256) {
        return _swapFee;
    }

    function getController() external view returns (address) {
        return _controller;
    }

    function getDataTokenAddress() external view returns (address) {
        return _datatokenAddress;
    }

    function getBaseTokenAddress() external view returns (address) {
        return _basetokenAddress;
    }

    function setSwapFee(uint256 swapFee) public {
        require(!_finalized, "ERR_IS_FINALIZED");
        require(msg.sender == _controller, "ERR_NOT_CONTROLLER");
        require(swapFee >= MIN_FEE, "ERR_MIN_FEE");
        require(swapFee <= MAX_FEE, "ERR_MAX_FEE");
        _swapFee = swapFee;
    }

    function finalize() internal {
        _finalized = true;
        _publicSwap = true;

        _mintPoolShare(INIT_POOL_SUPPLY);
        _pushPoolShare(msg.sender, INIT_POOL_SUPPLY);
    }

    function bind(
        address token,
        uint256 balance,
        uint256 denorm
    ) internal {
        require(msg.sender == _controller, "ERR_NOT_CONTROLLER");
        require(!_records[token].bound, "ERR_IS_BOUND");
        require(!_finalized, "ERR_IS_FINALIZED");

        require(_tokens.length < MAX_BOUND_TOKENS, "ERR_MAX_TOKENS");

        _records[token] = Record({
            bound: true,
            index: _tokens.length,
            denorm: 0, // balance and denorm will be validated
            balance: 0 // and set by `rebind`
        });
        _tokens.push(token);
        rebind(token, balance, denorm);
    }

    function rebind(
        address token,
        uint256 balance,
        uint256 denorm
    ) internal {
        require(denorm >= MIN_WEIGHT, "ERR_MIN_WEIGHT");
        require(denorm <= MAX_WEIGHT, "ERR_MAX_WEIGHT");
        require(balance >= MIN_BALANCE, "ERR_MIN_BALANCE");

        // Adjust the denorm and totalWeight
        uint256 oldWeight = _records[token].denorm;
        if (denorm > oldWeight) {
            _totalWeight = badd(_totalWeight, bsub(denorm, oldWeight));
            require(_totalWeight <= MAX_TOTAL_WEIGHT, "ERR_MAX_TOTAL_WEIGHT");
        } else if (denorm < oldWeight) {
            _totalWeight = bsub(_totalWeight, bsub(oldWeight, denorm));
        }
        _records[token].denorm = denorm;

        // Adjust the balance record and actual token balance
        uint256 oldBalance = _records[token].balance;
        _records[token].balance = balance;
        if (balance > oldBalance) {
            _pullUnderlying(token, msg.sender, bsub(balance, oldBalance));
        } else if (balance < oldBalance) {
            // In this case liquidity is being withdrawn, so charge EXIT_FEE
            uint256 tokenBalanceWithdrawn = bsub(oldBalance, balance);
            uint256 tokenExitFee = bmul(tokenBalanceWithdrawn, EXIT_FEE);
            _pushUnderlying(
                token,
                msg.sender,
                bsub(tokenBalanceWithdrawn, tokenExitFee)
            );
            _pushUnderlying(token, _factory, tokenExitFee);
        }
    }

    // Absorb any tokens that have been sent to this contract into the pool
    // function gulp(address token) external _lock_ {
    //     require(_records[token].bound, "ERR_NOT_BOUND");
    //     _records[token].balance = IERC20(token).balanceOf(address(this));
    // }

    function getSpotPrice(address tokenIn, address tokenOut)
        external
        view
        _viewlock_
        returns (uint256 spotPrice)
    {
        require(_records[tokenIn].bound, "ERR_NOT_BOUND");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");
        Record storage inRecord = _records[tokenIn];
        Record storage outRecord = _records[tokenOut];
        return
            calcSpotPrice(
                inRecord.balance,
                inRecord.denorm,
                outRecord.balance,
                outRecord.denorm
            );
    }

    // view function used for batch buy. useful for frontend
    function getAmountInExactOut(
        address tokenIn,
        address tokenOut,
        uint256 tokenAmountOut
    )
        external
        view
        returns (
            // _viewlock_
            uint256 tokenAmountIn
        )
    {
        require(_records[tokenIn].bound, "ERR_NOT_BOUND");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");
        Record storage inRecord = _records[tokenIn];
        Record storage outRecord = _records[tokenOut];

        return
            calcInGivenOut(
                inRecord.balance,
                inRecord.denorm,
                outRecord.balance,
                outRecord.denorm,
                tokenAmountOut
            );
    }

    // view function useful for frontend
    function getAmountOutExactIn(
        address tokenIn,
        address tokenOut,
        uint256 tokenAmountIn
    )
        external
        view
        returns (
            //  _viewlock_
            uint256 tokenAmountOut
        )
    {
        require(_records[tokenIn].bound, "ERR_NOT_BOUND");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");
        Record storage inRecord = _records[tokenIn];
        Record storage outRecord = _records[tokenOut];
        return
            calcOutGivenIn(
                inRecord.balance,
                inRecord.denorm,
                outRecord.balance,
                outRecord.denorm,
                tokenAmountIn
            );
    }

    function joinPool(uint256 poolAmountOut, uint256[] calldata maxAmountsIn)
        external
        _lock_
    {
        require(_finalized, "ERR_NOT_FINALIZED");

        uint256 poolTotal = totalSupply();
        uint256 ratio = bdiv(poolAmountOut, poolTotal);
        require(ratio != 0, "ERR_MATH_APPROX");
        for (uint256 i = 0; i < _tokens.length; i++) {
            address t = _tokens[i];
            uint256 bal = _records[t].balance;
            uint256 tokenAmountIn = bmul(ratio, bal);
            require(tokenAmountIn != 0, "ERR_MATH_APPROX");
            require(tokenAmountIn <= maxAmountsIn[i], "ERR_LIMIT_IN");
            _records[t].balance = badd(_records[t].balance, tokenAmountIn);
            emit LOG_JOIN(msg.sender, t, tokenAmountIn, block.timestamp);
            _pullUnderlying(t, msg.sender, tokenAmountIn);
        }
        _mintPoolShare(poolAmountOut);
        _pushPoolShare(msg.sender, poolAmountOut);
        emit LOG_BPT(poolAmountOut);
    }

    function exitPool(uint256 poolAmountIn, uint256[] calldata minAmountsOut)
        external
        _lock_
    {
        require(_finalized, "ERR_NOT_FINALIZED");

        uint256 poolTotal = totalSupply();
        uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);
        uint256 pAiAfterExitFee = bsub(poolAmountIn, exitFee);
        uint256 ratio = bdiv(pAiAfterExitFee, poolTotal);
        require(ratio != 0, "ERR_MATH_APPROX");

        _pullPoolShare(msg.sender, poolAmountIn);
        _pushPoolShare(_factory, exitFee);
        _burnPoolShare(pAiAfterExitFee);

        for (uint256 i = 0; i < _tokens.length; i++) {
            address t = _tokens[i];
            uint256 bal = _records[t].balance;
            uint256 tokenAmountOut = bmul(ratio, bal);
            require(tokenAmountOut != 0, "ERR_MATH_APPROX");
            require(tokenAmountOut >= minAmountsOut[i], "ERR_LIMIT_OUT");
            _records[t].balance = bsub(_records[t].balance, tokenAmountOut);
            emit LOG_EXIT(msg.sender, t, tokenAmountOut, block.timestamp);
            _pushUnderlying(t, msg.sender, tokenAmountOut);
        }
    }

    function swapExactAmountIn(
        address tokenIn,
        uint256 tokenAmountIn,
        address tokenOut,
        uint256 minAmountOut,
        uint256 maxPrice
    ) external _lock_ returns (uint256 tokenAmountOut, uint256 spotPriceAfter) {
        require(_finalized, "ERR_NOT_FINALIZED");

        require(_records[tokenIn].bound, "ERR_NOT_BOUND");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");
        Record storage inRecord = _records[address(tokenIn)];
        Record storage outRecord = _records[address(tokenOut)];

        require(
            tokenAmountIn <= bmul(inRecord.balance, MAX_IN_RATIO),
            "ERR_MAX_IN_RATIO"
        );

        uint256 spotPriceBefore = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        );

        require(spotPriceBefore <= maxPrice, "ERR_BAD_LIMIT_PRICE");
        uint256 balanceInToAdd;
        uint256[4] memory data = [
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        ];
        (tokenAmountOut, balanceInToAdd) = calcOutGivenInSwap(
            data,
            tokenAmountIn,
            tokenIn
        );

        require(tokenAmountOut >= minAmountOut, "ERR_LIMIT_OUT");

        inRecord.balance = badd(inRecord.balance, balanceInToAdd);
        outRecord.balance = bsub(outRecord.balance, tokenAmountOut);

        spotPriceAfter = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        );

        require(spotPriceAfter >= spotPriceBefore, "ERR_MATH_APPROX");
        require(spotPriceAfter <= maxPrice, "ERR_LIMIT_PRICE");

        require(
            spotPriceBefore <= bdiv(tokenAmountIn, tokenAmountOut),
            "ERR_MATH_APPROX"
        );

        emit LOG_SWAP(
            msg.sender,
            tokenIn,
            tokenOut,
            tokenAmountIn,
            tokenAmountOut,
            block.timestamp
        );

        _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);
        _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);

        return (tokenAmountOut, spotPriceAfter); //returning spot price 0 because there is no public spotPrice
    }

    function swapExactAmountOut(
        address tokenIn,
        uint256 maxAmountIn,
        address tokenOut,
        uint256 tokenAmountOut,
        uint256 maxPrice
    ) external _lock_ returns (uint256 tokenAmountIn, uint256 spotPriceAfter) {
        require(_finalized, "ERR_NOT_FINALIZED");
        require(_records[tokenIn].bound, "ERR_NOT_BOUND");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");

        Record storage inRecord = _records[address(tokenIn)];
        Record storage outRecord = _records[address(tokenOut)];

        require(
            tokenAmountOut <= bmul(outRecord.balance, MAX_OUT_RATIO),
            "ERR_MAX_OUT_RATIO"
        );

        uint256 spotPriceBefore = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        );

        require(spotPriceBefore <= maxPrice, "ERR_BAD_LIMIT_PRICE");
        // this is the amount we are going to register in balances
        // (only takes account of swapFee, not OPF and market fee, in order to not affect price during following swaps, fee wtihdrawl etc)
        uint256 balanceToAdd;
        uint256[4] memory data = [
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        ];

        (tokenAmountIn, balanceToAdd) = calcInGivenOutSwap(
            data,
            tokenAmountOut,
            tokenIn
        );

        require(tokenAmountIn <= maxAmountIn, "ERR_LIMIT_IN");

        inRecord.balance = badd(inRecord.balance, balanceToAdd);
        outRecord.balance = bsub(outRecord.balance, tokenAmountOut);

        spotPriceAfter = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        );

        require(spotPriceAfter >= spotPriceBefore, "ERR_MATH_APPROX");
        require(spotPriceAfter <= maxPrice, "ERR_LIMIT_PRICE");
        require(
            spotPriceBefore <= bdiv(tokenAmountIn, tokenAmountOut),
            "ERR_MATH_APPROX"
        );

        emit LOG_SWAP(
            msg.sender,
            tokenIn,
            tokenOut,
            tokenAmountIn,
            tokenAmountOut,
            block.timestamp
        );

        _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);
        _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);

        return (tokenAmountIn, spotPriceAfter);
    }

    function joinswapExternAmountIn(
        address tokenIn,
        uint256 tokenAmountIn,
        uint256 minPoolAmountOut
    ) external _lock_ returns (uint256 poolAmountOut) {
        require(_finalized, "ERR_NOT_FINALIZED");
        require(_records[tokenIn].bound, "ERR_NOT_BOUND");
        require(
            tokenAmountIn <= bmul(_records[tokenIn].balance, MAX_IN_RATIO),
            "ERR_MAX_IN_RATIO"
        );
        //ask ssContract
        Record storage inRecord = _records[tokenIn];

        poolAmountOut = calcPoolOutGivenSingleIn(
            inRecord.balance,
            inRecord.denorm,
            _totalSupply,
            _totalWeight,
            tokenAmountIn
        );

        require(poolAmountOut >= minPoolAmountOut, "ERR_LIMIT_OUT");

        inRecord.balance = badd(inRecord.balance, tokenAmountIn);

        emit LOG_JOIN(msg.sender, tokenIn, tokenAmountIn, block.timestamp);
        emit LOG_BPT(poolAmountOut);
        _mintPoolShare(poolAmountOut);
        _pushPoolShare(msg.sender, poolAmountOut);

        _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);

        //ask the ssContract to stake as well
        //calculate how much should the 1ss stake
        Record storage ssInRecord = _records[_datatokenAddress];
        address ssStakeToken;
        uint256 ssAmountIn = calcSingleInGivenPoolOut(
            ssInRecord.balance,
            ssInRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountOut
        );
        if (tokenIn == _datatokenAddress) {
            ssStakeToken = _basetokenAddress;
        } else {
            // ssInRecord = _records[_basetokenAddress];
            ssStakeToken = _datatokenAddress;
        }
        if (
            ssContract.canStake(_datatokenAddress, ssStakeToken, ssAmountIn) ==
            true
        ) {
            //call 1ss to approve

            ssContract.Stake(_datatokenAddress, ssStakeToken, ssAmountIn);
            // follow the same path
            ssInRecord.balance = badd(ssInRecord.balance, ssAmountIn);
            emit LOG_JOIN(
                _controller,
                ssStakeToken,
                ssAmountIn,
                block.timestamp
            );
            emit LOG_BPT(poolAmountOut);
            _mintPoolShare(poolAmountOut);
            _pushPoolShare(_controller, poolAmountOut);
            _pullUnderlying(ssStakeToken, _controller, ssAmountIn);
        }
        return poolAmountOut;
    }

    function joinswapPoolAmountOut(
        address tokenIn,
        uint256 poolAmountOut,
        uint256 maxAmountIn
    ) external _lock_ returns (uint256 tokenAmountIn) {
        require(_finalized, "ERR_NOT_FINALIZED");
        require(_records[tokenIn].bound, "ERR_NOT_BOUND");

        Record storage inRecord = _records[tokenIn];

        tokenAmountIn = calcSingleInGivenPoolOut(
            inRecord.balance,
            inRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountOut
        );

        //ask ssContract
        require(tokenAmountIn != 0, "ERR_MATH_APPROX");
        require(tokenAmountIn <= maxAmountIn, "ERR_LIMIT_IN");

        require(
            tokenAmountIn <= bmul(_records[tokenIn].balance, MAX_IN_RATIO),
            "ERR_MAX_IN_RATIO"
        );

        inRecord.balance = badd(inRecord.balance, tokenAmountIn);

        emit LOG_JOIN(msg.sender, tokenIn, tokenAmountIn, block.timestamp);
        emit LOG_BPT(poolAmountOut);
        _mintPoolShare(poolAmountOut);
        _pushPoolShare(msg.sender, poolAmountOut);
        _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);

        Record storage ssInRecord = _records[_datatokenAddress];
        //ask the ssContract to stake as well
        //calculate how much should the 1ss stake
        uint256 ssAmountIn = calcSingleInGivenPoolOut(
            ssInRecord.balance,
            ssInRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountOut
        );
        address ssStakeToken;

        if (tokenIn == _datatokenAddress) {
            ssStakeToken = _basetokenAddress;
        } else {
            ssStakeToken = _datatokenAddress;
        }
        if (
            ssContract.canStake(_datatokenAddress, ssStakeToken, ssAmountIn) ==
            true
        ) {
            //call 1ss to approve
            ssContract.Stake(_datatokenAddress, ssStakeToken, ssAmountIn);
            // follow the same path
            ssInRecord.balance = badd(ssInRecord.balance, ssAmountIn);
            emit LOG_JOIN(
                _controller,
                ssStakeToken,
                ssAmountIn,
                block.timestamp
            );
            _mintPoolShare(poolAmountOut);
            _pushPoolShare(_controller, poolAmountOut);
            _pullUnderlying(ssStakeToken, _controller, ssAmountIn);
        }
        return tokenAmountIn;
    }

    function exitswapPoolAmountIn(
        address tokenOut,
        uint256 poolAmountIn,
        uint256 minAmountOut
    ) external _lock_ returns (uint256 tokenAmountOut) {
        require(_finalized, "ERR_NOT_FINALIZED");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");

        Record storage outRecord = _records[tokenOut];

        tokenAmountOut = calcSingleOutGivenPoolIn(
            outRecord.balance,
            outRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountIn
        );

        require(tokenAmountOut >= minAmountOut, "ERR_LIMIT_OUT");

        require(
            tokenAmountOut <= bmul(_records[tokenOut].balance, MAX_OUT_RATIO),
            "ERR_MAX_OUT_RATIO"
        );

        outRecord.balance = bsub(outRecord.balance, tokenAmountOut);

        uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);

        emit LOG_EXIT(msg.sender, tokenOut, tokenAmountOut, block.timestamp);
        emit LOG_BPT(poolAmountIn);

        _pullPoolShare(msg.sender, poolAmountIn);

        _burnPoolShare(bsub(poolAmountIn, exitFee));
        _pushPoolShare(_factory, exitFee);
        _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);

        //ask the ssContract to unstake as well
        //calculate how much should the 1ss unstake
        address ssStakeToken;
        if (tokenOut == _datatokenAddress) {
            ssStakeToken = _basetokenAddress;
        } else {
            ssStakeToken = _datatokenAddress;
        }

        if (
            ssContract.canUnStake(
                _datatokenAddress,
                ssStakeToken,
                poolAmountIn
            ) == true
        ) {
            Record storage ssOutRecord = _records[_datatokenAddress];
            uint256 ssAmountOut = calcSingleOutGivenPoolIn(
                ssOutRecord.balance,
                ssOutRecord.denorm,
                _totalSupply,
                _totalWeight,
                poolAmountIn
            );

            ssOutRecord.balance = bsub(ssOutRecord.balance, ssAmountOut);
            exitFee = bmul(poolAmountIn, EXIT_FEE);
            emit LOG_EXIT(
                _controller,
                ssStakeToken,
                ssAmountOut,
                block.timestamp
            );
            _pullPoolShare(_controller, poolAmountIn);
            _burnPoolShare(bsub(poolAmountIn, exitFee));
            _pushPoolShare(_factory, exitFee);
            _pushUnderlying(ssStakeToken, _controller, ssAmountOut);
            //call unstake on 1ss to do cleanup on their side
            ssContract.UnStake(
                _datatokenAddress,
                ssStakeToken,
                ssAmountOut,
                poolAmountIn
            );
        }
        return tokenAmountOut;
    }

    function exitswapExternAmountOut(
        address tokenOut,
        uint256 tokenAmountOut,
        uint256 maxPoolAmountIn
    ) external _lock_ returns (uint256 poolAmountIn) {
        require(_finalized, "ERR_NOT_FINALIZED");
        require(_records[tokenOut].bound, "ERR_NOT_BOUND");
        require(
            tokenAmountOut <= bmul(_records[tokenOut].balance, MAX_OUT_RATIO),
            "ERR_MAX_OUT_RATIO"
        );

        Record storage outRecord = _records[tokenOut];

        poolAmountIn = calcPoolInGivenSingleOut(
            outRecord.balance,
            outRecord.denorm,
            _totalSupply,
            _totalWeight,
            tokenAmountOut
        );

        require(poolAmountIn != 0, "ERR_MATH_APPROX");
        require(poolAmountIn <= maxPoolAmountIn, "ERR_LIMIT_IN");

        outRecord.balance = bsub(outRecord.balance, tokenAmountOut);

        uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);

        emit LOG_EXIT(msg.sender, tokenOut, tokenAmountOut, block.timestamp);
        emit LOG_BPT(poolAmountIn);
        _pullPoolShare(msg.sender, poolAmountIn);
        _burnPoolShare(bsub(poolAmountIn, exitFee));
        _pushPoolShare(_factory, exitFee);
        _pushUnderlying(tokenOut, msg.sender, tokenAmountOut);

        //ask the ssContract to unstake as well
        //calculate how much should the 1ss unstake
        //ask ssContract
        address ssStakeToken;

        if (tokenOut == _datatokenAddress) {
            ssStakeToken = _basetokenAddress;
        } else {
            ssStakeToken = _datatokenAddress;
        }
        if (
            ssContract.canUnStake(
                _datatokenAddress,
                ssStakeToken,
                poolAmountIn
            ) == true
        ) {
            Record storage ssOutRecord = _records[_datatokenAddress];
            uint256 ssAmountOut = calcSingleOutGivenPoolIn(
                ssOutRecord.balance,
                ssOutRecord.denorm,
                _totalSupply,
                _totalWeight,
                poolAmountIn
            );
            ssOutRecord.balance = bsub(ssOutRecord.balance, ssAmountOut);
            exitFee = bmul(poolAmountIn, EXIT_FEE);
            emit LOG_EXIT(
                _controller,
                ssStakeToken,
                ssAmountOut,
                block.timestamp
            );
            _pullPoolShare(_controller, poolAmountIn);
            _burnPoolShare(bsub(poolAmountIn, exitFee));
            _pushPoolShare(_factory, exitFee);
            _pushUnderlying(ssStakeToken, _controller, ssAmountOut);
            //call unstake on 1ss to do cleanup on their side
            ssContract.UnStake(
                _datatokenAddress,
                ssStakeToken,
                ssAmountOut,
                poolAmountIn
            );
        }
        return poolAmountIn;
    }

    function calcSingleOutPoolIn(address tokenOut, uint256 poolAmountIn)
        external
        view
        returns (uint256 tokenAmountOut)
    {
        Record memory outRecord = _records[tokenOut];

        tokenAmountOut = calcSingleOutGivenPoolIn(
            outRecord.balance,
            outRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountIn
        );

        return tokenAmountOut;
    }

    function calcPoolInSingleOut(address tokenOut, uint256 tokenAmountOut)
        external
        view
        returns (uint256 poolAmountIn)
    {
        Record memory outRecord = _records[tokenOut];

        poolAmountIn = calcPoolInGivenSingleOut(
            outRecord.balance,
            outRecord.denorm,
            _totalSupply,
            _totalWeight,
            tokenAmountOut
        );
        return poolAmountIn;
    }

    function calcSingleInPoolOut(address tokenIn, uint256 poolAmountOut)
        external
        view
        returns (uint256 tokenAmountIn)
    {
        Record memory inRecord = _records[tokenIn];

        tokenAmountIn = calcSingleInGivenPoolOut(
            inRecord.balance,
            inRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountOut
        );

        return tokenAmountIn;
    }

    function calcPoolOutSingleIn(address tokenIn, uint256 tokenAmountIn)
        external
        view
        returns (uint256 poolAmountOut)
    {
        Record memory inRecord = _records[tokenIn];

        poolAmountOut = calcPoolOutGivenSingleIn(
            inRecord.balance,
            inRecord.denorm,
            _totalSupply,
            _totalWeight,
            tokenAmountIn
        );

        return poolAmountOut;
    }

    // ==
    // 'Underlying' token-manipulation functions make external calls but are NOT locked
    // You must `_lock_` or otherwise ensure reentry-safety

    function _pullUnderlying(
        address erc20,
        address from,
        uint256 amount
    ) internal {
        bool xfer = IERC20(erc20).transferFrom(from, address(this), amount);

        require(xfer, "ERR_ERC20_FALSE");
    }

    function _pushUnderlying(
        address erc20,
        address to,
        uint256 amount
    ) internal {
        bool xfer = IERC20(erc20).transfer(to, amount);
        require(xfer, "ERR_ERC20_FALSE");
    }

    function _pullPoolShare(address from, uint256 amount) internal {
        _pull(from, amount);
    }

    function _pushPoolShare(address to, uint256 amount) internal {
        _push(to, amount);
    }

    function _mintPoolShare(uint256 amount) internal {
        _mint(amount);
    }

    function _burnPoolShare(uint256 amount) internal {
        _burn(amount);
    }
}
