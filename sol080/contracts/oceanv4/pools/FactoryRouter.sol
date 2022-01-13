// SPDX-License-Identifier: Unknown
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

pragma solidity 0.8.10;

import "./balancer/BFactory.sol";
import "../interfaces/IFactory.sol";
import "../interfaces/IERC20.sol";
import "../interfaces/IFixedRateExchange.sol";
import "../interfaces/IPool.sol";
import "../interfaces/IDispenser.sol";
import "../utils/SafeERC20.sol";
import "../hardhat/console.sol";

contract FactoryRouter is BFactory {
    using SafeERC20 for IERC20;
    address public routerOwner;
    address public factory;
    address public fixedRate;
    uint256 public minVestingPeriodInBlocks = 2426000;

    uint256 public swapOceanFee = 1e15;
    mapping(address => bool) public oceanTokens;
    mapping(address => bool) public ssContracts;
    mapping(address => bool) public fixedPrice;
    mapping(address => bool) public dispenser;

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

    event PoolTemplateAdded(
        address indexed caller,
        address indexed contractAddress
    );
    event PoolTemplateRemoved(
        address indexed caller,
        address indexed contractAddress
    );

    event OPFFeeChanged(address indexed caller, uint256 newFee);

    modifier onlyRouterOwner() {
        require(routerOwner == msg.sender, "OceanRouter: NOT OWNER");
        _;
    }

    constructor(
        address _routerOwner,
        address _oceanToken,
        address _bpoolTemplate,
        address _opfCollector,
        address[] memory _preCreatedPools
    ) public BFactory(_bpoolTemplate, _opfCollector, _preCreatedPools) {
        require(
            _routerOwner != address(0),
            "FactoryRouter: Invalid router owner"
        );
        require(
            _opfCollector != address(0),
            "FactoryRouter: Invalid opfCollector"
        );
        require(
            _oceanToken != address(0),
            "FactoryRouter: Invalid Ocean Token address"
        );
        routerOwner = _routerOwner;
        opfCollector = _opfCollector;
        oceanTokens[_oceanToken] = true;
    }

    function changeRouterOwner(address _routerOwner) external onlyRouterOwner {
        require(_routerOwner != address(0), "Invalid new router owner");
        routerOwner = _routerOwner;
        emit RouterChanged(msg.sender, _routerOwner);
    }

    function addOceanToken(address oceanTokenAddress) external onlyRouterOwner {
        require(
            oceanTokenAddress != address(0),
            "FactoryRouter: Invalid Ocean Token address"
        );
        oceanTokens[oceanTokenAddress] = true;
        emit TokenAdded(msg.sender, oceanTokenAddress);
    }

    function removeOceanToken(address oceanTokenAddress)
        external
        onlyRouterOwner
    {
        require(
            oceanTokenAddress != address(0),
            "FactoryRouter: Invalid Ocean Token address"
        );
        oceanTokens[oceanTokenAddress] = false;
        emit TokenRemoved(msg.sender, oceanTokenAddress);
    }

    function addSSContract(address _ssContract) external onlyRouterOwner {
        require(
            _ssContract != address(0),
            "FactoryRouter: Invalid _ssContract address"
        );
        ssContracts[_ssContract] = true;
        emit SSContractAdded(msg.sender, _ssContract);
    }

    function removeSSContract(address _ssContract) external onlyRouterOwner {
        require(
            _ssContract != address(0),
            "FactoryRouter: Invalid _ssContract address"
        );
        ssContracts[_ssContract] = false;
        emit SSContractRemoved(msg.sender, _ssContract);
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

    function addFixedRateContract(address _fixedRate) external onlyRouterOwner {
        require(
            _fixedRate != address(0),
            "FactoryRouter: Invalid _fixedRate address"
        );
        fixedPrice[_fixedRate] = true;
        emit FixedRateContractAdded(msg.sender, _fixedRate);
    }

    function removeFixedRateContract(address _fixedRate)
        external
        onlyRouterOwner
    {
        require(
            _fixedRate != address(0),
            "FactoryRouter: Invalid _fixedRate address"
        );
        fixedPrice[_fixedRate] = false;
        emit FixedRateContractRemoved(msg.sender, _fixedRate);
    }

    function addDispenserContract(address _dispenser) external onlyRouterOwner {
        require(
            _dispenser != address(0),
            "FactoryRouter: Invalid _dispenser address"
        );
        dispenser[_dispenser] = true;
        emit DispenserContractAdded(msg.sender, _dispenser);
    }

    function removeDispenserContract(address _dispenser)
        external
        onlyRouterOwner
    {
        require(
            _dispenser != address(0),
            "FactoryRouter: Invalid _dispenser address"
        );
        dispenser[_dispenser] = false;
        emit DispenserContractRemoved(msg.sender, _dispenser);
    }

    function getOPFFee(address baseToken) public view returns (uint256) {
        if (oceanTokens[baseToken]) {
            return 0;
        } else return swapOceanFee;
    }

    function updateOPFFee(uint256 _newSwapOceanFee) external onlyRouterOwner {
        // TODO: add a maximum? how much? add event?
        swapOceanFee = _newSwapOceanFee;
        emit OPFFeeChanged(msg.sender, _newSwapOceanFee);
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
     tokens [datatokenAddress, basetokenAddress]
     publisherAddress user which will be assigned the vested amount.
     * @param tokens precreated parameter
     * @param ssParams params for the ssContract. 
     *                     [0]  = rate (wei)
     *                     [1]  = basetoken decimals
     *                     [2]  = vesting amount (wei)
     *                     [3]  = vested blocks
     *                     [4]  = initial liquidity in basetoken for pool creation
     * @param swapFees swapFees (swapFee, swapMarketFee), swapOceanFee will be set automatically later
     *                     [0] = swapFee for LP Providers
     *                     [1] = swapFee for marketplace runner
      
      .
     * @param addresses refers to an array of addresses passed by user
     *                     [0]  = side staking contract address
     *                     [1]  = basetoken address for pool creation(OCEAN or other)
     *                     [2]  = basetokenSender user which will provide the baseToken amount for initial liquidity
     *                     [3]  = publisherAddress user which will be assigned the vested amount
     *                     [4]  = marketFeeCollector marketFeeCollector address
                           [5]  = poolTemplateAddress
       
        @return pool address
     */
    function deployPool(
        address[2] calldata tokens,
        // [datatokenAddress, basetokenAddress]
        uint256[] calldata ssParams,
        uint256[] calldata swapFees,
        address[] calldata addresses
    )
        external
        returns (
            //[controller,basetokenAddress,basetokenSender,publisherAddress, marketFeeCollector,poolTemplateAddress]

            address
        )
    {
        require(
            IFactory(factory).erc20List(msg.sender),
            "FACTORY ROUTER: NOT ORIGINAL ERC20 TEMPLATE"
        );
        require(
            ssContracts[addresses[0]],
            "FACTORY ROUTER: invalid ssContract"
        );
        require(ssParams[1] > 0, "Wrong decimals");

        // we pull basetoken for creating initial pool and send it to the controller (ssContract)
        IERC20 bt = IERC20(tokens[1]);
        bt.safeTransferFrom(addresses[2], addresses[0], ssParams[4]);

        address pool = newBPool(tokens, ssParams, swapFees, addresses);

        require(pool != address(0), "FAILED TO DEPLOY POOL");
        if (oceanTokens[tokens[1]]) emit NewPool(pool, true);
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
     * @param uints array of uints [baseTokenDecimals,dataTokenDecimals, fixedRate, marketFee, withMint]
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

        require(
            fixedPrice[fixedPriceAddress],
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

        require(
            dispenser[_dispenser],
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

    function addPoolTemplate(address poolTemplate) external onlyRouterOwner {
        _addPoolTemplate(poolTemplate);
        emit PoolTemplateAdded(msg.sender, poolTemplate);
    }

    function removePoolTemplate(address poolTemplate) external onlyRouterOwner {
        _removePoolTemplate(poolTemplate);
        emit PoolTemplateRemoved(msg.sender, poolTemplate);
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
                IERC20(_operations[i].tokenIn).safeTransferFrom(
                    msg.sender,
                    address(this),
                    _operations[i].amountsIn
                );
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
                uint256 amountIn = IPool(_operations[i].source)
                    .getAmountInExactOut(
                        _operations[i].tokenIn,
                        _operations[i].tokenOut,
                        _operations[i].amountsOut,
                        _operations[i].swapMarketFee
                    );
                // pull amount In from user
                IERC20(_operations[i].tokenIn).safeTransferFrom(
                    msg.sender,
                    address(this),
                    amountIn
                );
                // we approve pool to pull token from router
                IERC20(_operations[i].tokenIn).safeIncreaseAllowance(
                    _operations[i].source,
                    amountIn
                );
                // perform swap
                IPool(_operations[i].source).swapExactAmountOut(
                    tokenInOutMarket,
                    amountsInOutMaxFee
                );
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
                        _operations[i].amountsOut
                    );

                // pull tokenIn amount
                IERC20(_operations[i].tokenIn).safeTransferFrom(
                    msg.sender,
                    address(this),
                    baseTokenAmount
                );
                // we approve pool to pull token from router
                IERC20(_operations[i].tokenIn).safeIncreaseAllowance(
                    _operations[i].source,
                    baseTokenAmount
                );
                // perform swap
                IFixedRateExchange(_operations[i].source).buyDT(
                    _operations[i].exchangeIds,
                    _operations[i].amountsOut,
                    _operations[i].amountsIn
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
}