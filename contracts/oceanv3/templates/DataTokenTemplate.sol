pragma solidity 0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import '../interfaces/IERC20Template.sol';
import 'OpenZeppelin/openzeppelin-contracts@2.1.1/contracts/token/ERC20/ERC20.sol';


/**
* @title DataTokenTemplate
*  
* @dev DataTokenTemplate is an ERC20 compliant token template
*      Used by the factory contract as a bytecode reference to 
*      deploy new DataTokens.
*/
contract DataTokenTemplate is IERC20Template, ERC20 {
    using SafeMath for uint256;

    string  private _name;
    string  private _symbol;
    string  private _blob;
    uint256 private _cap;
    uint8 private constant _decimals = 18;
    address private _communityFeeCollector;
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

    /**
     * @dev constructor
     *      Called prior contract deployment
     * @param name refers to a template DataToken name
     * @param symbol refers to a template DataToken symbol
     * @param minterAddress refers to an address that has minter role
     * @param cap the total ERC20 cap
     * @param blob data string refering to the resolver for the metadata
     * @param feeCollector it is the community fee collector address
     */
    constructor(
        string memory name,
        string memory symbol,
        address minterAddress,
        uint256 cap,
        string memory blob,
        address feeCollector
    )
        public
    {
        _initialize(
            name,
            symbol,
            minterAddress,
            cap,
            blob,
            feeCollector
        );
    }
    
    /**
     * @dev initialize
     *      Called prior contract initialization (e.g creating new DataToken instance)
     *      Calls private _initialize function. Only if contract is not initialized.
     * @param name refers to a new DataToken name
     * @param symbol refers to a nea DataToken symbol
     * @param minterAddress refers to an address that has minter rights
     * @param cap the total ERC20 cap
     * @param blob data string refering to the resolver for the metadata
     * @param feeCollector it is the community fee collector address
     */
    function initialize(
        string calldata name,
        string calldata symbol,
        address minterAddress,
        uint256 cap,
        string calldata blob,
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
            cap,
            blob,
            feeCollector
        );
    }

    /**
     * @dev _initialize
     *      Private function called on contract initialization.
     * @param name refers to a new DataToken name
     * @param symbol refers to a nea DataToken symbol
     * @param minterAddress refers to an address that has minter rights
     * @param cap the total ERC20 cap
     * @param blob data string refering to the resolver for the metadata
     * @param feeCollector it is the community fee collector address
     */
    function _initialize(
        string memory name,
        string memory symbol,
        address minterAddress,
        uint256 cap,
        string memory blob,
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
            cap != 0,
            'DataTokenTemplate: Invalid cap value'
        );
        _cap = cap;
        _name = name;
        _blob = blob;
        _symbol = symbol;
        _minter = minterAddress;
        _communityFeeCollector = feeCollector;
        initialized = true;
        return initialized;
    }

    /**
     * @dev mint
     *      Only the minter address can call it.
     *      msg.value should be higher than zero and gt or eq minting fee
     * @param account refers to an address that token is going to be minted to.
     * @param value refers to amount of tokens that is going to be minted.
     */
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

    /**
     * @dev startOrder
     *      called by payer or consumer prior ordering a service consume on a marketplace.
     * @param consumer is the consumer address (payer could be different address)
     * @param amount refers to amount of tokens that is going to be transfered.
     * @param serviceId service index in the metadata
     * @param mrktFeeCollector marketplace fee collector
     */
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

    /**
     * @dev finishOrder
     *      called by provider prior completing service delivery only
     *      if there is a partial or full refund.
     * @param orderTxId refers to the transaction Id  of startOrder acts 
     *                  as a payment reference.
     * @param consumer refers to an address that has consumed that service.
     * @param amount refers to amount of tokens that is going to be transfered.
     * @param serviceId service index in the metadata.
     */
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
     * @dev name
     *      It returns the token name.
     * @return DataToken name.
     */
    function name() external view returns(string memory) {
        return _name;
    }

    /**
     * @dev symbol
     *      It returns the token symbol.
     * @return DataToken symbol.
     */
    function symbol() external view returns(string memory) {
        return _symbol;
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
     * @dev decimals
     *      It returns the token decimals.
     *      how many supported decimal points
     * @return DataToken decimals.
     */
    function decimals() external view returns(uint8) {
        return _decimals;
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
