pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "./balancer/BFactory.sol";
import "../interfaces/IFactory.sol";
import "../interfaces/IERC20.sol";
import "../interfaces/IFixedRateExchange.sol";
import "../interfaces/IPool.sol";
import "../interfaces/IDispenser.sol";
import "../utils/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/math/SafeMath.sol";

contract FactoryRouter is BFactory {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;
    address public routerOwner;
    address public factory;
    address public fixedRate;
    uint256 public minVestingPeriodInBlocks = 2426000;

    uint256 public swapOceanFee = 0;
    uint256 public swapNonOceanFee = 1e15;  // 0.1%
    uint256 public consumeFee = 1e16; // 1%
    uint256 public providerFee = 0; // 0%
    address[] public oceanTokens;
    address[] public ssContracts;
    address[] public fixedrates;
    address[] public dispensers;
    // mapping(address => bool) public oceanTokens;
    // mapping(address => bool) public ssContracts;
    // mapping(address => bool) public fixedPrice;
    // mapping(address => bool) public dispenser;

    event NewPool(address indexed poolAddress, bool isOcean);
    event VestingPeriodChanges(address indexed caller, uint256 minVestingPeriodInBlocks);
    event RouterChanged(address indexed caller, address indexed newRouter);
    event FactoryContractChanged(
        address indexed caller,
        address indexed contractAddress
    );
    event TokenAdded(address indexed caller, address indexed token);
    event TokenRemoved(address indexed caller, address indexed token);
    event SSContractAdded(
        address indexed caller,
        address indexed contractAddress
    );
    event SSContractRemoved(
        address indexed caller,
        address indexed contractAddress
    );
    event FixedRateContractAdded(
        address indexed caller,
        address indexed contractAddress
    );
    event FixedRateContractRemoved(
        address indexed caller,
        address indexed contractAddress
    );
    event DispenserContractAdded(
        address indexed caller,
        address indexed contractAddress
    );
    event DispenserContractRemoved(
        address indexed caller,
        address indexed contractAddress
    );

    event OPCFeeChanged(address indexed caller, uint256 newSwapOceanFee,
        uint256 newSwapNonOceanFee, uint256 newConsumeFee, uint256 newProviderFee);

    modifier onlyRouterOwner() {
        require(routerOwner == msg.sender, "OceanRouter: NOT OWNER");
        _;
    }

    constructor(
        address _routerOwner,
        address _oceanToken,
        address _bpoolTemplate,
        address _opcCollector,
        address[] memory _preCreatedPools
    ) public BFactory(_bpoolTemplate, _opcCollector, _preCreatedPools) {
        require(
            _routerOwner != address(0),
            "FactoryRouter: Invalid router owner"
        );
        require(
            _opcCollector != address(0),
            "FactoryRouter: Invalid opcCollector"
        );
        require(
            _oceanToken != address(0),
            "FactoryRouter: Invalid Ocean Token address"
        );
        routerOwner = _routerOwner;
        opcCollector = _opcCollector;
        _addOceanToken(_oceanToken);
    }

    function changeRouterOwner(address _routerOwner) external onlyRouterOwner {
        require(_routerOwner != address(0), "Invalid new router owner");
        routerOwner = _routerOwner;
        emit RouterChanged(msg.sender, _routerOwner);
    }

    /**
     * @dev addOceanToken
     *      Adds a token to the list of tokens with reduced fees
     *  @param oceanTokenAddress address Token to be added
     */
    function addOceanToken(address oceanTokenAddress) external onlyRouterOwner {
        _addOceanToken(oceanTokenAddress);
    }
    
    function _addOceanToken(address oceanTokenAddress) internal {
        if(!isOceanToken(oceanTokenAddress)){
            oceanTokens.push(oceanTokenAddress);
            emit TokenAdded(msg.sender, oceanTokenAddress);
        }
    }

    /**
     * @dev removeOceanToken
     *      Removes a token if exists from the list of tokens with reduced fees
     *  @param oceanTokenAddress address Token to be removed
     */
    function removeOceanToken(address oceanTokenAddress)
        external
        onlyRouterOwner
    {
        require(
            oceanTokenAddress != address(0),
            "FactoryRouter: Invalid Ocean Token address"
        );
        uint256 i;
        for (i = 0; i < oceanTokens.length; i++) {
            if(oceanTokens[i] == oceanTokenAddress) break;
        }
        if(i < oceanTokens.length){
            // it's in the array
            for (uint c = i; c < oceanTokens.length - 1; c++) {
                    oceanTokens[c] = oceanTokens[c + 1];
            }
            oceanTokens.pop();
            emit TokenRemoved(msg.sender, oceanTokenAddress);
        }
    }
    /**
     * @dev isOceanToken
     *      Returns true if token exists in the list of tokens with reduced fees
     *  @param oceanTokenAddress address Token to be checked
     */
    function isOceanToken(address oceanTokenAddress) public view returns(bool) {
        for (uint256 i = 0; i < oceanTokens.length; i++) {
            if(oceanTokens[i] == oceanTokenAddress) return true;
        }
        return false;
    }
    /**
     * @dev getOceanTokens
     *      Returns the list of tokens with reduced fees
     */
    function getOceanTokens() public view returns(address[] memory) {
        return(oceanTokens);
    }


     /**
     * @dev addSSContract
     *      Adds a token to the list of ssContracts
     *  @param _ssContract address Contract to be added
     */

    function addSSContract(address _ssContract) external onlyRouterOwner {
        require(
            _ssContract != address(0),
            "FactoryRouter: Invalid _ssContract address"
        );
        if(!isSSContract(_ssContract)){
            ssContracts.push(_ssContract);
            emit SSContractAdded(msg.sender, _ssContract);
        }
    }
    /**
     * @dev removeSSContract
     *      Removes a token if exists from the list of ssContracts
     *  @param _ssContract address Contract to be removed
     */

    function removeSSContract(address _ssContract) external onlyRouterOwner {
        require(
            _ssContract != address(0),
            "FactoryRouter: Invalid _ssContract address"
        );
        uint256 i;
        for (i = 0; i < ssContracts.length; i++) {
            if(ssContracts[i] == _ssContract) break;
        }
        if(i < ssContracts.length){
            // it's in the array
            for (uint c = i; c < ssContracts.length - 1; c++) {
                    ssContracts[c] = ssContracts[c + 1];
            }
            ssContracts.pop();
            emit SSContractRemoved(msg.sender, _ssContract);
        }
    }

    /**
     * @dev isSSContract
     *      Returns true if token exists in the list of ssContracts
     *  @param _ssContract  address Contract to be checked
     */
    function isSSContract(address _ssContract) public view returns(bool) {
        for (uint256 i = 0; i < ssContracts.length; i++) {
            if(ssContracts[i] == _ssContract) return true;
        }
        return false;
    }
    /**
     * @dev getSSContracts
     *      Returns the list of ssContracts
     */
    function getSSContracts() public view returns(address[] memory) {
        return(ssContracts);
    }

    function addFactory(address _factory) external onlyRouterOwner {
        require(
            _factory != address(0),
            "FactoryRouter: Invalid _factory address"
        );
        require(factory == address(0), "FACTORY ALREADY SET");
        factory = _factory;
        emit FactoryContractChanged(msg.sender, _factory);
    }


    /**
     * @dev addFixedRateContract
     *      Adds an address to the list of fixed rate contracts
     *  @param _fixedRate address Contract to be added
     */
    function addFixedRateContract(address _fixedRate) external onlyRouterOwner {
        require(
            _fixedRate != address(0),
            "FactoryRouter: Invalid _fixedRate address"
        );
        if(!isFixedRateContract(_fixedRate)){
            fixedrates.push(_fixedRate);
            emit FixedRateContractAdded(msg.sender, _fixedRate);
        }
    }
     /**
     * @dev removeFixedRateContract
     *      Removes an address from the list of fixed rate contracts
     *  @param _fixedRate address Contract to be removed
     */
    function removeFixedRateContract(address _fixedRate)
        external
        onlyRouterOwner
    {
        require(
            _fixedRate != address(0),
            "FactoryRouter: Invalid _fixedRate address"
        );
        uint256 i;
        for (i = 0; i < fixedrates.length; i++) {
            if(fixedrates[i] == _fixedRate) break;
        }
        if(i < fixedrates.length){
            // it's in the array
            for (uint c = i; c < fixedrates.length - 1; c++) {
                    fixedrates[c] = fixedrates[c + 1];
            }
            fixedrates.pop();
            emit FixedRateContractRemoved(msg.sender, _fixedRate);
        }
    }
    /**
     * @dev isFixedRateContract
     *      Removes true if address exists in the list of fixed rate contracts
     *  @param _fixedRate address Contract to be checked
     */
    function isFixedRateContract(address _fixedRate) public view returns(bool) {
        for (uint256 i = 0; i < fixedrates.length; i++) {
            if(fixedrates[i] == _fixedRate) return true;
        }
        return false;
    }
    /**
     * @dev getFixedRatesContracts
     *      Returns the list of fixed rate contracts
     */
    function getFixedRatesContracts() public view returns(address[] memory) {
        return(fixedrates);
    }

    /**
     * @dev addDispenserContract
     *      Adds an address to the list of dispensers
     *  @param _dispenser address Contract to be added
     */
    function addDispenserContract(address _dispenser) external onlyRouterOwner {
        require(
            _dispenser != address(0),
            "FactoryRouter: Invalid _dispenser address"
        );
          if(!isDispenserContract(_dispenser)){
            dispensers.push(_dispenser);
            emit DispenserContractAdded(msg.sender, _dispenser);
        }
    }

    /**
     * @dev removeDispenserContract
     *      Removes an address from the list of dispensers
     *  @param _dispenser address Contract to be removed
     */
    function removeDispenserContract(address _dispenser)
        external
        onlyRouterOwner
    {
        require(
            _dispenser != address(0),
            "FactoryRouter: Invalid _dispenser address"
        );
        uint256 i;
        for (i = 0; i < dispensers.length; i++) {
            if(dispensers[i] == _dispenser) break;
        }
        if(i < dispensers.length){
            // it's in the array
            for (uint c = i; c < dispensers.length - 1; c++) {
                    dispensers[c] = dispensers[c + 1];
            }
            dispensers.pop();
            emit DispenserContractRemoved(msg.sender, _dispenser);
        }
    }
    /**
     * @dev isDispenserContract
     *      Returns true if address exists in the list of dispensers
     *  @param _dispenser  address Contract to be checked
     */
    function isDispenserContract(address _dispenser) public view returns(bool) {
        for (uint256 i = 0; i < dispensers.length; i++) {
            if(dispensers[i] == _dispenser) return true;
        }
        return false;
    }
    /**
     * @dev getDispensersContracts
     *      Returns the list of fixed rate contracts
     */
    function getDispensersContracts() public view returns(address[] memory) {
        return(dispensers);
    }

    /**
     * @dev getOPCFee
     *      Gets OP Community Fees for a particular token
     * @param baseToken  address token to be checked
     */
    function getOPCFee(address baseToken) public view returns (uint256) {
        if (isOceanToken(baseToken)) {
            return swapOceanFee;
        } else return swapNonOceanFee;
    }

    /**
     * @dev getOPCFees
     *      Gets OP Community Fees for approved tokens and non approved tokens
     */
    function getOPCFees() public view returns (uint256,uint256) {
        return (swapOceanFee, swapNonOceanFee);
    }

    /**
     * @dev getConsumeFee
     *      Gets OP Community Fee cuts for consume fees
     */
    function getOPCConsumeFee() public view returns (uint256) {
        return consumeFee;
    }

    /**
     * @dev getOPCProviderFee
     *      Gets OP Community Fee cuts for provider fees
     */
    function getOPCProviderFee() public view returns (uint256) {
        return providerFee;
    }


    /**
     * @dev updateOPCFee
     *      Updates OP Community Fees
     * @param _newSwapOceanFee Amount charged for swapping with ocean approved tokens
     * @param _newSwapNonOceanFee Amount charged for swapping with non ocean approved tokens
     * @param _newConsumeFee Amount charged from consumeFees
     * @param _newProviderFee Amount charged for providerFees
     */
    function updateOPCFee(uint256 _newSwapOceanFee, uint256 _newSwapNonOceanFee,
        uint256 _newConsumeFee, uint256 _newProviderFee) external onlyRouterOwner {

        swapOceanFee = _newSwapOceanFee;
        swapNonOceanFee = _newSwapNonOceanFee;
        consumeFee = _newConsumeFee;
        providerFee = _newProviderFee;
        emit OPCFeeChanged(msg.sender, _newSwapOceanFee, _newSwapNonOceanFee, _newConsumeFee, _newProviderFee);
    }

    /*
     * @dev getMinVestingPeriod
     *      Returns current minVestingPeriodInBlocks
       @return minVestingPeriodInBlocks
     */
    function getMinVestingPeriod() public view returns (uint256) {
        return minVestingPeriodInBlocks;
    }
    /*
     * @dev updateMinVestingPeriod
     *      Set new minVestingPeriodInBlocks
     * @param _newPeriod
     */
    function updateMinVestingPeriod(uint256 _newPeriod) external onlyRouterOwner {
        minVestingPeriodInBlocks = _newPeriod;
        emit VestingPeriodChanges(msg.sender, _newPeriod);
    }
    /**
     * @dev Deploys a new `OceanPool` on Ocean Friendly Fork modified for 1SS.
     This function cannot be called directly, but ONLY through the ERC20DT contract from a ERC20DEployer role

      ssContract address
     tokens [datatokenAddress, baseTokenAddress]
     publisherAddress user which will be assigned the vested amount.
     * @param tokens precreated parameter
     * @param ssParams params for the ssContract. 
     *                     [0]  = rate (wei)
     *                     [1]  = baseToken decimals
     *                     [2]  = vesting amount (wei)
     *                     [3]  = vested blocks
     *                     [4]  = initial liquidity in baseToken for pool creation
     * @param swapFees swapFees (swapFee, swapMarketFee), swapOceanFee will be set automatically later
     *                     [0] = swapFee for LP Providers
     *                     [1] = swapFee for marketplace runner
      
      .
     * @param addresses refers to an array of addresses passed by user
     *                     [0]  = side staking contract address
     *                     [1]  = baseToken address for pool creation(OCEAN or other)
     *                     [2]  = baseTokenSender user which will provide the baseToken amount for initial liquidity
     *                     [3]  = publisherAddress user which will be assigned the vested amount
     *                     [4]  = marketFeeCollector marketFeeCollector address
                           [5]  = poolTemplateAddress
       
        @return pool address
     */
    function deployPool(
        address[2] calldata tokens,
        // [datatokenAddress, baseTokenAddress]
        uint256[] calldata ssParams,
        uint256[] calldata swapFees,
        address[] calldata addresses
    )
        external
        returns (
            //[controller,baseTokenAddress,baseTokenSender,publisherAddress, marketFeeCollector,poolTemplateAddress]

            address
        )
    {
        require(
            IFactory(factory).erc20List(msg.sender),
            "FACTORY ROUTER: NOT ORIGINAL ERC20 TEMPLATE"
        );
        require(isSSContract(addresses[0]),
            "FACTORY ROUTER: invalid ssContract"
        );
        require(ssParams[1] > 0, "Wrong decimals");

        // we pull baseToken for creating initial pool and send it to the controller (ssContract)
        _pullUnderlying(tokens[1],addresses[2], addresses[0], ssParams[4]);
        
        address pool = newBPool(tokens, ssParams, swapFees, addresses);
        require(pool != address(0), "FAILED TO DEPLOY POOL");
        if (isOceanToken(tokens[1])) emit NewPool(pool, true);
        else emit NewPool(pool, false);
        return pool;
    }

    function getLength(IERC20[] memory array) internal pure returns (uint256) {
        return array.length;
    }

    /**
     * @dev deployFixedRate
     *      Creates a new FixedRateExchange setup.
     * As for deployPool, this function cannot be called directly,
     * but ONLY through the ERC20DT contract from a ERC20DEployer role
     * @param fixedPriceAddress fixedPriceAddress
     * @param addresses array of addresses [baseToken,owner,marketFeeCollector]
     * @param uints array of uints [baseTokenDecimals,datatokenDecimals, fixedRate, marketFee, withMint]
       @return exchangeId
     */

    function deployFixedRate(
        address fixedPriceAddress,
        address[] calldata addresses,
        uint256[] calldata uints
    ) external returns (bytes32 exchangeId) {
        require(
            IFactory(factory).erc20List(msg.sender),
            "FACTORY ROUTER: NOT ORIGINAL ERC20 TEMPLATE"
        );

        require(isFixedRateContract(fixedPriceAddress),
            "FACTORY ROUTER: Invalid FixedPriceContract"
        );

        exchangeId = IFixedRateExchange(fixedPriceAddress).createWithDecimals(
            msg.sender,
            addresses,
            uints
        );
    }

    /**
     * @dev deployDispenser
     *      Activates a new Dispenser
     * As for deployPool, this function cannot be called directly,
     * but ONLY through the ERC20DT contract from a ERC20DEployer role
     * @param _dispenser dispenser contract address
     * @param datatoken refers to datatoken address.
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     * @param owner - owner
     * @param allowedSwapper - if !=0, only this address can request DTs
     */

    function deployDispenser(
        address _dispenser,
        address datatoken,
        uint256 maxTokens,
        uint256 maxBalance,
        address owner,
        address allowedSwapper
    ) external {
        require(
            IFactory(factory).erc20List(msg.sender),
            "FACTORY ROUTER: NOT ORIGINAL ERC20 TEMPLATE"
        );

        require(isDispenserContract(_dispenser),
            "FACTORY ROUTER: Invalid DispenserContract"
        );
        IDispenser(_dispenser).create(
            datatoken,
            maxTokens,
            maxBalance,
            owner,
            allowedSwapper
        );
    }

     /**
     * @dev addPoolTemplate
     *      Adds an address to the list of pools templates
     *  @param poolTemplate address Contract to be added
     */
    function addPoolTemplate(address poolTemplate) external onlyRouterOwner {
        _addPoolTemplate(poolTemplate);
    }
     /**
     * @dev removePoolTemplate
     *      Removes an address from the list of pool templates
     *  @param poolTemplate address Contract to be removed
     */
    function removePoolTemplate(address poolTemplate) external onlyRouterOwner {
        _removePoolTemplate(poolTemplate);
    }

    // If you need to buy multiple DT (let's say for a compute job which has multiple datasets),
    // you have to send one transaction for each DT that you want to buy.

    // Perks:

    // one single call to buy multiple DT for multiple assets (better UX, better gas optimization)

    enum operationType {
        SwapExactIn,
        SwapExactOut,
        FixedRate,
        Dispenser
    }

    struct Operations {
        bytes32 exchangeIds; // used for fixedRate or dispenser
        address source; // pool, dispenser or fixed rate address
        operationType operation; // type of operation: enum operationType
        address tokenIn; // token in address, only for pools
        uint256 amountsIn; // ExactAmount In for swapExactIn operation, maxAmount In for swapExactOut
        address tokenOut; // token out address, only for pools
        uint256 amountsOut; // minAmountOut for swapExactIn or exactAmountOut for swapExactOut
        uint256 maxPrice; // maxPrice, only for pools
        uint256 swapMarketFee;
        address marketFeeAddress;
    }

    // require tokenIn approvals for router from user. (except for dispenser operations)
    function buyDTBatch(Operations[] calldata _operations) external {
        // TODO: to avoid DOS attack, we set a limit to maximum orders (50?)
        require(_operations.length <= 50, "FactoryRouter: Too Many Operations");
        for (uint256 i = 0; i < _operations.length; i++) {
            // address[] memory tokenInOutMarket = new address[](3);
            address[3] memory tokenInOutMarket = [
                _operations[i].tokenIn,
                _operations[i].tokenOut,
                _operations[i].marketFeeAddress
            ];
            uint256[4] memory amountsInOutMaxFee = [
                _operations[i].amountsIn,
                _operations[i].amountsOut,
                _operations[i].maxPrice,
                _operations[i].swapMarketFee
            ];

            // tokenInOutMarket[0] =
            if (_operations[i].operation == operationType.SwapExactIn) {
                // Get amountIn from user to router
                _pullUnderlying(_operations[i].tokenIn,msg.sender,
                    address(this),
                    _operations[i].amountsIn);
                // we approve pool to pull token from router
                IERC20(_operations[i].tokenIn).safeIncreaseAllowance(
                    _operations[i].source,
                    _operations[i].amountsIn
                );

                // Perform swap
                (uint256 amountReceived, ) = IPool(_operations[i].source)
                    .swapExactAmountIn(tokenInOutMarket, amountsInOutMaxFee);
                // transfer token swapped to user

                IERC20(_operations[i].tokenOut).safeTransfer(
                    msg.sender,
                    amountReceived
                );
            } else if (_operations[i].operation == operationType.SwapExactOut) {
                // calculate how much amount In we need for exact Out
                uint256 amountIn;
                (amountIn, , , , ) = IPool(_operations[i].source)
                    .getAmountInExactOut(
                        _operations[i].tokenIn,
                        _operations[i].tokenOut,
                        _operations[i].amountsOut,
                        _operations[i].swapMarketFee
                    );
                // pull amount In from user
                _pullUnderlying(_operations[i].tokenIn,msg.sender,
                    address(this),
                    amountIn);
                // we approve pool to pull token from router
                IERC20(_operations[i].tokenIn).safeIncreaseAllowance(
                    _operations[i].source,
                    amountIn
                );
                // perform swap
                (uint tokenAmountIn,) = IPool(_operations[i].source).swapExactAmountOut(
                    tokenInOutMarket,
                    amountsInOutMaxFee
                );
                require(tokenAmountIn <= amountsInOutMaxFee[0], 'TOO MANY TOKENS IN');
                // send amount out back to user
                IERC20(_operations[i].tokenOut).safeTransfer(
                    msg.sender,
                    _operations[i].amountsOut
                );
            } else if (_operations[i].operation == operationType.FixedRate) {
                // get datatoken address
                (, address datatoken, , , , , , , , , , ) = IFixedRateExchange(
                    _operations[i].source
                ).getExchange(_operations[i].exchangeIds);
                // get tokenIn amount required for dt out
                (uint256 baseTokenAmount, , , ) = IFixedRateExchange(
                    _operations[i].source
                ).calcBaseInGivenOutDT(
                        _operations[i].exchangeIds,
                        _operations[i].amountsOut,
                        _operations[i].swapMarketFee
                    );

                // pull tokenIn amount
                _pullUnderlying(_operations[i].tokenIn,msg.sender,
                    address(this),
                    baseTokenAmount);
                // we approve pool to pull token from router
                IERC20(_operations[i].tokenIn).safeIncreaseAllowance(
                    _operations[i].source,
                    baseTokenAmount
                );
                // perform swap
                IFixedRateExchange(_operations[i].source).buyDT(
                    _operations[i].exchangeIds,
                    _operations[i].amountsOut,
                    _operations[i].amountsIn,
                    _operations[i].marketFeeAddress,
                    _operations[i].swapMarketFee
                );
                // send dt out to user
                IERC20(datatoken).safeTransfer(
                    msg.sender,
                    _operations[i].amountsOut
                );
            } else {
                IDispenser(_operations[i].source).dispense(
                    _operations[i].tokenOut,
                    _operations[i].amountsOut,
                    msg.sender
                );
            }
        }
    }

    struct Stakes {
        address poolAddress;
        uint256 tokenAmountIn;
        uint256 minPoolAmountOut;
    }
    // require pool[].baseToken (for each pool) approvals for router from user.
    function stakeBatch(Stakes[] calldata _stakes) external {
        // TODO: to avoid DOS attack, we set a limit to maximum orders (50?)
        require(_stakes.length <= 50, "FactoryRouter: Too Many Operations");
        for (uint256 i = 0; i < _stakes.length; i++) {
            address baseToken = IPool(_stakes[i].poolAddress).getBaseTokenAddress();
            _pullUnderlying(baseToken,msg.sender,
                    address(this),
                    _stakes[i].tokenAmountIn);
            uint256 balanceBefore = IERC20(_stakes[i].poolAddress).balanceOf(address(this));
            // we approve pool to pull token from router
            IERC20(baseToken).safeIncreaseAllowance(
                    _stakes[i].poolAddress,
                    _stakes[i].tokenAmountIn);
            //now stake
            uint poolAmountOut = IPool(_stakes[i].poolAddress).joinswapExternAmountIn(
                _stakes[i].tokenAmountIn, _stakes[i].minPoolAmountOut
                );
            require(poolAmountOut >=  _stakes[i].minPoolAmountOut,'NOT ENOUGH LP');
            uint256 balanceAfter = IERC20(_stakes[i].poolAddress).balanceOf(address(this));
            //send LP shares to user
            IERC20(_stakes[i].poolAddress).safeTransfer(
                    msg.sender,
                    balanceAfter.sub(balanceBefore)
                );
        }
    }
    
    function _pullUnderlying(
        address erc20,
        address from,
        address to,
        uint256 amount
    ) internal {
        uint256 balanceBefore = IERC20(erc20).balanceOf(to);
        IERC20(erc20).safeTransferFrom(from, to, amount);
        require(IERC20(erc20).balanceOf(to) >= balanceBefore.add(amount),
                    "Transfer amount is too low");
    }
}
