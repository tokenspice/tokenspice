pragma solidity 0.8.10;
// Copyright Balancer, BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "./BToken.sol";
import "./BMath.sol";
import "../../interfaces/ISideStaking.sol";
import "../../utils/SafeERC20.sol";

/**
 * @title BPool
 *
 * @dev Used by the (Ocean version) BFactory contract as a bytecode reference to
 *      deploy new BPools.
 *
 * This contract is a friendly fork of Balancer [1]
 *  [1] https://github.com/balancer-labs/balancer-core/contracts/.

 * All fees are expressed in wei.  Examples:
 *  (1e17 = 10 % , 1e16 = 1% , 1e15 = 0.1%, 1e14 = 0.01%)
 */
contract BPool is BMath, BToken {
    using SafeERC20 for IERC20;
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
        address indexed datatoken,
        uint256 datatokenAmountIn,
        uint256 datatokenWeight
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
    event LOG_BPT_SS(uint256 bptAmount); //emitted for SS contract

    event OPCFee(
        address caller,
        address OPCWallet,
        address token,
        uint256 amount
    );
    event SwapFeeChanged(address caller, uint256 amount);
    event PublishMarketFee(
        address caller,
        address marketAddress,
        address token,
        uint256 amount
    );
    // emited for fees sent to consumeMarket
    event ConsumeMarketFee(address to, address token, uint256 amount);
    event SWAP_FEES(uint LPFeeAmount, uint oceanFeeAmount, uint marketFeeAmount,
        uint consumeMarketFeeAmount, address tokenFeeAddress);
    //emitted for every change done by publisherMarket
    event PublishMarketFeeChanged(address caller, address newMarketCollector, uint256 swapFee);

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

    //address public _publishMarketCollector;
    address public _publishMarketCollector;
    address public _opcCollector;
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

    /**
     * @dev getId
     *      Return template id in case we need different ABIs. 
     *      If you construct your own template, please make sure to change the hardcoded value
     */
    function getId() pure public returns (uint8) {
        return 1;
    }

    function isInitialized() external view returns (bool) {
        return initialized;
    }

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
        require(swapFees[1] == 0 || swapFees[1]>= MIN_FEE, "ERR_MIN_FEE");
        require(swapFees[1] <= MAX_FEE, "ERR_MAX_FEE");
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
        emit SwapFeeChanged(msg.sender, _swapFee);
        _swapPublishMarketFee = swapFees[1];
        _publicSwap = publicSwap;
        _finalized = finalized;
        _datatokenAddress = tokens[0];
        _baseTokenAddress = tokens[1];
        _publishMarketCollector = feeCollectors[0];
        emit PublishMarketFeeChanged(msg.sender, _publishMarketCollector, _swapPublishMarketFee);
        _opcCollector = feeCollectors[1];
        initialized = true;
        ssContract = ISideStaking(_controller);
        return initialized;
    }

    
    /**
     * @dev setup
     *      Initial setup of the pool
     *      Can be called only by the controller
     * @param datatokenAddress datatokenAddress
     * @param datatokenAmount how many datatokens in the initial reserve
     * @param datatokenWeight datatoken weight (hardcoded in deployer at 50%)
     * @param baseTokenAddress base token
     * @param baseTokenAmount how many basetokens in the initial reserve
     * @param baseTokenWeight base weight (hardcoded in deployer at 50%)
     */
    function setup(
        address datatokenAddress,
        uint256 datatokenAmount,
        uint256 datatokenWeight,
        address baseTokenAddress,
        uint256 baseTokenAmount,
        uint256 baseTokenWeight
    ) external _lock_ {
        require(msg.sender == _controller, "ERR_INVALID_CONTROLLER");
        require(
            datatokenAddress == _datatokenAddress,
            "ERR_INVALID_DATATOKEN_ADDRESS"
        );
        require(
            baseTokenAddress == _baseTokenAddress,
            "ERR_INVALID_baseToken_ADDRESS"
        );
        // other inputs will be validated prior
        // calling the below functions
        // bind datatoken
        bind(datatokenAddress, datatokenAmount, datatokenWeight);
        emit LOG_JOIN(
            msg.sender,
            datatokenAddress,
            datatokenAmount,
            block.timestamp
        );

        // bind baseToken
        bind(baseTokenAddress, baseTokenAmount, baseTokenWeight);
        emit LOG_JOIN(
            msg.sender,
            baseTokenAddress,
            baseTokenAmount,
            block.timestamp
        );
        // finalize
        finalize();
        emit LOG_SETUP(
            msg.sender,
            baseTokenAddress,
            baseTokenAmount,
            baseTokenWeight,
            datatokenAddress,
            datatokenAmount,
            datatokenWeight
        );
    }

    //Proxy contract functionality: end
    //-----------------------------------------------------------------------
    /**
     * @dev isPublicSwap
     *      Returns true if swapping is allowed
     */
    function isPublicSwap() external view returns (bool) {
        return _publicSwap;
    }
    /**
     * @dev isFinalized
     *      Returns true if pool is finalized
     */
    function isFinalized() external view returns (bool) {
        return _finalized;
    }

    /**
     * @dev isBound
     *      Returns true if token is bound
     * @param t token to be checked
     */
    function isBound(address t) external view returns (bool) {
        return _records[t].bound;
    }

    function _checkBound(address token) internal view {
        require(_records[token].bound, "ERR_NOT_BOUND");
    }

    /**
     * @dev getNumTokens
     *      Returns number of tokens bounded to pool
     */
    function getNumTokens() external view returns (uint256) {
        return _tokens.length;
    }

    /**
     * @dev getCurrentTokens
     *      Returns tokens bounded to pool, before the pool is finalized
     */
    function getCurrentTokens()
        external
        view
        _viewlock_
        returns (address[] memory tokens)
    {
        return _tokens;
    }

    /**
     * @dev getFinalTokens
     *      Returns tokens bounded to pool, after the pool was finalized
     */
    function getFinalTokens()
        public
        view
        _viewlock_
        returns (address[] memory tokens)
    {
        require(_finalized, "ERR_NOT_FINALIZED");
        return _tokens;
    }

    /**
     * @dev collectOPC
     *      Collects and send all OPC Fees to _opcCollector.
     *      This funtion can be called by anyone, because fees are being sent to _opcCollector
     */
    function collectOPC() external {
        address[] memory tokens = getFinalTokens();
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 amount = communityFees[tokens[i]];
            communityFees[tokens[i]] = 0;
            IERC20(tokens[i]).safeTransfer(_opcCollector, amount);
            emit OPCFee(msg.sender, _opcCollector, tokens[i], amount);
        }
    }

    /**
     * @dev getCurrentOPCFees
     *      Get the current amount of fees which can be withdrawned by OPC
     * @return address[] - array of tokens addresses
     *         uint256[] - array of amounts
     */
    function getCurrentOPCFees()
        public
        view
        returns (address[] memory, uint256[] memory)
    {
        address[] memory poolTokens = getFinalTokens();
        address[] memory tokens = new address[](poolTokens.length);
        uint256[] memory amounts = new uint256[](poolTokens.length);
        for (uint256 i = 0; i < poolTokens.length; i++) {
            tokens[i] = poolTokens[i];
            amounts[i] = communityFees[poolTokens[i]];
        }
        return (tokens, amounts);
    }

    /**
     * @dev getCurrentMarketFees
     *      Get the current amount of fees which can be withdrawned by _publishMarketCollector
     * @return address[] - array of tokens addresses
     *         uint256[] - array of amounts
     */
    function getCurrentMarketFees()
        public
        view
        returns (address[] memory, uint256[] memory)
    {
        address[] memory poolTokens = getFinalTokens();
        address[] memory tokens = new address[](poolTokens.length);
        uint256[] memory amounts = new uint256[](poolTokens.length);
        for (uint256 i = 0; i < poolTokens.length; i++) {
            tokens[i] = poolTokens[i];
            amounts[i] = publishMarketFees[poolTokens[i]];
        }
        return (tokens, amounts);
    }

    /**
     * @dev collectMarketFee
     *      Collects and send all Market Fees to _publishMarketCollector.
     *      This function can be called by anyone, because fees are being sent to _publishMarketCollector
     */
    function collectMarketFee() external {
        address[] memory tokens = getFinalTokens();
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 amount = publishMarketFees[tokens[i]];
            publishMarketFees[tokens[i]] = 0;
            IERC20(tokens[i]).safeTransfer(_publishMarketCollector, amount);
            emit PublishMarketFee(
                msg.sender,
                _publishMarketCollector,
                tokens[i],
                amount
            );
        }
    }

    /**
     * @dev updatePublishMarketFee
     *      Set _newCollector as _publishMarketCollector
     * @param _newCollector new _publishMarketCollector
     * @param _newSwapFee new swapFee
     */
    function updatePublishMarketFee(address _newCollector, uint256 _newSwapFee) external {
        require(_publishMarketCollector == msg.sender, "ONLY MARKET COLLECTOR");
        require(_newCollector != address(0), "Invalid _newCollector address");
        require(_newSwapFee ==0 || _newSwapFee >= MIN_FEE, "ERR_MIN_FEE");
        require(_newSwapFee <= MAX_FEE, "ERR_MAX_FEE");
        _publishMarketCollector = _newCollector;
        _swapPublishMarketFee = _newSwapFee;
        emit PublishMarketFeeChanged(msg.sender, _publishMarketCollector, _swapPublishMarketFee);
    }

    /**
     * @dev getDenormalizedWeight
     *      Returns denormalized weight of a token
     * @param token token to be checked
     */
    function getDenormalizedWeight(address token)
        external
        view
        _viewlock_
        returns (uint256)
    {
        _checkBound(token);
        return _records[token].denorm;
    }

     /**
     * @dev getTotalDenormalizedWeight
     *      Returns total denormalized weught of the pool
     */
    function getTotalDenormalizedWeight()
        external
        view
        _viewlock_
        returns (uint256)
    {
        return _totalWeight;
    }

    /**
     * @dev getNormalizedWeight
     *      Returns normalized weight of a token
     * @param token token to be checked
     */
    
    function getNormalizedWeight(address token)
        external
        view
        _viewlock_
        returns (uint256)
    {
        _checkBound(token);
        uint256 denorm = _records[token].denorm;
        return bdiv(denorm, _totalWeight);
    }


    /**
     * @dev getBalance
     *      Returns the current token reserve amount
     * @param token token to be checked
     */
    function getBalance(address token)
        external
        view
        _viewlock_
        returns (uint256)
    {
        _checkBound(token);
        return _records[token].balance;
    }

    /**
     * @dev getSwapFee
     *      Returns the current Liquidity Providers swap fee
     */
    function getSwapFee() external view returns (uint256) {
        return _swapFee;
    }

    /**
     * @dev getMarketFee
     *      Returns the current fee of publishingMarket
     */
    function getMarketFee() external view returns (uint256) {
        return _swapPublishMarketFee;
    }

    /**
     * @dev getController
     *      Returns the current controller address (ssBot)
     */
    function getController() external view returns (address) {
        return _controller;
    }

    /**
     * @dev getDatatokenAddress
     *      Returns the current datatoken address
     */
    function getDatatokenAddress() external view returns (address) {
        return _datatokenAddress;
    }

    /**
     * @dev getBaseTokenAddress
     *      Returns the current baseToken address
     */
    function getBaseTokenAddress() external view returns (address) {
        return _baseTokenAddress;
    }


    /**
     * @dev setSwapFee
     *      Allows controller to change the swapFee
     * @param swapFee new swap fee (max 1e17 = 10 % , 1e16 = 1% , 1e15 = 0.1%, 1e14 = 0.01%)
     */
    function setSwapFee(uint256 swapFee) public {
        require(msg.sender == _controller, "ERR_NOT_CONTROLLER");
        require(swapFee >= MIN_FEE, "ERR_MIN_FEE");
        require(swapFee <= MAX_FEE, "ERR_MAX_FEE");
        _swapFee = swapFee;
        emit SwapFeeChanged(msg.sender, swapFee);
    }

    /**
     * @dev finalize
     *      Finalize pool. After this,new tokens cannot be bound
     */
    function finalize() internal {
        _finalized = true;
        _publicSwap = true;

        _mintPoolShare(INIT_POOL_SUPPLY);
        _pushPoolShare(msg.sender, INIT_POOL_SUPPLY);
    }

    /**
     * @dev bind
     *      Bind a new token to the pool.
     * @param token token address
     * @param balance initial reserve
     * @param denorm denormalized weight
     */
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

    /**
     * @dev rebind
     *      Update pool reserves & weight after a token bind
     * @param token token address
     * @param balance initial reserve
     * @param denorm denormalized weight
     */
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
            // In this case liquidity is being withdrawn, we don't have EXIT_FEES
            uint256 tokenBalanceWithdrawn = bsub(oldBalance, balance);
            _pushUnderlying(
                token,
                msg.sender,
                tokenBalanceWithdrawn
            );
        }
    }

    /**
     * @dev getSpotPrice
     *      Return the spot price of swapping tokenIn to tokenOut
     * @param tokenIn in token
     * @param tokenOut out token
     * @param _consumeMarketSwapFee consume market swap fee 
     */
    function getSpotPrice(
        address tokenIn,
        address tokenOut,
        uint256 _consumeMarketSwapFee
    ) external view _viewlock_ returns (uint256 spotPrice) {
        _checkBound(tokenIn);
        _checkBound(tokenOut);
        Record storage inRecord = _records[tokenIn];
        Record storage outRecord = _records[tokenOut];
        return
            calcSpotPrice(
                inRecord.balance,
                inRecord.denorm,
                outRecord.balance,
                outRecord.denorm,
                _consumeMarketSwapFee
            );
    }

    // view function used for batch buy. useful for frontend
     /**
     * @dev getAmountInExactOut
     *      How many tokensIn do you need in order to get exact tokenAmountOut.
            Returns: tokenAmountIn, LPFee, opcFee , publishMarketSwapFee, consumeMarketSwapFee
     * @param tokenIn token to be swaped
     * @param tokenOut token to get
     * @param tokenAmountOut exact amount of tokenOut
     * @param _consumeMarketSwapFee consume market swap fee
     */

    function getAmountInExactOut(
        address tokenIn,
        address tokenOut,
        uint256 tokenAmountOut,
        uint256 _consumeMarketSwapFee
    )
        external
        view
        returns (
            // _viewlock_
            uint256 tokenAmountIn, uint lpFeeAmount, 
            uint oceanFeeAmount, 
            uint publishMarketSwapFeeAmount,
            uint consumeMarketSwapFeeAmount
        )
    {
        _checkBound(tokenIn);
        _checkBound(tokenOut);
        uint256[4] memory data = [
            _records[tokenIn].balance,
            _records[tokenIn].denorm,
            _records[tokenOut].balance,
            _records[tokenOut].denorm
        ];
        uint tokenAmountInBalance;
        swapfees memory _swapfees;
        (tokenAmountIn, tokenAmountInBalance, _swapfees) =        
            calcInGivenOut(
                data,
                tokenAmountOut,
                // tokenIn,
                _consumeMarketSwapFee
            );
        return(tokenAmountIn, _swapfees.LPFee, _swapfees.oceanFeeAmount, 
        _swapfees.publishMarketFeeAmount, _swapfees.consumeMarketFee);

    }

    // view function useful for frontend
    /**
     * @dev getAmountOutExactIn
     *      How many tokensOut you will get for a exact tokenAmountIn
            Returns: tokenAmountOut, LPFee, opcFee ,  publishMarketSwapFee, consumeMarketSwapFee
     * @param tokenIn token to be swaped
     * @param tokenOut token to get
     * @param tokenAmountOut exact amount of tokenOut
     * @param _consumeMarketSwapFee consume market swap fee
     */
    function getAmountOutExactIn(
        address tokenIn,
        address tokenOut,
        uint256 tokenAmountIn,
        uint256 _consumeMarketSwapFee
    )
        external
        view
        returns (
            //  _viewlock_
            uint256 tokenAmountOut,
            uint lpFeeAmount, 
            uint oceanFeeAmount, 
            uint publishMarketSwapFeeAmount,
            uint consumeMarketSwapFeeAmount
        )
    {
        _checkBound(tokenIn);
        _checkBound(tokenOut);
        uint256[4] memory data = [
            _records[tokenIn].balance,
            _records[tokenIn].denorm,
            _records[tokenOut].balance,
            _records[tokenOut].denorm
        ];
        uint balanceInToAdd;
        swapfees memory _swapfees;
         (tokenAmountOut, balanceInToAdd, _swapfees) =        
            calcOutGivenIn(
                data,
                tokenAmountIn,
               // tokenIn,
                _consumeMarketSwapFee
            );
        return(tokenAmountOut, _swapfees.LPFee, 
        _swapfees.oceanFeeAmount, _swapfees.publishMarketFeeAmount, _swapfees.consumeMarketFee);
    }


    /**
     * @dev joinPool
     *      Adds dual side liquidity to the pool (both datatoken and basetoken)
     * @param poolAmountOut expected number of pool shares that you will get
     * @param maxAmountsIn array with maxium amounts spent
     */
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

    /**
     * @dev exitPool
     *      Removes dual side liquidity from the pool (both datatoken and basetoken)
     * @param poolAmountIn amount of pool shares spent
     * @param minAmountsOut array with minimum amount of tokens expected
     */
    function exitPool(uint256 poolAmountIn, uint256[] calldata minAmountsOut)
        external
        _lock_
    {
        require(_finalized, "ERR_NOT_FINALIZED");

        uint256 poolTotal = totalSupply();
        //uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);
        //uint256 pAiAfterExitFee = bsub(poolAmountIn, exitFee);
        
        uint256 ratio = bdiv(poolAmountIn, poolTotal);
        require(ratio != 0, "ERR_MATH_APPROX");

        _pullPoolShare(msg.sender, poolAmountIn);
        //_pushPoolShare(_factory, exitFee);
        _burnPoolShare(poolAmountIn);

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
        emit LOG_BPT(poolAmountIn);
    }

    /**
     * @dev swapExactAmountIn
     *      Swaps an exact amount of tokensIn to get a mimum amount of tokenOut
     * @param tokenInOutMarket array of addreses: [tokenIn, tokenOut, consumeMarketFeeAddress]
     * @param amountsInOutMaxFee array of ints: [tokenAmountIn, minAmountOut, maxPrice, consumeMarketSwapFee]
     */
    function swapExactAmountIn(
        address[3] calldata tokenInOutMarket, 
        uint256[4] calldata amountsInOutMaxFee
    ) external _lock_ returns (uint256 tokenAmountOut, uint256 spotPriceAfter) {
        require(_finalized, "ERR_NOT_FINALIZED");
        _checkBound(tokenInOutMarket[0]);
        _checkBound(tokenInOutMarket[1]);
        Record storage inRecord = _records[address(tokenInOutMarket[0])];
        Record storage outRecord = _records[address(tokenInOutMarket[1])];
        require(amountsInOutMaxFee[3] ==0 || amountsInOutMaxFee[3] >= MIN_FEE,'ConsumeSwapFee too low');
        require(amountsInOutMaxFee[3] <= MAX_FEE,'ConsumeSwapFee too high');
        require(
            amountsInOutMaxFee[0] <= bmul(inRecord.balance, MAX_IN_RATIO),
            "ERR_MAX_IN_RATIO"
        );

        uint256 spotPriceBefore = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm,
            amountsInOutMaxFee[3]
        );

        require(
            spotPriceBefore <= amountsInOutMaxFee[2],
            "ERR_BAD_LIMIT_PRICE"
        );
        uint256 balanceInToAdd;
        uint256[4] memory data = [
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        ];
        swapfees memory _swapfees;
        (tokenAmountOut, balanceInToAdd, _swapfees) = calcOutGivenIn(
            data,
            amountsInOutMaxFee[0],
           // tokenInOutMarket[0],
            amountsInOutMaxFee[3]
        );
        // update balances
        communityFees[tokenInOutMarket[0]] = badd(communityFees[tokenInOutMarket[0]],_swapfees.oceanFeeAmount);
        publishMarketFees[tokenInOutMarket[0]] = 
        badd(publishMarketFees[tokenInOutMarket[0]],_swapfees.publishMarketFeeAmount);
        emit SWAP_FEES(_swapfees.LPFee, _swapfees.oceanFeeAmount,
        _swapfees.publishMarketFeeAmount,_swapfees.consumeMarketFee, tokenInOutMarket[0]);
        require(tokenAmountOut >= amountsInOutMaxFee[1], "ERR_LIMIT_OUT");

        inRecord.balance = badd(inRecord.balance, balanceInToAdd);
        outRecord.balance = bsub(outRecord.balance, tokenAmountOut);

        spotPriceAfter = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm,
            amountsInOutMaxFee[3]
        );

        require(spotPriceAfter >= spotPriceBefore, "ERR_MATH_APPROX");
        require(spotPriceAfter <= amountsInOutMaxFee[2], "ERR_LIMIT_PRICE");

        require(
            spotPriceBefore <= bdiv(amountsInOutMaxFee[0], tokenAmountOut),
            "ERR_MATH_APPROX"
        );

        emit LOG_SWAP(
            msg.sender,
            tokenInOutMarket[0],
            tokenInOutMarket[1],
            amountsInOutMaxFee[0],
            tokenAmountOut,
            block.timestamp
        );

        _pullUnderlying(tokenInOutMarket[0], msg.sender, amountsInOutMaxFee[0]);
        uint256 consumeMarketFeeAmount = bsub(
            amountsInOutMaxFee[0],
            bmul(amountsInOutMaxFee[0], bsub(BONE, amountsInOutMaxFee[3]))
        );
        if (amountsInOutMaxFee[3] > 0) {
            IERC20(tokenInOutMarket[0]).safeTransfer(
                tokenInOutMarket[2],
                consumeMarketFeeAmount
            );
            emit ConsumeMarketFee(
                tokenInOutMarket[2],
                tokenInOutMarket[0],
                consumeMarketFeeAmount
            );
        }
        _pushUnderlying(tokenInOutMarket[1], msg.sender, tokenAmountOut);

        return (tokenAmountOut, spotPriceAfter); //returning spot price 0 because there is no public spotPrice
    }


    /**
     * @dev swapExactAmountOut
     *      Swaps a maximum  maxAmountIn of tokensIn to get an exact amount of tokenOut
     * @param tokenInOutMarket array of addreses: [tokenIn, tokenOut, consumeMarketFeeAddress]
     * @param amountsInOutMaxFee array of ints: [maxAmountIn,tokenAmountOut,maxPrice, consumeMarketSwapFee]
     */
    function swapExactAmountOut(
        address[3] calldata tokenInOutMarket,
        uint256[4] calldata amountsInOutMaxFee
    ) external _lock_ returns (uint256 tokenAmountIn, uint256 spotPriceAfter) {
        require(_finalized, "ERR_NOT_FINALIZED");
        require(amountsInOutMaxFee[3] ==0 || amountsInOutMaxFee[3] >= MIN_FEE,'ConsumeSwapFee too low');
        require(amountsInOutMaxFee[3] <= MAX_FEE,'ConsumeSwapFee too high');
        _checkBound(tokenInOutMarket[0]);
        _checkBound(tokenInOutMarket[1]);
        Record storage inRecord = _records[address(tokenInOutMarket[0])];
        Record storage outRecord = _records[address(tokenInOutMarket[1])];

        require(
            amountsInOutMaxFee[1] <= bmul(outRecord.balance, MAX_OUT_RATIO),
            "ERR_MAX_OUT_RATIO"
        );

        uint256 spotPriceBefore = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm,
            amountsInOutMaxFee[3]
        );

        require(
            spotPriceBefore <= amountsInOutMaxFee[2],
            "ERR_BAD_LIMIT_PRICE"
        );
        // this is the amount we are going to register in balances
        // (only takes account of swapFee, not OPC and market fee,
        //in order to not affect price during following swaps, fee wtihdrawl etc)
        uint256 balanceToAdd;
        uint256[4] memory data = [
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm
        ];
        swapfees memory _swapfees;
        (tokenAmountIn, balanceToAdd,
        _swapfees) = calcInGivenOut(
            data,
            amountsInOutMaxFee[1],
            //tokenInOutMarket[0],
            amountsInOutMaxFee[3]
        );
        communityFees[tokenInOutMarket[0]] = badd(communityFees[tokenInOutMarket[0]],_swapfees.oceanFeeAmount);
        publishMarketFees[tokenInOutMarket[0]] 
        = badd(publishMarketFees[tokenInOutMarket[0]],_swapfees.publishMarketFeeAmount);
        emit SWAP_FEES(_swapfees.LPFee, _swapfees.oceanFeeAmount,
        _swapfees.publishMarketFeeAmount,_swapfees.consumeMarketFee, tokenInOutMarket[0]);
        require(tokenAmountIn <= amountsInOutMaxFee[0], "ERR_LIMIT_IN");

        inRecord.balance = badd(inRecord.balance, balanceToAdd);
        outRecord.balance = bsub(outRecord.balance, amountsInOutMaxFee[1]);

        spotPriceAfter = calcSpotPrice(
            inRecord.balance,
            inRecord.denorm,
            outRecord.balance,
            outRecord.denorm,
            amountsInOutMaxFee[3]
        );

        require(spotPriceAfter >= spotPriceBefore, "ERR_MATH_APPROX");
        require(spotPriceAfter <= amountsInOutMaxFee[2], "ERR_LIMIT_PRICE");
        require(
            spotPriceBefore <= bdiv(tokenAmountIn, amountsInOutMaxFee[1]),
            "ERR_MATH_APPROX"
        );

        emit LOG_SWAP(
            msg.sender,
            tokenInOutMarket[0],
            tokenInOutMarket[1],
            tokenAmountIn,
            amountsInOutMaxFee[1],
            block.timestamp
        );
        _pullUnderlying(tokenInOutMarket[0], msg.sender, tokenAmountIn);
        uint256 consumeMarketFeeAmount = bsub(
            tokenAmountIn,
            bmul(tokenAmountIn, bsub(BONE, amountsInOutMaxFee[3]))
        );
        if (amountsInOutMaxFee[3] > 0) {
            IERC20(tokenInOutMarket[0]).safeTransfer(
                tokenInOutMarket[2],// market address
                consumeMarketFeeAmount
            );
            emit ConsumeMarketFee(
                tokenInOutMarket[2], // to (market address)
                tokenInOutMarket[0], // token
                consumeMarketFeeAmount
            );
        }
        _pushUnderlying(tokenInOutMarket[1], msg.sender, amountsInOutMaxFee[1]);
        return (tokenAmountIn, spotPriceAfter);
    }

    /**
     * @dev joinswapExternAmountIn
     *      Single side add liquidity to the pool,
     *      expecting a minPoolAmountOut of shares for spending tokenAmountIn basetokens
     * @param tokenAmountIn exact number of base tokens to spend
     * @param minPoolAmountOut minimum of pool shares expectex
     */
    function joinswapExternAmountIn(
        uint256 tokenAmountIn,
        uint256 minPoolAmountOut
    ) external _lock_ returns (uint256 poolAmountOut) {
        //tokenIn = _baseTokenAddress;
        require(_finalized, "ERR_NOT_FINALIZED");
        _checkBound(_baseTokenAddress);
        require(
            tokenAmountIn <= bmul(_records[_baseTokenAddress].balance, MAX_IN_RATIO),
            "ERR_MAX_IN_RATIO"
        );
        //ask ssContract
        Record storage inRecord = _records[_baseTokenAddress];

        poolAmountOut = calcPoolOutGivenSingleIn(
            inRecord.balance,
            inRecord.denorm,
            _totalSupply,
            _totalWeight,
            tokenAmountIn
        );

        require(poolAmountOut >= minPoolAmountOut, "ERR_LIMIT_OUT");

        inRecord.balance = badd(inRecord.balance, tokenAmountIn);

        emit LOG_JOIN(msg.sender, _baseTokenAddress, tokenAmountIn, block.timestamp);
        emit LOG_BPT(poolAmountOut);
        _mintPoolShare(poolAmountOut);
        _pushPoolShare(msg.sender, poolAmountOut);

        _pullUnderlying(_baseTokenAddress, msg.sender, tokenAmountIn);

        //ask the ssContract to stake as well
        //calculate how much should the 1ss stake
        Record storage ssInRecord = _records[_datatokenAddress];
        uint256 ssAmountIn = calcSingleInGivenPoolOut(
            ssInRecord.balance,
            ssInRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountOut
        );
        if (ssContract.canStake(_datatokenAddress, ssAmountIn)) {
            //call 1ss to approve
            ssContract.Stake(_datatokenAddress, ssAmountIn);
            // follow the same path
            ssInRecord.balance = badd(ssInRecord.balance, ssAmountIn);
            emit LOG_JOIN(
                _controller,
                _datatokenAddress,
                ssAmountIn,
                block.timestamp
            );
            emit LOG_BPT_SS(poolAmountOut);
            _mintPoolShare(poolAmountOut);
            _pushPoolShare(_controller, poolAmountOut);
            _pullUnderlying(_datatokenAddress, _controller, ssAmountIn);
        }
        return poolAmountOut;
    }

    
    /**
     * @dev exitswapPoolAmountIn
     *      Single side remove liquidity from the pool,
     *      expecting a minAmountOut of basetokens for spending poolAmountIn pool shares
     * @param poolAmountIn exact number of pool shares to spend
     * @param minAmountOut minimum amount of basetokens expected
     */
    function exitswapPoolAmountIn(
        uint256 poolAmountIn,
        uint256 minAmountOut
    ) external _lock_ returns (uint256 tokenAmountOut) {
        //tokenOut = _baseTokenAddress;
        require(_finalized, "ERR_NOT_FINALIZED");
        _checkBound(_baseTokenAddress);

        Record storage outRecord = _records[_baseTokenAddress];

        tokenAmountOut = calcSingleOutGivenPoolIn(
            outRecord.balance,
            outRecord.denorm,
            _totalSupply,
            _totalWeight,
            poolAmountIn
        );

        require(tokenAmountOut >= minAmountOut, "ERR_LIMIT_OUT");

        require(
            tokenAmountOut <= bmul(_records[_baseTokenAddress].balance, MAX_OUT_RATIO),
            "ERR_MAX_OUT_RATIO"
        );

        outRecord.balance = bsub(outRecord.balance, tokenAmountOut);

        //uint256 exitFee = bmul(poolAmountIn, EXIT_FEE);

        emit LOG_EXIT(msg.sender, _baseTokenAddress, tokenAmountOut, block.timestamp);
        emit LOG_BPT(poolAmountIn);

        _pullPoolShare(msg.sender, poolAmountIn);

        //_burnPoolShare(bsub(poolAmountIn, exitFee));
        _burnPoolShare(poolAmountIn);
        //_pushPoolShare(_factory, exitFee);
        _pushUnderlying(_baseTokenAddress, msg.sender, tokenAmountOut);

        //ask the ssContract to unstake as well
        //calculate how much should the 1ss unstake
        
        if (
            ssContract.canUnStake(_datatokenAddress, poolAmountIn)
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
            //exitFee = bmul(poolAmountIn, EXIT_FEE);
            emit LOG_EXIT(
                _controller,
                _datatokenAddress,
                ssAmountOut,
                block.timestamp
            );
            _pullPoolShare(_controller, poolAmountIn);
            //_burnPoolShare(bsub(poolAmountIn, exitFee));
            _burnPoolShare(poolAmountIn);
            //_pushPoolShare(_factory, exitFee);
            _pushUnderlying(_datatokenAddress, _controller, ssAmountOut);
            //call unstake on 1ss to do cleanup on their side
            ssContract.UnStake(
                _datatokenAddress,
                ssAmountOut,
                poolAmountIn
            );
            emit LOG_BPT_SS(poolAmountIn);
        }
        return tokenAmountOut;
    }

    

    /**
     * @dev calcSingleOutPoolIn
     *      Returns expected amount of tokenOut for removing exact poolAmountIn pool shares from the pool
     * @param tokenOut tokenOut
     * @param poolAmountIn amount of shares spent
     */
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

    /**
     * @dev calcPoolInSingleOut
     *      Returns number of poolshares needed to withdraw exact tokenAmountOut tokens
     * @param tokenOut tokenOut
     * @param tokenAmountOut expected amount of tokensOut
     */
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

    /**
     * @dev calcSingleInPoolOut
     *      Returns number of tokens to be staked to the pool in order to get an exact number of poolshares
     * @param tokenIn tokenIn
     * @param poolAmountOut expected amount of pool shares
     */
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

    /**
     * @dev calcPoolOutSingleIn
     *      Returns number of poolshares obtain by staking exact tokenAmountIn tokens
     * @param tokenIn tokenIn
     * @param tokenAmountIn exact number of tokens staked
     */
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


    // Internal functions below

    // ==
    // 'Underlying' token-manipulation functions make external calls but are NOT locked
    // You must `_lock_` or otherwise ensure reentry-safety
    function _pullUnderlying(
        address erc20,
        address from,
        uint256 amount
    ) internal {
        uint256 balanceBefore = IERC20(erc20).balanceOf(address(this));
        IERC20(erc20).safeTransferFrom(from, address(this), amount);
        require(IERC20(erc20).balanceOf(address(this)) >= balanceBefore + amount,
                    "Transfer amount is too low");
        //require(xfer, "ERR_ERC20_FALSE");
    }

    function _pushUnderlying(
        address erc20,
        address to,
        uint256 amount
    ) internal {
        IERC20(erc20).safeTransfer(to, amount);
        //require(xfer, "ERR_ERC20_FALSE");
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
