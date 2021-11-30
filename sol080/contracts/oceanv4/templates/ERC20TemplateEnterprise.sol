pragma solidity >=0.6.0;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "../interfaces/IERC20Template.sol";
import "../interfaces/IERC721Template.sol";
import "../interfaces/IFactoryRouter.sol";
import "../interfaces/IFixedRateExchange.sol";
import "../interfaces/IDispenser.sol";
import "../utils/ERC725/ERC725Ocean.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/ERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/math/SafeMath.sol";
import "../utils/ERC20Roles.sol";


/**
 * @title DataTokenTemplate
 *
 * @dev ERC20TemplateEnterprise is an ERC20 compliant token template
 *      Used by the factory contract as a bytecode reference to
 *      deploy new DataTokens.
 * IMPORTANT CHANGES:
 *  - buyFromFreAndOrder function:  one call to buy a DT from the minting capable FRE, startOrder and burn the DT
 *  - buyFromDispenserAndOrder function:  one call to fetch a DT from the Dispenser, startOrder and burn the DT
 *  - creation of pools is not allowed
 */
contract ERC20TemplateEnterprise is ERC20("test", "testSymbol"), ERC20Roles, ERC20Burnable {
    using SafeMath for uint256;

    string private _name;
    string private _symbol;
    uint256 private _cap;
    uint8 private constant _decimals = 18;
    address private _communityFeeCollector;
    bool private initialized = false;
    address private _erc721Address;
    address private feeCollector;
    address private publishMarketFeeAddress;
    address private publishMarketFeeToken;  
    uint256 private publishMarketFeeAmount;
    uint8 private constant templateId = 2;

    uint256 public constant BASE = 10**18;
    uint256 public constant BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 100;  // == OPF takes 1% of the fees
    

    // EIP 2612 SUPPORT
    bytes32 public DOMAIN_SEPARATOR;
    // keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    bytes32 public constant PERMIT_TYPEHASH =
        0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;

    mapping(address => uint256) public nonces;
    address public router;
    

    event OrderStarted(
        address indexed consumer,
        address payer,
        uint256 amount,
        uint256 serviceId,
        uint256 timestamp,
        address indexed publishMarketAddress,
        address indexed consumeFeeMarketAddress,
        uint256 blockNumber
    );

    
    event MinterProposed(address currentMinter, address newMinter);

    event MinterApproved(address currentMinter, address newMinter);

    event NewPool(
        address poolAddress,
        address ssContract,
        address basetokenAddress
    );

    event NewFixedRate(bytes32 exchangeId, address owner);

    modifier onlyNotInitialized() {
        require(
            !initialized,
            "ERC20Template: token instance already initialized"
        );
        _;
    }
    modifier onlyNFTOwner() {
        require(
            msg.sender == IERC721Template(_erc721Address).ownerOf(1),
            "ERC20Template: not NFTOwner"
        );
        _;
    }

    modifier onlyPublishingMarketFeeAddress() {
        require(
            msg.sender == publishMarketFeeAddress,
            "ERC20Template: not publishMarketFeeAddress"
        );
        _;
    }

    modifier onlyERC20Deployer() {
        require(
            IERC721Template(_erc721Address)
                .getPermissions(msg.sender)
                .deployERC20 == true,
            "ERC20Template: NOT DEPLOYER ROLE"
        );
        _;
    }

    /**
     * @dev initialize
     *      Called prior contract initialization (e.g creating new DataToken instance)
     *      Calls private _initialize function. Only if contract is not initialized.
     * @param strings_ refers to an array of strings
     *                      [0] = name token
     *                      [1] = symbol
     * @param addresses_ refers to an array of addresses passed by user
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = feeManager initial feeManager for this DT
     *                     [2]  = publishing Market Address
     *                     [3]  = publishing Market Fee Token
     * @param factoryAddresses_ refers to an array of addresses passed by the factory
     *                     [0]  = erc721Address
     *                     [1]  = communityFeeCollector it is the community fee collector address
     *                     [2]  = router address
     *
     * @param uints_  refers to an array of uints
     *                     [0] = cap_ the total ERC20 cap
     *                     [1] = publishing Market Fee Amount
     * @param bytes_  refers to an array of bytes
     *                     Currently not used, usefull for future templates
     */
    function initialize(
        string[] calldata strings_,
        address[] calldata addresses_,
        address[] calldata factoryAddresses_,
        uint256[] calldata uints_,
        bytes[] calldata bytes_
    ) external onlyNotInitialized returns (bool) {
        return
            _initialize(
                strings_,
                addresses_,
                factoryAddresses_,
                uints_,
                bytes_
            );
    }

    /**
     * @dev _initialize
     *      Private function called on contract initialization.
     * @param strings_ refers to an array of strings
     *                      [0] = name token
     *                      [1] = symbol
     * @param addresses_ refers to an array of addresses passed by user
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = feeManager initial feeManager for this DT
     *                     [2]  = publishing Market Address
     *                     [3]  = publishing Market Fee Token
     * @param factoryAddresses_ refers to an array of addresses passed by the factory
     *                     [0]  = erc721Address
     *                     [1]  = communityFeeCollector it is the community fee collector address
     *                     [2]  = router address
     *
     * @param uints_  refers to an array of uints
     *                     [0] = cap_ the total ERC20 cap
     *                     [1] = publishing Market Fee Amount
     * @param bytes_  refers to an array of bytes
     *                     Currently not used, usefull for future templates
     */
    function _initialize(
        string[] memory strings_,
        address[] memory addresses_,
        address[] memory factoryAddresses_,
        uint256[] memory uints_,
        bytes[] memory bytes_
        ) private returns (bool) {
        address erc721Address = factoryAddresses_[0];
        address communityFeeCollector = factoryAddresses_[1];
        require(
            erc721Address != address(0),
            "ERC20Template: Invalid minter,  zero address"
        );

        require(
            communityFeeCollector != address(0),
            "ERC20Template: Invalid community fee collector, zero address"
        );

        require(uints_[0] != 0, "DataTokenTemplate: Invalid cap value");
        _cap = uints_[0];
        _name = strings_[0];
        _symbol = strings_[1];
        _erc721Address = erc721Address;
        router = factoryAddresses_[2];
        _communityFeeCollector = communityFeeCollector;
        initialized = true;
        // add a default minter, similar to what happens with manager in the 721 contract
        _addMinter(addresses_[0]);
        _addFeeManager(addresses_[1]);
        publishMarketFeeAddress = addresses_[2];
        publishMarketFeeToken = addresses_[3];
        publishMarketFeeAmount = uints_[1];
        uint256 chainId;
        assembly {
            chainId := chainid()
        }
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256(
                    "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
                ),
                keccak256(bytes(_name)),
                keccak256(bytes("1")), // version, could be any other value
                chainId,
                address(this)
            )
        );

        return initialized;
    }

    

    /**
     * @dev createFixedRate
     *      Creates a new FixedRateExchange setup.
     * @param fixedPriceAddress fixedPriceAddress
     * @param addresses array of addresses [baseToken,owner,marketFeeCollector]
     * @param uints array of uints [baseTokenDecimals,dataTokenDecimals, fixedRate, marketFee, withMint]
     * @return exchangeId
     */
    function createFixedRate(
        address fixedPriceAddress,
        address[] memory addresses,
        uint[] memory uints
    ) external onlyERC20Deployer returns (bytes32 exchangeId) {
        //force FRE allowedSwapper to this contract address. no one else can swap
        addresses[3] = address(this);
        exchangeId = IFactoryRouter(router).deployFixedRate(
            fixedPriceAddress,
            addresses,
            uints
        );
        if (uints[4] > 0)
            _addMinter(fixedPriceAddress);
        emit NewFixedRate(exchangeId, addresses[0]);
    }

    /**
     * @dev createDispenser
     *      Creates a new Dispenser
     * @param _dispenser dispenser contract address
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     */
    function createDispenser(
        address _dispenser,
        uint256 maxTokens,
        uint256 maxBalance,
        bool withMint
    ) external onlyERC20Deployer {
        IFactoryRouter(router).deployDispenser(
            _dispenser, address(this), maxTokens, maxBalance, msg.sender, address(this) );
        // add FixedPriced contract as minter if withMint == true
        if (withMint == true)
            _addMinter(_dispenser);
        
    }

    /**
     * @dev mint
     *      Only the minter address can call it.
     *      msg.value should be higher than zero and gt or eq minting fee
     * @param account refers to an address that token is going to be minted to.
     * @param value refers to amount of tokens that is going to be minted.
     */
    function mint(address account, uint256 value) external {
        require(
            permissions[msg.sender].minter == true,
            "ERC20Template: NOT MINTER"
        );
        require(
            totalSupply().add(value) <= _cap,
            "DataTokenTemplate: cap exceeded"
        );
        _mint(account, value);
    }
    
    /**
     * @dev isMinter
     *      Check if an address has the minter role
     * @param account refers to an address that is checked
     */
    function isMinter(address account) public view returns(bool) {
        return(permissions[account].minter);
    }
    
    /**
     * @dev startOrder
     *      called by payer or consumer prior ordering a service consume on a marketplace.
     *      Requires previous approval of consumeFeeToken and publishMarketFeeToken
     * @param consumer is the consumer address (payer could be different address)
     * @param amount refers to amount of tokens that is going to be transfered.
     * @param serviceId service index in the metadata
     * @param consumeFeeAddress consume marketplace fee address
       @param consumeFeeToken // address of the token marketplace wants to add fee on top
       @param consumeFeeAmount // fee amount
     */
    function startOrder(
        address consumer,
        uint256 amount,
        uint256 serviceId,
        address consumeFeeAddress,
        address consumeFeeToken, // address of the token marketplace wants to add fee on top
        uint256 consumeFeeAmount // amount to be transfered to marketFeeCollector
    ) external {
        _startOrder(consumer,amount,serviceId,consumeFeeAddress,consumeFeeToken,consumeFeeAmount);
    }

    function _startOrder(
        address consumer,
        uint256 amount,
        uint256 serviceId,
        address consumeFeeAddress,
        address consumeFeeToken, // address of the token marketplace wants to add fee on top
        uint256 consumeFeeAmount // amount to be transfered to marketFeeCollector
    ) private {
        uint256 communityFeeConsume = 0;
        uint256 communityFeePublish = 0;
        require(balanceOf(msg.sender) >= amount, "Not enough Data Tokens to start Order");
        // publishMarketFees
        // Requires approval for the publishMarketFeeToken of publishMarketFeeAmount
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        if (publishMarketFeeAmount > 0 && publishMarketFeeToken!=address(0) && publishMarketFeeAddress!=address(0)) {
            require(IERC20(publishMarketFeeToken).transferFrom(
                msg.sender,
                address(this),
                publishMarketFeeAmount
            ),'Failed to transfer publishMarketFee');
            communityFeePublish = publishMarketFeeAmount.div(100); //hardcode 1% goes to OPF
            //send publishMarketFee
            require(IERC20(publishMarketFeeToken)
            .transfer(publishMarketFeeAddress,publishMarketFeeAmount.sub(communityFeePublish))
            , 'Failed to transfer fee to publishMarketFeeAddress');
        }

        // consumeFees
        // Requires approval for the consumeFeeToken of consumeFeeAmount
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        if (consumeFeeAmount > 0 && consumeFeeToken!=address(0) && consumeFeeAddress!=address(0)) {
            require(IERC20(consumeFeeToken).transferFrom(
                msg.sender,
                address(this),
                consumeFeeAmount
            ),'Failed to transfer consumeFee');
            communityFeeConsume = consumeFeeAmount.div(100); //hardcode 1% goes to OPF
            //send consumeFee
            require(IERC20(consumeFeeToken)
            .transfer(consumeFeeAddress,consumeFeeAmount.sub(communityFeeConsume))
            , 'Failed to transfer fee to consumeFeeAddress');
        }
        //send fees to OPF
        if(communityFeePublish>0 && communityFeeConsume>0 && consumeFeeToken == publishMarketFeeToken){
            //since both fees are in the same token, have just one transaction for both, to save gas
            require(IERC20(consumeFeeToken)
            .transfer(_communityFeeCollector,communityFeePublish.add(communityFeeConsume))
            , 'Failed to transfer both fees to OPF');
        }
        else{
            //we need to do them one by one
            if(communityFeePublish>0 && publishMarketFeeToken!=address(0)){
                require(IERC20(publishMarketFeeToken)
                .transfer(_communityFeeCollector,communityFeePublish), 'Failed to transfer publish fees to OPF');
            }
            if(communityFeeConsume>0 && consumeFeeToken!=address(0)){
                require(IERC20(consumeFeeToken)
                .transfer(_communityFeeCollector,communityFeeConsume), 'Failed to transfer consume fee to OPF');
            }
        }
        // instead of sending datatoken to publisher, we burn them
        burn(amount);
        
        emit OrderStarted(
            consumer,
            msg.sender,
            amount,
            serviceId,
            block.timestamp,
            publishMarketFeeAddress,
            consumeFeeAddress,
            block.number
        );
    }

 
    
    /**
     * @dev addMinter
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple minters
     * @param _minter new minter address
     */

    function addMinter(address _minter) external onlyERC20Deployer {
        _addMinter(_minter);
    }

    /**
     * @dev removeMinter
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple minters
     * @param _minter minter address to remove
     */

    function removeMinter(address _minter) external onlyERC20Deployer {
        _removeMinter(_minter);
    }

    /**
     * @dev addFeeManager (can set who's going to collect fee when consuming orders)
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple feeManagers
     * @param _feeManager new minter address
     */

    function addFeeManager(address _feeManager) external onlyERC20Deployer {
        _addFeeManager(_feeManager);
    }

    /**
     * @dev removeFeeManager
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple feeManagers
     * @param _feeManager feeManager address to remove
     */

    function removeFeeManager(address _feeManager) external onlyERC20Deployer {
        _removeFeeManager(_feeManager);
    }

    /**
     * @dev setData
     *      Only ERC20Deployer (at 721 level) can call it.
     *      This function allows to store data with a preset key (keccak256(ERC20Address)) into NFT 725 Store
     * @param _value data to be set with this key
     */

    function setData(bytes calldata _value) external onlyERC20Deployer {
        bytes32 key = keccak256(abi.encodePacked(address(this)));
        IERC721Template(_erc721Address).setDataERC20(key, _value);
    }

    /**
     * @dev cleanPermissions()
     *      Only NFT Owner (at 721 level) can call it.
     *      This function allows to remove all minters, feeManagers and reset the feeCollector
     *
     */

    function cleanPermissions() external onlyNFTOwner {
        _cleanPermissions();
        feeCollector = address(0);
    }

    /**
     * @dev cleanFrom721() 
     *      OnlyNFT(721) Contract can call it.
     *      This function allows to remove all minters, feeManagers and reset the feeCollector
     *       This function is used when transferring an NFT to a new owner,
     * so that permissions at ERC20level (minter,feeManager,feeCollector) can be reset.
     *      
     */
    function cleanFrom721() external {
        require(
            msg.sender == _erc721Address,
            "ERC20Template: NOT 721 Contract"
        );
        _cleanPermissions();
        feeCollector = address(0);
    }

    /**
     * @dev setFeeCollector
     *      Only feeManager can call it
     *      This function allows to set a newFeeCollector (receives DT when consuming)
            If not set the feeCollector is the NFT Owner
     * @param _newFeeCollector new fee collector 
     */

    function setFeeCollector(address _newFeeCollector) external {
        require(
            permissions[msg.sender].feeManager == true,
            "ERC20Template: NOT FEE MANAGER"
        );
        feeCollector = _newFeeCollector;
    }


    
    /**
     * @dev getPublishingMarketFee
     *      Get publishingMarket Fees
     *      This function allows to get the current fee set by the publishing market
     */
    function getPublishingMarketFee() external view returns (address , address, uint256) {
        return (publishMarketFeeAddress, publishMarketFeeToken, publishMarketFeeAmount);
    }

     /**
     * @dev setPublishingMarketFee
     *      Only publishMarketFeeAddress can call it
     *      This function allows to set the fees required by the publisherMarket            
     * @param _publishMarketFeeAddress  new _publishMarketFeeAddress
     * @param _publishMarketFeeToken new _publishMarketFeeToken
     * @param _publishMarketFeeAmount new fee amount
     */
    function setPublishingMarketFee(
        address _publishMarketFeeAddress, 
        address _publishMarketFeeToken, 
        uint256 _publishMarketFeeAmount) external onlyPublishingMarketFeeAddress {
        publishMarketFeeAddress = _publishMarketFeeAddress;
        publishMarketFeeToken =  _publishMarketFeeToken;
        publishMarketFeeAmount = _publishMarketFeeAmount;
    }
    /**
     * @dev getId
     *      Return template id
     */
    function getId() external pure returns (uint8) {
        return templateId;
    }

    /**
     * @dev name
     *      It returns the token name.
     * @return DataToken name.
     */
    function name() public view override returns (string memory) {
        return _name;
    }

    /**
     * @dev symbol
     *      It returns the token symbol.
     * @return DataToken symbol.
     */
    function symbol() public view override returns (string memory) {
        return _symbol;
    }

    /**
     * @dev decimals
     *      It returns the token decimals.
     *      how many supported decimal points
     * @return DataToken decimals.
     */
    function decimals() public pure override returns (uint8) {
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
     * @dev isInitialized
     *      It checks whether the contract is initialized.
     * @return true if the contract is initialized.
     */

    function isInitialized() external view returns (bool) {
        return initialized;
    }

    /**
     * @dev permit
     *      used for signed approvals, see ERC20Template test for more details
     * @param owner user who signed the message
     * @param spender spender
     * @param value token amount
     * @param deadline deadline after which signed message is no more valid
     * @param v parameters from signed message
     * @param r parameters from signed message
     * @param s parameters from signed message
     */

    function permit(
        address owner,
        address spender,
        uint256 value,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(deadline >= block.timestamp, "ERC20DT: EXPIRED");
        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19\x01",
                DOMAIN_SEPARATOR,
                keccak256(
                    abi.encode(
                        PERMIT_TYPEHASH,
                        owner,
                        spender,
                        value,
                        nonces[owner]++,
                        deadline
                    )
                )
            )
        );
        address recoveredAddress = ecrecover(digest, v, r, s);
        require(
            recoveredAddress != address(0) && recoveredAddress == owner,
            "ERC20DT: INVALID_SIGNATURE"
        );
        _approve(owner, spender, value);
    }

    /**
     * @dev getAddressLength
     *      It returns the array lentgh
            @param array address array we want to get length
     * @return length
     */

    function getAddressLength(address[] memory array)
        private
        pure
        returns (uint256)
    {
        return array.length;
    }

    /**
     * @dev getUintLength
     *      It returns the array lentgh
            @param array uint array we want to get length
     * @return length
     */

    function getUintLength(uint256[] memory array)
        private
        pure
        returns (uint256)
    {
        return array.length;
    }

    /**
     * @dev getBytesLength
     *      It returns the array lentgh
            @param array bytes32 array we want to get length
     * @return length
     */

    function getBytesLength(bytes32[] memory array)
        private
        pure
        returns (uint256)
    {
        return array.length;
    }

    /**
     * @dev getFeeCollector
     *      It returns the current feeCollector
     * @return feeCollector address
     */

    function getFeeCollector() public view returns (address) {
        if (feeCollector == address(0)) {
            return IERC721Template(_erc721Address).ownerOf(1);
        } else {
            return feeCollector;
        }
    }

    /**
     * @dev fallback function
     *      this is a default fallback function in which receives
     *      the collected ether.
     */
    fallback() external payable {}

    /**
     * @dev withdrawETH
     *      transfers all the accumlated ether the collector account
     */
    function withdrawETH() 
        external 
        payable
    {
        payable(getFeeCollector()).transfer(address(this).balance);
    }


    
    struct OrderParams{
        address consumer;
        uint256 amount;
        uint256 serviceId;
        address consumeFeeAddress;
        address consumeFeeToken; // address of the token marketplace wants to add fee on top
        uint256 consumeFeeAmount; 
    }
    struct FreParams{
        address exchangeContract;
        bytes32 exchangeId;
        uint256 maxBaseTokenAmount;
    }
    
    /**
    * @dev buyFromFreAndOrder
    *      Buys 1 DT from the FRE and then startsOrder, while burning that DT
    */
    function buyFromFreAndOrder(OrderParams memory _orderParams,FreParams memory _freParams) external{
        // get exchange info
        (
            ,
            address datatoken,
            ,
            address baseToken,
            ,
            ,
            ,
            ,
            ,
            ,
            ,
            
            
        ) = IFixedRateExchange(_freParams.exchangeContract).getExchange(_freParams.exchangeId);
        require(datatoken == address(this), 'This FixedRate is not providing this DT');
        // get token amounts needed
        (
            uint256 baseTokenAmount,
            ,
            ,
            
        ) = IFixedRateExchange(_freParams.exchangeContract)
        .calcBaseInGivenOutDT(_freParams.exchangeId, _orderParams.amount);
        require(baseTokenAmount<=_freParams.maxBaseTokenAmount, 'FixedRateExchange: Too many base tokens');
        //transfer baseToken to us first
        require(IERC20(baseToken).transferFrom(
                msg.sender,
                address(this),
                baseTokenAmount
            ),'Failed to transfer baseTokenAmount');
        //approve FRE to spend baseTokens
        IERC20(baseToken).approve(_freParams.exchangeContract, baseTokenAmount);
        //buy DT
        IFixedRateExchange(_freParams.exchangeContract)
        .buyDT(_freParams.exchangeId, _orderParams.amount, baseTokenAmount);
        require(balanceOf(address(this))>=_orderParams.amount, "Unable to buy DT from FixedRate");
        //we need the following because startOrder expects msg.sender to have dt
        _transfer(address(this),msg.sender,_orderParams.amount);
        //startOrder and burn it
        _startOrder(_orderParams.consumer,_orderParams.amount,_orderParams.serviceId,
        _orderParams.consumeFeeAddress, _orderParams.consumeFeeToken, _orderParams.consumeFeeAmount);

    }

    /**
    * @dev buyFromDispenserAndOrder
    *      Gets DT from dispenser and then startsOrder, while burning that DT
    */
    function buyFromDispenserAndOrder(OrderParams memory _orderParams, address dispenserContract) external{
        //get DT
        IDispenser(dispenserContract).dispense(address(this), _orderParams.amount, msg.sender);
        require(balanceOf(address(msg.sender))>=_orderParams.amount, "Unable to get DT from Dispenser");
        //startOrder and burn it
        _startOrder(_orderParams.consumer,_orderParams.amount,_orderParams.serviceId,
        _orderParams.consumeFeeAddress, _orderParams.consumeFeeToken, _orderParams.consumeFeeAmount);
    }
}
