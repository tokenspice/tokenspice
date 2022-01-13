pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0
import "../../interfaces/IERC20.sol";
import "../../interfaces/IERC20Template.sol";
import "../../interfaces/IPool.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/math/SafeMath.sol";
import "../../utils/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/security/ReentrancyGuard.sol";
/**
 * @title SideStaking
 *
 * @dev SideStaking is a contract that monitors stakings in pools, 
        adding or removing dt when only basetoken liquidity is added or removed
 *      Called by the pool contract
 *      Every ss newDataTokenCreated function has a ssParams array, 
        which for this contract has the following structure: 
     *                     [0]  = rate (wei)
     *                     [1]  = basetoken decimals
     *                     [2]  = vesting amount (wei)
     *                     [3]  = vested blocks
     *                     [4]  = initial liquidity in basetoken for pool creation
 *
 */
contract SideStaking is ReentrancyGuard {
    using SafeMath for uint256;
    using SafeERC20 for IERC20;
    address public router;

    struct Record {
        bool bound; //datatoken bounded
        address basetokenAddress;
        address poolAddress;
        bool poolFinalized; // did we finalized the pool ? We have to do it after burn-in
        uint256 datatokenBalance; //current dt balance
        uint256 datatokenCap; //dt cap
        uint256 basetokenBalance; //current basetoken balance
        uint256 lastPrice; //used for creating the pool
        uint256 rate; // rate to exchange DT<->BaseToken
        address publisherAddress;
        uint256 blockDeployed; //when this record was created
        uint256 vestingEndBlock; //see below
        uint256 vestingAmount; // total amount to be vested to publisher until vestingEndBlock
        uint256 vestingLastBlock; //last block in which a vesting has been granted
        uint256 vestingAmountSoFar; //how much was vested so far
    }

    mapping(address => Record) private _datatokens;
    uint256 private constant BASE = 10**18;

    modifier onlyRouter() {
        require(msg.sender == router, "ONLY ROUTER");
        _;
    }

    /**
     * @dev constructor
     *      Called on contract deployment.
     */
    constructor(address _router) public {
        require(_router != address(0), "Invalid _router address");
        router = _router;
    }

    /**
     * @dev newDataTokenCreated
     *      Called when new DataToken is deployed by the DataTokenFactory
     * @param datatokenAddress - datatokenAddress
     * @param basetokenAddress -
     * @param poolAddress - poolAddress
     * @param publisherAddress - publisherAddress
     * @param ssParams  - ss Params, see below
     */

    function newDataTokenCreated(
        address datatokenAddress,
        address basetokenAddress,
        address poolAddress,
        address publisherAddress,
        uint256[] memory ssParams
    ) external onlyRouter nonReentrant returns (bool) {
        //check if we are the controller of the pool
        require(poolAddress != address(0), "Invalid poolAddress");
        IPool bpool = IPool(poolAddress);
        require(
            bpool.getController() == address(this),
            "We are not the pool controller"
        );
        //check if the tokens are bound
        require(
            bpool.getDataTokenAddress() == datatokenAddress,
            "DataToken address missmatch"
        );
        require(
            bpool.getBaseTokenAddress() == basetokenAddress,
            "BaseToken address missmatch"
        );
        // check if we are the minter of DT
        IERC20Template dt = IERC20Template(datatokenAddress);
        require(
            (dt.permissions(address(this))).minter,
            "BaseToken address mismatch"
        );
        // get cap and mint it..
        dt.mint(address(this), dt.cap());

        require(dt.balanceOf(address(this)) == dt.totalSupply(), "Mint failed");
        require(dt.totalSupply().div(10) >= ssParams[2], "Max vesting 10%");
        //we are rich :)let's setup the records and we are good to go
        _datatokens[datatokenAddress] = Record({
            bound: true,
            basetokenAddress: basetokenAddress,
            poolAddress: poolAddress,
            poolFinalized: false,
            datatokenBalance: dt.totalSupply() - ssParams[2], // We need to remove the vesting amount from that
            datatokenCap: dt.cap(),
            basetokenBalance: ssParams[4],
            lastPrice: 0,
            rate: ssParams[0],
            publisherAddress: publisherAddress,
            blockDeployed: block.number,
            vestingEndBlock: block.number + ssParams[3],
            vestingAmount: ssParams[2],
            vestingLastBlock: block.number,
            vestingAmountSoFar: 0
        });

        notifyFinalize(datatokenAddress, ssParams[1]);

        return (true);
    }

    //public getters
    /**
     *  Returns  (total vesting amount + token released from the contract when adding liquidity)
     * @param datatokenAddress - datatokenAddress

     */

    function getDataTokenCirculatingSupply(address datatokenAddress)
        external
        view
        returns (uint256)
    {
        if (!_datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].datatokenCap -
            _datatokens[datatokenAddress].datatokenBalance);
    }

    /**
     *  Returns actual dts in circulation (vested token withdrawn from the contract +
         token released from the contract when adding liquidity)
     * @param datatokenAddress - datatokenAddress

     */

    function getDataTokenCurrentCirculatingSupply(address datatokenAddress)
        external
        view
        returns (uint256)
    {
        if (!_datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].datatokenCap -
            _datatokens[datatokenAddress].datatokenBalance -
            getvestingAmount(datatokenAddress) +
            getvestingAmountSoFar(datatokenAddress));
    }

    /**
     *  Returns publisher address
     * @param datatokenAddress - datatokenAddress

     */

    function getPublisherAddress(address datatokenAddress)
        external
        view
        returns (address)
    {
        if (!_datatokens[datatokenAddress].bound) return (address(0));
        return (_datatokens[datatokenAddress].publisherAddress);
    }

    /**
     *  Returns basetoken address
     * @param datatokenAddress - datatokenAddress

     */

    function getBaseTokenAddress(address datatokenAddress)
        external
        view
        returns (address)
    {
        if (!_datatokens[datatokenAddress].bound) return (address(0));
        return (_datatokens[datatokenAddress].basetokenAddress);
    }

    /**
     *  Returns pool address
     * @param datatokenAddress - datatokenAddress

     */

    function getPoolAddress(address datatokenAddress)
        external
        view
        returns (address)
    {
        if (!_datatokens[datatokenAddress].bound) return (address(0));
        return (_datatokens[datatokenAddress].poolAddress);
    }

    /**
     *  Returns basetoken balance in the contract
     * @param datatokenAddress - datatokenAddress

     */
    function getBaseTokenBalance(address datatokenAddress)
        external
        view
        returns (uint256)
    {
        if (! _datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].basetokenBalance);
    }

    /**
     *  Returns datatoken balance in the contract
     * @param datatokenAddress - datatokenAddress

     */

    function getDataTokenBalance(address datatokenAddress)
        external
        view
        returns (uint256)
    {
        if (! _datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].datatokenBalance);
    }

    /**
     *  Returns last vesting block
     * @param datatokenAddress - datatokenAddress

     */

    function getvestingEndBlock(address datatokenAddress)
        external
        view
        returns (uint256)
    {
        if (! _datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].vestingEndBlock);
    }

    /**
     *  Returns total vesting amount
     * @param datatokenAddress - datatokenAddress

     */

    function getvestingAmount(address datatokenAddress)
        public
        view
        returns (uint256)
    {
        if (! _datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].vestingAmount);
    }

    /**
     *  Returns last block when some vesting tokens were collected
     * @param datatokenAddress - datatokenAddress

     */

    function getvestingLastBlock(address datatokenAddress)
        external
        view
        returns (uint256)
    {
        if (!_datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].vestingLastBlock);
    }

    /**
     *  Returns amount of vested tokens that have been withdrawn from the contract so far
     * @param datatokenAddress - datatokenAddress

     */

    function getvestingAmountSoFar(address datatokenAddress)
        public
        view
        returns (uint256)
    {
        if (! _datatokens[datatokenAddress].bound) return (0);
        return (_datatokens[datatokenAddress].vestingAmountSoFar);
    }

    //called by pool to confirm that we can stake a token (add pool liquidty). If true, pool will call Stake function
    function canStake(
        address datatokenAddress,
        address stakeToken,
        uint256 amount
    ) public view returns (bool) {
        require(
            msg.sender == _datatokens[datatokenAddress].poolAddress,
            "ERR: Only pool can call this"
        );
        if (! _datatokens[datatokenAddress].bound) return (false);
        if (_datatokens[datatokenAddress].basetokenAddress == stakeToken)
            return (false);

        //check balances. Make sure that we have enough to vest
        if (_datatokens[datatokenAddress].datatokenBalance >= 
        (amount + (_datatokens[datatokenAddress].vestingAmount - _datatokens[datatokenAddress].vestingAmountSoFar))
        )
            return (true);
        return (false);
    }

    //called by pool so 1ss will stake a token (add pool liquidty).
    // Function only needs to approve the amount to be spent by the pool, pool will do the rest
    function Stake(
        address datatokenAddress,
        address stakeToken,
        uint256 amount
    ) external nonReentrant {
        if (!_datatokens[datatokenAddress].bound) return;
        require(
            msg.sender == _datatokens[datatokenAddress].poolAddress,
            "ERR: Only pool can call this"
        );
        bool ok = canStake(datatokenAddress, stakeToken, amount);
        if (!ok) return;
        IERC20 dt = IERC20(datatokenAddress);
        dt.safeIncreaseAllowance(_datatokens[datatokenAddress].poolAddress, amount);
        _datatokens[datatokenAddress].datatokenBalance -= amount;
    }

    //called by pool to confirm that we can stake a token (add pool liquidty). If true, pool will call Unstake function
    function canUnStake(
        address datatokenAddress,
        address stakeToken,
        uint256 lptIn
    ) public view returns (bool) {
        //TO DO
        if (! _datatokens[datatokenAddress].bound) return (false);
        require(
            msg.sender == _datatokens[datatokenAddress].poolAddress,
            "ERR: Only pool can call this"
        );
        //check balances, etc and issue true or false
        if (_datatokens[datatokenAddress].basetokenAddress == stakeToken)
            return (false);

        // we check LPT balance TODO: review this part
        if (IERC20(msg.sender).balanceOf(address(this)) >= lptIn) {
            return true;
        }
        return false;
    }

    //called by pool so 1ss will unstake a token (remove pool liquidty). 
    // In our case the balancer pool will handle all, this is just a notifier so 1ss can handle internal kitchen
    function UnStake(
        address datatokenAddress,
        address stakeToken,
        uint256 dtAmountIn,
        uint256 poolAmountOut
    ) external nonReentrant{
        if (! _datatokens[datatokenAddress].bound) return;
        require(
            msg.sender == _datatokens[datatokenAddress].poolAddress,
            "ERR: Only pool can call this"
        );
        bool ok = canUnStake(datatokenAddress, stakeToken, poolAmountOut);
        if (!ok) return;
        _datatokens[datatokenAddress].datatokenBalance += dtAmountIn;
    }

    //called by the pool (or by us) when we should finalize the pool
    function notifyFinalize(address datatokenAddress, uint256 decimals)
        internal
    {
        if (! _datatokens[datatokenAddress].bound ) return;
        if (_datatokens[datatokenAddress].poolFinalized) return;
        _datatokens[datatokenAddress].poolFinalized = true;
        uint256 baseTokenWeight = 5 * BASE; //pool weight: 50-50
        uint256 dataTokenWeight = 5 * BASE; //pool weight: 50-50
        uint256 baseTokenAmount = _datatokens[datatokenAddress]
            .basetokenBalance;
        //given the price, compute dataTokenAmount

        uint256 dataTokenAmount = ((_datatokens[datatokenAddress].rate *
            baseTokenAmount *
            dataTokenWeight) /
            baseTokenWeight /
            BASE) * (10**(18 - decimals));


        //approve the tokens and amounts
        IERC20 dt = IERC20(datatokenAddress);
        dt.safeIncreaseAllowance(_datatokens[datatokenAddress].poolAddress, dataTokenAmount);
        IERC20 dtBase = IERC20(
            _datatokens[datatokenAddress].basetokenAddress
        );
        dtBase.safeIncreaseAllowance(
            _datatokens[datatokenAddress].poolAddress,
            baseTokenAmount
        );

        // call the pool, bind the tokens, set the price, finalize pool
        IPool pool = IPool(_datatokens[datatokenAddress].poolAddress);
        pool.setup(
            datatokenAddress,
            dataTokenAmount,
            dataTokenWeight,
            _datatokens[datatokenAddress].basetokenAddress,
            baseTokenAmount,
            baseTokenWeight
        );
        //substract
        _datatokens[datatokenAddress].basetokenBalance -= baseTokenAmount;
        _datatokens[datatokenAddress].datatokenBalance -= dataTokenAmount;
        // send 50% of the pool shares back to the publisher
        IERC20 lPTokens = IERC20(
            _datatokens[datatokenAddress].poolAddress
        );
        uint256 lpBalance = lPTokens.balanceOf(address(this));
        //  uint256 balanceToTransfer = lpBalance.div(2);
        lPTokens.safeTransfer(
            _datatokens[datatokenAddress].publisherAddress,
            lpBalance.div(2)
        );
    }

    /**
     *  Send available vested tokens to the publisher address, can be called by anyone
     * @param datatokenAddress - datatokenAddress

     */
    // called by vester to get datatokens
    function getVesting(address datatokenAddress) external nonReentrant {
        require(
            _datatokens[datatokenAddress].bound,
            "ERR:Invalid datatoken"
        );
        // is this needed?
        // require(msg.sender == _datatokens[datatokenAddress].publisherAddress,'ERR: Only publisher can call this');

        //calculate how many tokens we need to vest to publisher<<
        uint256 blocksPassed;

        if (_datatokens[datatokenAddress].vestingEndBlock < block.number) {
            blocksPassed =
                _datatokens[datatokenAddress].vestingEndBlock -
                _datatokens[datatokenAddress].vestingLastBlock;
        } else {
            blocksPassed =
                block.number -
                _datatokens[datatokenAddress].vestingLastBlock;
        }

        uint256 vestPerBlock = _datatokens[datatokenAddress].vestingAmount.div(
            _datatokens[datatokenAddress].vestingEndBlock -
                _datatokens[datatokenAddress].blockDeployed
        );
        if (vestPerBlock == 0) return;
        uint256 amount = blocksPassed.mul(vestPerBlock);
        if (
            amount > 0 &&
            _datatokens[datatokenAddress].datatokenBalance >= amount
        ) {
            IERC20 dt = IERC20(datatokenAddress);
            _datatokens[datatokenAddress].vestingLastBlock = block.number;
            dt.safeTransfer(_datatokens[datatokenAddress].publisherAddress, amount);
            _datatokens[datatokenAddress].datatokenBalance -= amount;
            _datatokens[datatokenAddress].vestingAmountSoFar += amount;
        }
    }


    /**
     *  Change pool fee
     * @param datatokenAddress - datatokenAddress
     * @param poolAddress - poolAddress
     * @param swapFee - new fee

     */
    // called by ERC20 Deployer of datatoken
    function setPoolSwapFee(address datatokenAddress, address poolAddress, uint256 swapFee) external nonReentrant {
        require(poolAddress != address(0), "Invalid poolAddress");
        IPool bpool = IPool(poolAddress);
        require(
            bpool.getController() == address(this),
            "We are not the pool controller"
        );
        //check if the tokens are bound
        require(
            bpool.getDataTokenAddress() == datatokenAddress,
            "DataToken address missmatch"
        );
         IERC20Template dt = IERC20Template(datatokenAddress);
        require(dt.isERC20Deployer(msg.sender), "Not ERC20 Deployer");
        bpool.setSwapFee(swapFee);
    }
}