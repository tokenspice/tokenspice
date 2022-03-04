pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "../interfaces/IERC20Template.sol";
import "../interfaces/IERC721Template.sol";
import "../interfaces/IFactoryRouter.sol";
import "../utils/ERC725/ERC725Ocean.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/ERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/math/SafeMath.sol";

import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/utils/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/security/ReentrancyGuard.sol";
import "../utils/ERC20Roles.sol";

/**
 * @title DatatokenTemplate
 *
 * @dev DatatokenTemplate is an ERC20 compliant token template
 *      Used by the factory contract as a bytecode reference to
 *      deploy new Datatokens.
 */
contract ERC20Template is
    ERC20("test", "testSymbol"),
    ERC20Roles,
    ERC20Burnable,
    ReentrancyGuard
{
    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    string private _name;
    string private _symbol;
    uint256 private _cap;
    uint8 private constant _decimals = 18;
    address private _communityFeeCollector;
    bool private initialized = false;
    address private _erc721Address;
    address private paymentCollector;
    address private publishMarketFeeAddress;
    address private publishMarketFeeToken;
    uint256 private publishMarketFeeAmount;
    uint256 public constant BASE = 10**18;
    
    // EIP 2612 SUPPORT
    bytes32 public DOMAIN_SEPARATOR;
    // keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    bytes32 public constant PERMIT_TYPEHASH =
        0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;

    mapping(address => uint256) public nonces;

    address public router;
    address[] deployedPools;
    struct fixedRate{
        address contractAddress;
        bytes32 id;
    }
    fixedRate[] fixedRateExchanges;
    address[] dispensers;

    struct providerFee{
        address providerFeeAddress;
        address providerFeeToken; // address of the token 
        uint256 providerFeeAmount; // amount to be transfered to provider
        uint8 v; // v of provider signed message
        bytes32 r; // r of provider signed message
        bytes32 s; // s of provider signed message
        uint256 validUntil; //validity expresses in unix timestamp
        bytes providerData; //data encoded by provider   
    }

    struct consumeMarketFee{
        address consumeMarketFeeAddress;
        address consumeMarketFeeToken; // address of the token marketplace wants to add fee on top
        uint256 consumeMarketFeeAmount; // amount to be transfered to marketFeeCollector
    }

    event OrderStarted(
        address indexed consumer,
        address payer,
        uint256 amount,
        uint256 serviceIndex,
        uint256 timestamp,
        address indexed publishMarketAddress,
        uint256 blockNumber
    );

    event OrderReused(
            bytes32 orderTxId,
            address caller,
            uint256 timestamp,
            uint256 number
    );

    event OrderExecuted( 
        address indexed providerAddress,
        address indexed consumerAddress,
        bytes32 orderTxId,
        bytes providerData,
        bytes providerSignature,
        bytes consumerData,
        bytes consumerSignature,
        uint256 timestamp,
        uint256 blockNumber
    );

    event PublishMarketFeeChanged(
        address caller,
        address PublishMarketFeeAddress,
        address PublishMarketFeeToken,
        uint256 PublishMarketFeeAmount
    );

    // emited for every order
    event PublishMarketFee(
        address indexed PublishMarketFeeAddress,
        address indexed PublishMarketFeeToken,
        uint256 PublishMarketFeeAmount
    );

    // emited for every order
    event ConsumeMarketFee(
        address indexed consumeMarketFeeAddress,
        address indexed consumeMarketFeeToken,
        uint256 consumeMarketFeeAmount
    );

    // emited for every order
    event ProviderFee(
        address indexed providerFeeAddress,
        address indexed providerFeeToken,
        uint256 providerFeeAmount,
        bytes providerData,
        uint8 v, 
        bytes32 r, 
        bytes32 s,
        uint256 validUntil
    );
    

    event MinterProposed(address currentMinter, address newMinter);

    event MinterApproved(address currentMinter, address newMinter);

    event NewPool(
        address poolAddress,
        address ssContract,
        address baseTokenAddress
    );
    event VestingCreated(address indexed datatokenAddress,
        address indexed publisherAddress,
        uint256 vestingEndBlock,
        uint256 totalVestingAmount);
    event NewFixedRate(bytes32 exchangeId, address indexed owner, address exchangeContract, address indexed baseToken);
    event NewDispenser(address dispenserContract);

    event NewPaymentCollector(
        address indexed caller,
        address indexed _newPaymentCollector,
        uint256 timestamp,
        uint256 blockNumber
    );

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
                .deployERC20,
            "ERC20Template: NOT DEPLOYER ROLE"
        );
        _;
    }

    /**
     * @dev initialize
     *      Called prior contract initialization (e.g creating new Datatoken instance)
     *      Calls private _initialize function. Only if contract is not initialized.
     * @param strings_ refers to an array of strings
     *                      [0] = name token
     *                      [1] = symbol
     * @param addresses_ refers to an array of addresses passed by user
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = paymentCollector  initial paymentCollector  for this DT
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
     *                     [1]  = paymentCollector  initial paymentCollector  for this DT
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

        require(uints_[0] != 0, "DatatokenTemplate: Invalid cap value");
        _cap = uints_[0];
        _name = strings_[0];
        _symbol = strings_[1];
        _erc721Address = erc721Address;
        router = factoryAddresses_[2];
        _communityFeeCollector = communityFeeCollector;
        initialized = true;
        // add a default minter, similar to what happens with manager in the 721 contract
        _addMinter(addresses_[0]);
        if (addresses_[1] != address(0)) {
            _setPaymentCollector(addresses_[1]);
            emit NewPaymentCollector(
                msg.sender,
                addresses_[1],
                block.timestamp,
                block.number
            );
        }
        publishMarketFeeAddress = addresses_[2];
        publishMarketFeeToken = addresses_[3];
        publishMarketFeeAmount = uints_[1];
        emit PublishMarketFeeChanged(
            msg.sender,
            publishMarketFeeAddress,
            publishMarketFeeToken,
            publishMarketFeeAmount
        );
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
     * @dev deployPool
     *      Function to deploy new Pool with 1SS. It also has a vesting schedule.
     *     This function can only be called ONCE and ONLY if no token have been minted yet.
     *      Requires baseToken approval
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
                           [5] = poolTemplateAddress
     */

    function deployPool(
        uint256[] memory ssParams,
        uint256[] memory swapFees,
        address[] memory addresses
    ) external onlyERC20Deployer nonReentrant returns (address pool) {
        require(totalSupply() == 0, "ERC20Template: tokens already minted");
        _addMinter(addresses[0]);
        // TODO: confirm minimum number of blocks required
        require(
            ssParams[3] >= IFactoryRouter(router).getMinVestingPeriod(),
            "ERC20Template: Vesting period too low. See FactoryRouter.minVestingPeriodInBlocks"
        );

        address[2] memory tokens = [address(this), addresses[1]];
        pool = IFactoryRouter(router).deployPool(
            tokens,
            ssParams,
            swapFees,
            addresses
        );
        deployedPools.push(pool);
        emit NewPool(pool, addresses[0], addresses[1]);
    }

    /**
     * @dev createFixedRate
     *      Creates a new FixedRateExchange setup.
     * @param fixedPriceAddress fixedPriceAddress
     * @param addresses array of addresses [baseToken,owner,marketFeeCollector]
     * @param uints array of uints [baseTokenDecimals,datatokenDecimals, fixedRate, marketFee, withMint]
     * @return exchangeId
     */
    function createFixedRate(
        address fixedPriceAddress,
        address[] memory addresses,
        uint256[] memory uints
    ) external onlyERC20Deployer nonReentrant returns (bytes32 exchangeId) {
        exchangeId = IFactoryRouter(router).deployFixedRate(
            fixedPriceAddress,
            addresses,
            uints
        );
        // add FixedPriced contract as minter if withMint == true
        if (uints[4] > 0) _addMinter(fixedPriceAddress);
        emit NewFixedRate(exchangeId, addresses[1], fixedPriceAddress, addresses[0]);
        fixedRateExchanges.push(fixedRate(fixedPriceAddress,exchangeId));

    }

    /**
     * @dev createDispenser
     *      Creates a new Dispenser
     * @param _dispenser dispenser contract address
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     * @param withMint - true if we want to allow the dispenser to be a minter
     * @param allowedSwapper - only account that can ask tokens. set address(0) if not required
     */
    function createDispenser(
        address _dispenser,
        uint256 maxTokens,
        uint256 maxBalance,
        bool withMint,
        address allowedSwapper
    ) external onlyERC20Deployer nonReentrant {
        IFactoryRouter(router).deployDispenser(
            _dispenser,
            address(this),
            maxTokens,
            maxBalance,
            msg.sender,
            allowedSwapper
        );
        // add FixedPriced contract as minter if withMint == true
        if (withMint) _addMinter(_dispenser);
        dispensers.push(_dispenser);
        emit NewDispenser(_dispenser);
    }

    /**
     * @dev mint
     *      Only the minter address can call it.
     *      msg.value should be higher than zero and gt or eq minting fee
     * @param account refers to an address that token is going to be minted to.
     * @param value refers to amount of tokens that is going to be minted.
     */
    function mint(address account, uint256 value) external {
        require(permissions[msg.sender].minter, "ERC20Template: NOT MINTER");
        require(
            totalSupply().add(value) <= _cap,
            "DatatokenTemplate: cap exceeded"
        );
        _mint(account, value);
    }

    /**
     * @dev isMinter
     *      Check if an address has the minter role
     * @param account refers to an address that is checked
     */
    function isMinter(address account) external view returns (bool) {
        return (permissions[account].minter);
    }

    
    /**
     * @dev checkProviderFee
     *      Checks if a providerFee structure is valid, signed and 
     *      transfers fee to providerAddress
     * @param _providerFee providerFee structure
     */
    function checkProviderFee(providerFee calldata _providerFee) internal{
        // check if they are signed
        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        bytes32 message = keccak256(
            abi.encodePacked(prefix,
                keccak256(
                    abi.encodePacked(
                        _providerFee.providerData,
                        _providerFee.providerFeeAddress,
                        _providerFee.providerFeeToken,
                        _providerFee.providerFeeAmount,
                        _providerFee.validUntil
                    )
                )
            )
        );
        address signer = ecrecover(message, _providerFee.v, _providerFee.r, _providerFee.s);
        require(signer == _providerFee.providerFeeAddress, "Invalid provider fee");
        emit ProviderFee(
            _providerFee.providerFeeAddress,
            _providerFee.providerFeeToken,
            _providerFee.providerFeeAmount,
            _providerFee.providerData,
            _providerFee.v,
            _providerFee.r,
            _providerFee.s,
            _providerFee.validUntil
        );
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        // Requires approval for the providerFeeToken of providerFeeAmount
        if (
            _providerFee.providerFeeAmount > 0 &&
            _providerFee.providerFeeToken != address(0) &&
            _providerFee.providerFeeAddress != address(0)
        ) {
            uint256 OPCFee = IFactoryRouter(router).getOPCProviderFee();
            uint256 OPCcut = 0;
            if(OPCFee > 0)
                OPCcut = _providerFee.providerFeeAmount.mul(OPCFee).div(BASE);
            uint256 providerCut = _providerFee.providerFeeAmount.sub(OPCcut);

            _pullUnderlying(_providerFee.providerFeeToken,msg.sender,
                address(this),
                _providerFee.providerFeeAmount);
            IERC20(_providerFee.providerFeeToken).safeTransfer(
                _providerFee.providerFeeAddress,
                providerCut
            );
            if(OPCcut > 0){
              IERC20(_providerFee.providerFeeToken).safeTransfer(
                _communityFeeCollector,
                OPCcut
            );  
            }
        }
    }
    
    /**
     * @dev startOrder
     *      called by payer or consumer prior ordering a service consume on a marketplace.
     *      Requires previous approval of consumeFeeToken and publishMarketFeeToken
     * @param consumer is the consumer address (payer could be different address)
     * @param serviceIndex service index in the metadata
     * @param _providerFee provider fee
     * @param _consumeMarketFee consume market fee
     */
    function startOrder(
        address consumer,
        uint256 serviceIndex,
        providerFee calldata _providerFee,
        consumeMarketFee calldata _consumeMarketFee
    ) external nonReentrant {
        uint256 amount = 1e18; // we always pay 1 DT. No more, no less
        uint256 communityFeePublish = 0;
        require(
            balanceOf(msg.sender) >= amount,
            "Not enough datatokens to start Order"
        );
        emit OrderStarted(
            consumer,
            msg.sender,
            amount,
            serviceIndex,
            block.timestamp,
            publishMarketFeeAddress,
            block.number
        );
        // publishMarketFee
        // Requires approval for the publishMarketFeeToken of publishMarketFeeAmount
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        if (
            publishMarketFeeAmount > 0 &&
            publishMarketFeeToken != address(0) &&
            publishMarketFeeAddress != address(0)
        ) {
            _pullUnderlying(publishMarketFeeToken,msg.sender,
                address(this),
                publishMarketFeeAmount);
            uint256 OPCFee = IFactoryRouter(router).getOPCConsumeFee();
            if(OPCFee > 0)
                communityFeePublish = publishMarketFeeAmount.mul(OPCFee).div(BASE); 
            //send publishMarketFee
            IERC20(publishMarketFeeToken).safeTransfer(
                publishMarketFeeAddress,
                publishMarketFeeAmount.sub(communityFeePublish)
            );

            emit PublishMarketFee(
                publishMarketFeeAddress,
                publishMarketFeeToken,
                publishMarketFeeAmount.sub(communityFeePublish)
            );
            //send fee to OPC
            if (communityFeePublish > 0) {
                //since both fees are in the same token, have just one transaction for both, to save gas
                IERC20(publishMarketFeeToken).safeTransfer(
                    _communityFeeCollector,
                    communityFeePublish
                );
                emit PublishMarketFee(
                    _communityFeeCollector,
                    publishMarketFeeToken,
                    communityFeePublish
                );
            }
        }

        // consumeMarketFee
        // Requires approval for the FeeToken 
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        if (
            _consumeMarketFee.consumeMarketFeeAmount > 0 &&
            _consumeMarketFee.consumeMarketFeeToken != address(0) &&
            _consumeMarketFee.consumeMarketFeeAddress != address(0)
        ) {
            _pullUnderlying(_consumeMarketFee.consumeMarketFeeToken,msg.sender,
                address(this),
                _consumeMarketFee.consumeMarketFeeAmount);
            uint256 OPCFee = IFactoryRouter(router).getOPCConsumeFee();
            if(OPCFee > 0)
                communityFeePublish = _consumeMarketFee.consumeMarketFeeAmount.mul(OPCFee).div(BASE); 
            //send publishMarketFee
            IERC20(_consumeMarketFee.consumeMarketFeeToken).safeTransfer(
                _consumeMarketFee.consumeMarketFeeAddress,
                _consumeMarketFee.consumeMarketFeeAmount.sub(communityFeePublish)
            );

            emit ConsumeMarketFee(
                _consumeMarketFee.consumeMarketFeeAddress,
                _consumeMarketFee.consumeMarketFeeToken,
                _consumeMarketFee.consumeMarketFeeAmount.sub(communityFeePublish)
            );
            //send fee to OPC
            if (communityFeePublish > 0) {
                //since both fees are in the same token, have just one transaction for both, to save gas
                IERC20(_consumeMarketFee.consumeMarketFeeToken).safeTransfer(
                    _communityFeeCollector,
                    communityFeePublish
                );
                emit ConsumeMarketFee(
                    _communityFeeCollector,
                    _consumeMarketFee.consumeMarketFeeToken,
                    communityFeePublish
                );
            }
        }
        checkProviderFee(_providerFee);
        
        // send datatoken to publisher
        require(
            transfer(getPaymentCollector(), amount),
            "Failed to send DT to publisher"
        );
    }

    /**
     * @dev reuseOrder
     *      called by payer or consumer having a valid order, but with expired provider access
     *      Pays the provider fee again, but it will not require a new datatoken payment
     *      Requires previous approval of provider fee.
     * @param orderTxId previous valid order
     * @param _providerFee provider feee
     */
    function reuseOrder(
        bytes32 orderTxId,
        providerFee calldata _providerFee
    ) external nonReentrant {
        emit OrderReused(
            orderTxId,
            msg.sender,
            block.timestamp,
            block.number
        );
        checkProviderFee(_providerFee);
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
     * @dev addPaymentManager (can set who's going to collect fee when consuming orders)
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple paymentCollectors
     * @param _paymentManager new minter address
     */

    function addPaymentManager(address _paymentManager)
        external
        onlyERC20Deployer
    {
        _addPaymentManager(_paymentManager);
    }

    /**
     * @dev removePaymentManager
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple paymentManagers
     * @param _paymentManager _paymentManager address to remove
     */

    function removePaymentManager(address _paymentManager)
        external
        onlyERC20Deployer
    {
        _removePaymentManager(_paymentManager);
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
     *      This function allows to remove all minters, feeManagers and reset the paymentCollector
     *
     */

    function cleanPermissions() external onlyNFTOwner {
        _cleanPermissions();
        paymentCollector = address(0);
    }

    /**
     * @dev cleanFrom721()
     *      OnlyNFT(721) Contract can call it.
     *      This function allows to remove all minters, feeManagers and reset the paymentCollector
     *       This function is used when transferring an NFT to a new owner,
     * so that permissions at ERC20level (minter,feeManager,paymentCollector) can be reset.
     *
     */
    function cleanFrom721() external {
        require(
            msg.sender == _erc721Address,
            "ERC20Template: NOT 721 Contract"
        );
        _cleanPermissions();
        paymentCollector = address(0);
    }

    /**
     * @dev setPaymentCollector
     *      Only feeManager can call it
     *      This function allows to set a newPaymentCollector (receives DT when consuming)
            If not set the paymentCollector is the NFT Owner
     * @param _newPaymentCollector new fee collector 
     */

    function setPaymentCollector(address _newPaymentCollector) external {
        //we allow _newPaymentCollector = address(0), because it means that the collector is nft owner
        require(
            permissions[msg.sender].paymentManager ||
                IERC721Template(_erc721Address)
                    .getPermissions(msg.sender)
                    .deployERC20,
            "ERC20Template: NOT PAYMENT MANAGER or OWNER"
        );
        _setPaymentCollector(_newPaymentCollector);
        emit NewPaymentCollector(
            msg.sender,
            _newPaymentCollector,
            block.timestamp,
            block.number
        );
    }

    /**
     * @dev _setPaymentCollector
     * @param _newPaymentCollector new fee collector
     */

    function _setPaymentCollector(address _newPaymentCollector) internal {
        paymentCollector = _newPaymentCollector;
    }

    /**
     * @dev getPublishingMarketFee
     *      Get publishingMarket Fee
     *      This function allows to get the current fee set by the publishing market
     */
    function getPublishingMarketFee()
        external
        view
        returns (
            address,
            address,
            uint256
        )
    {
        return (
            publishMarketFeeAddress,
            publishMarketFeeToken,
            publishMarketFeeAmount
        );
    }

    /**
     * @dev setPublishingMarketFee
     *      Only publishMarketFeeAddress can call it
     *      This function allows to set the fee required by the publisherMarket
     * @param _publishMarketFeeAddress  new _publishMarketFeeAddress
     * @param _publishMarketFeeToken new _publishMarketFeeToken
     * @param _publishMarketFeeAmount new fee amount
     */
    function setPublishingMarketFee(
        address _publishMarketFeeAddress,
        address _publishMarketFeeToken,
        uint256 _publishMarketFeeAmount
    ) external onlyPublishingMarketFeeAddress {
        require(
            _publishMarketFeeAddress != address(0),
            "Invalid _publishMarketFeeAddress address"
        );
           require(
            _publishMarketFeeToken != address(0),
            "Invalid _publishMarketFeeToken address"
        );
        publishMarketFeeAddress = _publishMarketFeeAddress;
        publishMarketFeeToken = _publishMarketFeeToken;
        publishMarketFeeAmount = _publishMarketFeeAmount;
        emit PublishMarketFeeChanged(
            msg.sender,
            _publishMarketFeeAddress,
            _publishMarketFeeToken,
            _publishMarketFeeAmount
        );
    }

    /**
     * @dev getId
     *      Return template id in case we need different ABIs. 
     *      If you construct your own template, please make sure to change the hardcoded value
     */
    function getId() pure public returns (uint8) {
        return 1;
    }

    /**
     * @dev name
     *      It returns the token name.
     * @return Datatoken name.
     */
    function name() public view override returns (string memory) {
        return _name;
    }

    /**
     * @dev symbol
     *      It returns the token symbol.
     * @return Datatoken symbol.
     */
    function symbol() public view override returns (string memory) {
        return _symbol;
    }

    /**
     * @dev getERC721Address
     *      It returns the parent ERC721
     * @return ERC721 address.
     */
    function getERC721Address() public view returns (address) {
        return _erc721Address;
    }

    /**
     * @dev decimals
     *      It returns the token decimals.
     *      how many supported decimal points
     * @return Datatoken decimals.
     */
    function decimals() public pure override returns (uint8) {
        return _decimals;
    }

    /**
     * @dev cap
     *      it returns the capital.
     * @return Datatoken cap.
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
        require(deadline >= block.number, "ERC20DT: EXPIRED");
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
     * @dev getPaymentCollector
     *      It returns the current paymentCollector
     * @return paymentCollector address
     */

    function getPaymentCollector() public view returns (address) {
        if (paymentCollector == address(0)) {
            return IERC721Template(_erc721Address).ownerOf(1);
        } else {
            return paymentCollector;
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
    function withdrawETH() external payable {
        payable(getPaymentCollector()).transfer(address(this).balance);
    }

    /**
     * @dev isERC20Deployer
     *      returns true if address has deployERC20 role
     */
    function isERC20Deployer(address user) public returns (bool deployer) {
        deployer = IERC721Template(_erc721Address)
            .getPermissions(user)
            .deployERC20;
        return (deployer);
    }

    /**
     * @dev getPools
     *      Returns the list of pools created for this datatoken
     */
    function getPools() public view returns(address[] memory) {
        return(deployedPools);
    }
    /**
     * @dev getFixedRates
     *      Returns the list of fixedRateExchanges created for this datatoken
     */
    function getFixedRates() public view returns(fixedRate[] memory) {
        return(fixedRateExchanges);
    }
    /**
     * @dev getDispensers
     *      Returns the list of dispensers created for this datatoken
     */
    function getDispensers() public view returns(address[] memory) {
        return(dispensers);
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


    /**
     * @dev orderExecuted
     *      Providers should call this to prove order execution
     * @param orderTxId order tx
     * @param providerData provider data
     * @param providerSignature provider signature
     * @param consumerData consumer data
     * @param consumerSignature consumer signature
     * @param consumerAddress consumer address
     */
    function orderExecuted(
        bytes32 orderTxId,
        bytes calldata providerData,
        bytes calldata providerSignature,
        bytes calldata consumerData,
        bytes calldata consumerSignature,
        address consumerAddress
    ) external {
        require(msg.sender != consumerAddress, "Provider cannot be the consumer");
        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        bytes32 providerHash = keccak256(
            abi.encodePacked(prefix,
                keccak256(
                    abi.encodePacked(
                        orderTxId,
                        providerData
                    )
                )
            )
        );
        require(ecrecovery(providerHash, providerSignature) == msg.sender, "Provider signature check failed");
        bytes32 consumerHash = keccak256(
            abi.encodePacked(prefix,
                keccak256(
                    abi.encodePacked(
                        consumerData
                    )
                )
            )
        );
        require(ecrecovery(consumerHash, consumerSignature) == consumerAddress, "Consumer signature check failed");
        emit OrderExecuted(msg.sender, consumerAddress ,orderTxId, providerData, providerSignature,
                consumerData, consumerSignature, block.timestamp, block.number);
    }



    function ecrecovery(bytes32 hash, bytes memory sig) pure internal returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;
        if (sig.length != 65) {
          return address(0);
        }
        assembly {
          r := mload(add(sig, 32))
        s := mload(add(sig, 64))
        v := and(mload(add(sig, 65)), 255)
        }
        if (v < 27) {
          v += 27;
        }   
        if (v != 27 && v != 28) {
        return address(0);
        }
        return ecrecover(hash, v, r, s);
    }

}
