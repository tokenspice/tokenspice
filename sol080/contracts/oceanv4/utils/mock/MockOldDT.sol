pragma solidity >=0.7.1;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

//import '../interfaces/IERC20Template.sol';
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/ERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/math/SafeMath.sol";

/**
* @title DataTokenTemplate
*  
* @dev DataTokenTemplate is an ERC20 compliant token template
*      Used by the factory contract as a bytecode reference to 
*      deploy new DataTokens.
*/
contract MockOldDT is ERC20('Test','TESTSYMBOL') {
    using SafeMath for uint256;

    string  private _name = 'MOCKV3DT';
    string  private _symbol = 'V3DT';
    string  private _blob = 'blob';
    uint256 private _cap = 1e21;
    uint8 private constant _decimals = 18;
    address private _communityFeeCollector = address(0);
    bool    private initialized = false;
    address private _minter;
    address private _proposedMinter;
    uint256 public constant BASE = 10**18;
    uint256 public constant BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000;
    uint256 public constant BASE_MARKET_FEE_PERCENTAGE = BASE / 1000;

    event OrderStarted(
            address indexed consumer,
            address indexed payer,
            uint256 amount, 
            uint256 serviceId, 
            uint256 timestamp,
            address indexed mrktFeeCollector,
            uint256 marketFee
    );

    event OrderFinished(
            bytes32 orderTxId, 
            address indexed consumer,
            uint256 amount, 
            uint256 serviceId, 
            address indexed provider,
            uint256 timestamp
    );

    event MinterProposed(
        address currentMinter,
        address newMinter
    );

    event MinterApproved(
        address currentMinter,
        address newMinter
    );

    modifier onlyNotInitialized() {
        require(
            !initialized,
            'DataTokenTemplate: token instance already initialized'
        );
        _;
    }
    
    modifier onlyMinter() {
        require(
            msg.sender == _minter,
            'DataTokenTemplate: invalid minter' 
        );
        _;
    }

    constructor() 
        
    {
        _initialize(
            _name,
            _symbol,
            msg.sender,
            _cap,
            _blob,
            msg.sender
        );
    }
    
   
    function initialize(
        string calldata name,
        string calldata symbol,
        address minterAddress,
        uint256 cap_,
        string calldata blob_,
        address feeCollector
    ) 
        external
        onlyNotInitialized
        returns(bool)
    {
        return _initialize(
            name,
            symbol,
            minterAddress,
            cap_,
            blob_,
            feeCollector
        );
    }

   
    function _initialize(
        string memory name,
        string memory symbol,
        address minterAddress,
        uint256 cap_,
        string memory blob_,
        address feeCollector
    )
        private
        returns(bool)
    {
        require(
            minterAddress != address(0), 
            'DataTokenTemplate: Invalid minter,  zero address'
        );

        require(
            _minter == address(0), 
            'DataTokenTemplate: Invalid minter, zero address'
        );

        require(
            feeCollector != address(0),
            'DataTokenTemplate: Invalid community fee collector, zero address'
        );

        require(
            cap_ != 0,
            'DataTokenTemplate: Invalid cap value'
        );
        _cap = cap_;
        _name = name;
        _blob = blob_;
        _symbol = symbol;
        _minter = minterAddress;
        _communityFeeCollector = feeCollector;
        initialized = true;
        return initialized;
    }

   
    function mint(
        address account,
        uint256 value
    ) 
        external  
        onlyMinter 
    {
        require(
            totalSupply().add(value) <= _cap, 
            'DataTokenTemplate: cap exceeded'
        );
        _mint(account, value);
    }

    function startOrder(
        address consumer,
        uint256 amount,
        uint256 serviceId,
        address mrktFeeCollector
    )
        external
    {
        uint256 marketFee = 0;
        uint256 communityFee = calculateFee(
            amount, 
            BASE_COMMUNITY_FEE_PERCENTAGE
        );
        transfer(_communityFeeCollector, communityFee);
        if(mrktFeeCollector != address(0)){
            marketFee = calculateFee(
                amount, 
                BASE_MARKET_FEE_PERCENTAGE
            );
            transfer(mrktFeeCollector, marketFee);
        }
        uint256 totalFee = communityFee.add(marketFee);
        transfer(_minter, amount.sub(totalFee));
        emit OrderStarted(
            consumer,
            msg.sender,
            amount,
            serviceId,
            /* solium-disable-next-line */
            block.timestamp,
            mrktFeeCollector,
            marketFee
        );
    }

    
    function finishOrder(
        bytes32 orderTxId, 
        address consumer, 
        uint256 amount,
        uint256 serviceId
    )
        external
    {
        if ( amount != 0 )  
            require(
                transfer(consumer, amount),
                'DataTokenTemplate: failed to finish order'
            );
        
        emit OrderFinished(
            orderTxId, 
            consumer, 
            amount, 
            serviceId, 
            msg.sender,
            /* solium-disable-next-line */
            block.timestamp
        );
    }

    /**
     * @dev proposeMinter
     *      It proposes a new token minter address.
     *      Only the current minter can call it.
     * @param newMinter refers to a new token minter address.
     */
    function proposeMinter(address newMinter) 
        external 
        onlyMinter 
    {
        _proposedMinter = newMinter;
        emit MinterProposed(
            msg.sender,
            _proposedMinter
        );
    }

    /**
     * @dev approveMinter
     *      It approves a new token minter address.
     *      Only the current minter can call it.
     */
    function approveMinter()
        external
    {
        require(
            msg.sender == _proposedMinter,
            'DataTokenTemplate: invalid proposed minter address'
        );
        emit MinterApproved(
            _minter,
            _proposedMinter
        );
        _minter = _proposedMinter;
        _proposedMinter = address(0);
    }

  

    /**
     * @dev blob
     *      It returns the blob (e.g https://123.com).
     * @return DataToken blob.
     */
    function blob() external view returns(string memory) {
        return _blob;
    }

   
    /**
     * @dev cap
     *      it returns the capital.
     * @return DataToken cap.
     */
    function cap() external view returns (uint256) {
        return _cap;
    }

    /**
     * @dev isMinter
     *      It takes the address and checks whether it has a minter role.
     * @param account refers to the address.
     * @return true if account has a minter role.
     */
    function isMinter(address account) external view returns(bool) {
        return (_minter == account);
    } 

    /**
     * @dev minter
     * @return minter's address.
     */
    function minter()
        external
        view 
        returns(address)
    {
        return _minter;
    }

    /**
     * @dev isInitialized
     *      It checks whether the contract is initialized.
     * @return true if the contract is initialized.
     */ 
    function isInitialized() external view returns(bool) {
        return initialized;
    }

    /**
     * @dev calculateFee
     *      giving a fee percentage, and amount it calculates the actual fee
     * @param amount the amount of token
     * @param feePercentage the fee percentage 
     * @return the token fee.
     */ 
    function calculateFee(
        uint256 amount,
        uint256 feePercentage
    )
        public
        pure
        returns(uint256)
    {
        if(amount == 0) return 0;
        if(feePercentage == 0) return 0;
        return amount.mul(feePercentage).div(BASE);
    }
}