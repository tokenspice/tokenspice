pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "./utils/Deployer.sol";
import "./interfaces/IERC721Template.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/access/Ownable.sol";
import "./interfaces/IERC20Template.sol";
import "./interfaces/IERC721Template.sol";
import "./interfaces/IERC20.sol";
import "./utils/SafeERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/utils/math/SafeMath.sol";
import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/security/ReentrancyGuard.sol";
/**
 * @title DTFactory contract
 * @author Ocean Protocol Team
 *
 * @dev Implementation of Ocean datatokens Factory
 *
 *      DTFactory deploys datatoken proxy contracts.
 *      New datatoken proxy contracts are links to the template contract's bytecode.
 *      Proxy contract functionality is based on Ocean Protocol custom implementation of ERC1167 standard.
 */
contract ERC721Factory is Deployer, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;
    address private communityFeeCollector;
    uint256 private currentNFTCount;
    address private erc20Factory;
    uint256 private nftTemplateCount;

    struct Template {
        address templateAddress;
        bool isActive;
    }

    mapping(uint256 => Template) public nftTemplateList;

    mapping(uint256 => Template) public templateList;

    mapping(address => address) public erc721List;

    mapping(address => bool) public erc20List;

    event NFTCreated(
        address indexed newTokenAddress,
        address indexed templateAddress,
        string tokenName,
        address admin,
        string symbol,
        string tokenURI
    );

       uint256 private currentTokenCount = 0;
    uint256 public templateCount;
    address public router;

    event Template721Added(address indexed _templateAddress, uint256 indexed nftTemplateCount);
    event Template20Added(address indexed _templateAddress, uint256 indexed nftTemplateCount);
  //stored here only for ABI reasons
    event TokenCreated(
        address indexed newTokenAddress,
        address indexed templateAddress,
        string name,
        string symbol,
        uint256 cap,
        address creator
    );  
    
    event NewPool(
        address poolAddress,
        address ssContract,
        address baseTokenAddress
    );


    event NewFixedRate(bytes32 exchangeId, address indexed owner, address exchangeContract, address indexed baseToken);
    event NewDispenser(address dispenserContract);

    event DispenserCreated(  // emited when a dispenser is created
        address indexed datatokenAddress,
        address indexed owner,
        uint256 maxTokens,
        uint256 maxBalance,
        address allowedSwapper
    );
    

    /**
     * @dev constructor
     *      Called on contract deployment. Could not be called with zero address parameters.
     * @param _template refers to the address of a deployed datatoken contract.
     * @param _collector refers to the community fee collector address
     * @param _router router contract address
     */
    constructor(
        address _template721,
        address _template,
        address _collector,
        address _router
    ) {
        require(
            _template != address(0) &&
                _collector != address(0) &&
                _template721 != address(0),
            "ERC721DTFactory: Invalid template token/community fee collector address"
        );
        require(_router != address(0), "ERC721DTFactory: Invalid router address");
        add721TokenTemplate(_template721);
        addTokenTemplate(_template);
        router = _router;
        communityFeeCollector = _collector;
    }


    /**
     * @dev deployERC721Contract
     *      
     * @param name NFT name
     * @param symbol NFT Symbol
     * @param _templateIndex template index we want to use
     * @param additionalERC20Deployer if != address(0), we will add it with ERC20Deployer role
     * @param additionalMetaDataUpdater if != address(0), we will add it with updateMetadata role
     */

    function deployERC721Contract(
        string memory name,
        string memory symbol,
        uint256 _templateIndex,
        address additionalERC20Deployer,
        address additionalMetaDataUpdater,
        string memory tokenURI
    ) public returns (address token) {
        require(
            _templateIndex <= nftTemplateCount && _templateIndex != 0,
            "ERC721DTFactory: Template index doesnt exist"
        );
        Template memory tokenTemplate = nftTemplateList[_templateIndex];

        require(
            tokenTemplate.isActive,
            "ERC721DTFactory: ERC721Token Template disabled"
        );

        token = deploy(tokenTemplate.templateAddress);

        require(
            token != address(0),
            "ERC721DTFactory: Failed to perform minimal deploy of a new token"
        );
       
        erc721List[token] = token;

        IERC721Template tokenInstance = IERC721Template(token);
        require(
            tokenInstance.initialize(
                msg.sender,
                name,
                symbol,
                address(this),
                additionalERC20Deployer,
                additionalMetaDataUpdater,
                tokenURI
            ),
            "ERC721DTFactory: Unable to initialize token instance"
        );

        emit NFTCreated(token, tokenTemplate.templateAddress, name, msg.sender, symbol, tokenURI);
        currentNFTCount += 1;
    }
    
    /**
     * @dev get the current token count.
     * @return the current token count
     */
    function getCurrentNFTCount() external view returns (uint256) {
        return currentNFTCount;
    }

    /**
     * @dev get the token template Object
     * @param _index template Index
     * @return the template struct
     */
    function getNFTTemplate(uint256 _index)
        external
        view
        returns (Template memory)
    {
        Template memory template = nftTemplateList[_index];
        return template;
    }

      /**
     * @dev add a new NFT Template.
      Only Factory Owner can call it
     * @param _templateAddress new template address
     * @return the actual template count
     */
    
    function add721TokenTemplate(address _templateAddress)
        public
        onlyOwner
        returns (uint256)
    {
        require(
            _templateAddress != address(0),
            "ERC721DTFactory: ERC721 template address(0) NOT ALLOWED"
        );
        require(isContract(_templateAddress), "ERC721Factory: NOT CONTRACT");
        nftTemplateCount += 1;
        Template memory template = Template(_templateAddress, true);
        nftTemplateList[nftTemplateCount] = template;
        emit Template721Added(_templateAddress,nftTemplateCount);
        return nftTemplateCount;
    }
      /**
     * @dev reactivate a disabled NFT Template.
            Only Factory Owner can call it
     * @param _index index we want to reactivate
     */
    
    // function to activate a disabled token.
    function reactivate721TokenTemplate(uint256 _index) external onlyOwner {
        require(
            _index <= nftTemplateCount && _index != 0,
            "ERC721DTFactory: Template index doesnt exist"
        );
        Template storage template = nftTemplateList[_index];
        template.isActive = true;
    }

      /**
     * @dev disable an NFT Template.
      Only Factory Owner can call it
     * @param _index index we want to disable
     */
    function disable721TokenTemplate(uint256 _index) external onlyOwner {
        require(
            _index <= nftTemplateCount && _index != 0,
            "ERC721DTFactory: Template index doesnt exist"
        );
        Template storage template = nftTemplateList[_index];
        template.isActive = false;
    }

    function getCurrentNFTTemplateCount() external view returns (uint256) {
        return nftTemplateCount;
    }

    /**
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize, which returns 0 for contracts in
        // construction, since the code is only stored at the end of the
        // constructor execution.

        uint256 size;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            size := extcodesize(account)
        }
        return size > 0;
    }

 
    struct tokenStruct{
        string[] strings;
        address[] addresses;
        uint256[] uints;
        bytes[] bytess;
        address owner;
    }
    /**
     * @dev Deploys new datatoken proxy contract.
     *      This function is not called directly from here. It's called from the NFT contract.
            An NFT contract can deploy multiple ERC20 tokens.
     * @param _templateIndex ERC20Template index 
     * @param strings refers to an array of strings
     *                      [0] = name
     *                      [1] = symbol
     * @param addresses refers to an array of addresses
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = feeManager initial feeManager for this DT
     *                     [2]  = publishing Market Address
     *                     [3]  = publishing Market Fee Token
     * @param uints  refers to an array of uints
     *                     [0] = cap_ the total ERC20 cap
     *                     [1] = publishing Market Fee Amount
     * @param bytess  refers to an array of bytes, not in use now, left for future templates
     * @return token address of a new proxy datatoken contract
     */
    function createToken(
        uint256 _templateIndex,
        string[] memory strings,
        address[] memory addresses,
        uint256[] memory uints,
        bytes[] memory bytess
    ) external returns (address token) {
        require(
            erc721List[msg.sender] == msg.sender,
            "ERC721Factory: ONLY ERC721 INSTANCE FROM ERC721FACTORY"
        );
        token = _createToken(_templateIndex, strings, addresses, uints, bytess, msg.sender);
        
    }
    function _createToken(
        uint256 _templateIndex,
        string[] memory strings,
        address[] memory addresses,
        uint256[] memory uints,
        bytes[] memory bytess,
        address owner
    ) internal returns (address token) {
        require(uints[0] != 0, "ERC20Factory: zero cap is not allowed");
        require(
            _templateIndex <= templateCount && _templateIndex != 0,
            "ERC20Factory: Template index doesnt exist"
        );
        Template memory tokenTemplate = templateList[_templateIndex];

        require(
            tokenTemplate.isActive,
            "ERC20Factory: ERC721Token Template disabled"
        );
        token = deploy(tokenTemplate.templateAddress);
        erc20List[token] = true;

        require(
            token != address(0),
            "ERC721Factory: Failed to perform minimal deploy of a new token"
        );
        emit TokenCreated(token, tokenTemplate.templateAddress, strings[0], strings[1], uints[0], owner);
        currentTokenCount += 1;
        tokenStruct memory tokenData = tokenStruct(strings,addresses,uints,bytess,owner); 
        // tokenData.strings = strings;
        // tokenData.addresses = addresses;
        // tokenData.uints = uints;
        // tokenData.owner = owner;
        // tokenData.bytess = bytess;
        _createTokenStep2(token, tokenData);
    }

    function _createTokenStep2(address token, tokenStruct memory tokenData) internal {
        
        IERC20Template tokenInstance = IERC20Template(token);
        address[] memory factoryAddresses = new address[](3);
        factoryAddresses[0] = tokenData.owner;
        
        factoryAddresses[1] = communityFeeCollector;
        
        factoryAddresses[2] = router;
        
        require(
            tokenInstance.initialize(
                tokenData.strings,
                tokenData.addresses,
                factoryAddresses,
                tokenData.uints,
                tokenData.bytess
            ),
            "ERC20Factory: Unable to initialize token instance"
        );
        
    }

    /**
     * @dev get the current ERC20token deployed count.
     * @return the current token count
     */
    function getCurrentTokenCount() external view returns (uint256) {
        return currentTokenCount;
    }

    /**
     * @dev get the current ERC20token template.
      @param _index template Index
     * @return the token Template Object
     */

    function getTokenTemplate(uint256 _index)
        external
        view
        returns (Template memory)
    {
        Template memory template = templateList[_index];
        require(
            _index <= templateCount && _index != 0,
            "ERC20Factory: Template index doesnt exist"
        );
        return template;
    }

    /**
     * @dev add a new ERC20Template.
      Only Factory Owner can call it
     * @param _templateAddress new template address
     * @return the actual template count
     */

    
    function addTokenTemplate(address _templateAddress)
        public
        onlyOwner
        returns (uint256)
    {
        require(
            _templateAddress != address(0),
            "ERC20Factory: ERC721 template address(0) NOT ALLOWED"
        );
        require(isContract(_templateAddress), "ERC20Factory: NOT CONTRACT");
        templateCount += 1;
        Template memory template = Template(_templateAddress, true);
        templateList[templateCount] = template;
        emit Template20Added(_templateAddress, templateCount);
        return templateCount;
    }

     /**
     * @dev disable an ERC20Template.
      Only Factory Owner can call it
     * @param _index index we want to disable
     */

    function disableTokenTemplate(uint256 _index) external onlyOwner {
        Template storage template = templateList[_index];
        template.isActive = false;
    }


     /**
     * @dev reactivate a disabled ERC20Template.
      Only Factory Owner can call it
     * @param _index index we want to reactivate
     */

    // function to activate a disabled token.
    function reactivateTokenTemplate(uint256 _index) external onlyOwner {
        require(
            _index <= templateCount && _index != 0,
            "ERC20DTFactory: Template index doesnt exist"
        );
        Template storage template = templateList[_index];
        template.isActive = true;
    }

    // if templateCount is public we could remove it, or set templateCount to private
    function getCurrentTemplateCount() external view returns (uint256) {
        return templateCount;
    }

    struct tokenOrder {
        address tokenAddress;
        address consumer;
        uint256 serviceIndex;
        IERC20Template.providerFee _providerFee;
        IERC20Template.consumeMarketFee _consumeMarketFee;
    }

    /**
     * @dev startMultipleTokenOrder
     *      Used as a proxy to order multiple services
     *      Users can have inifinite approvals for fees for factory instead of having one approval/ erc20 contract
     *      Requires previous approval of all :
     *          - consumeFeeTokens
     *          - publishMarketFeeTokens
     *          - erc20 datatokens
     *          - providerFees
     * @param orders an array of struct tokenOrder
     */
    function startMultipleTokenOrder(
        tokenOrder[] memory orders
    ) external nonReentrant {
        // TODO: to avoid DOS attack, we set a limit to maximum order (50 ?)
        require(orders.length <= 50, 'ERC721Factory: Too Many Orders');
        // TO DO.  We can do better here , by groupping publishMarketFeeTokens and consumeFeeTokens and have a single 
        // transfer for each one, instead of doing it per dt..
        for (uint256 i = 0; i < orders.length; i++) {
            (address publishMarketFeeAddress, address publishMarketFeeToken, uint256 publishMarketFeeAmount) 
                = IERC20Template(orders[i].tokenAddress).getPublishingMarketFee();
            
            // check if we have publishFees, if so transfer them to us and approve dttemplate to take them
            if (publishMarketFeeAmount > 0 && publishMarketFeeToken!=address(0) 
            && publishMarketFeeAddress!=address(0)) {
                _pullUnderlying(publishMarketFeeToken,msg.sender,
                    address(this),
                    publishMarketFeeAmount);
                IERC20(publishMarketFeeToken).safeIncreaseAllowance(orders[i].tokenAddress, publishMarketFeeAmount);
            }
            // check if we have consumeMarketFee, if so transfer them to us and approve dttemplate to take them
            if (orders[i]._consumeMarketFee.consumeMarketFeeAmount > 0
            && orders[i]._consumeMarketFee.consumeMarketFeeAddress!=address(0) 
            && orders[i]._consumeMarketFee.consumeMarketFeeToken!=address(0)) {
                _pullUnderlying(orders[i]._consumeMarketFee.consumeMarketFeeToken,msg.sender,
                    address(this),
                    orders[i]._consumeMarketFee.consumeMarketFeeAmount);
                IERC20(orders[i]._consumeMarketFee.consumeMarketFeeToken)
                .safeIncreaseAllowance(orders[i].tokenAddress, orders[i]._consumeMarketFee.consumeMarketFeeAmount);
            }
            // handle provider fees
            if (orders[i]._providerFee.providerFeeAmount > 0 && orders[i]._providerFee.providerFeeToken!=address(0) 
            && orders[i]._providerFee.providerFeeAddress!=address(0)) {
                _pullUnderlying(orders[i]._providerFee.providerFeeToken,msg.sender,
                    address(this),
                    orders[i]._providerFee.providerFeeAmount);
                IERC20(orders[i]._providerFee.providerFeeToken)
                .safeIncreaseAllowance(orders[i].tokenAddress, orders[i]._providerFee.providerFeeAmount);
            }
            // transfer erc20 datatoken from consumer to us
            _pullUnderlying(orders[i].tokenAddress,msg.sender,
                    address(this),
                    1e18);
            IERC20Template(orders[i].tokenAddress).startOrder(
                orders[i].consumer,
                orders[i].serviceIndex,
                orders[i]._providerFee,
                orders[i]._consumeMarketFee
            );
        }
    }

    struct reuseTokenOrder {
        address tokenAddress;
        bytes32 orderTxId;
        IERC20Template.providerFee _providerFee;
    }
    /**
     * @dev reuseMultipleTokenOrder
     *      Used as a proxy to order multiple reuses
     *      Users can have inifinite approvals for fees for factory instead of having one approval/ erc20 contract
     *      Requires previous approval of all :
     *          - consumeFeeTokens
     *          - publishMarketFeeTokens
     *          - erc20 datatokens
     *          - providerFees
     * @param orders an array of struct tokenOrder
     */
    function reuseMultipleTokenOrder(
        reuseTokenOrder[] memory orders
    ) external nonReentrant {
        // TODO: to avoid DOS attack, we set a limit to maximum order (50 ?)
        require(orders.length <= 50, 'ERC721Factory: Too Many Orders');
        // TO DO.  We can do better here , by groupping publishMarketFeeTokens and consumeFeeTokens and have a single 
        // transfer for each one, instead of doing it per dt..
        for (uint256 i = 0; i < orders.length; i++) {
            // handle provider fees
            if (orders[i]._providerFee.providerFeeAmount > 0 && orders[i]._providerFee.providerFeeToken!=address(0) 
            && orders[i]._providerFee.providerFeeAddress!=address(0)) {
                _pullUnderlying(orders[i]._providerFee.providerFeeToken,msg.sender,
                    address(this),
                    orders[i]._providerFee.providerFeeAmount);
                IERC20(orders[i]._providerFee.providerFeeToken)
                .safeIncreaseAllowance(orders[i].tokenAddress, orders[i]._providerFee.providerFeeAmount);
            }
        
            IERC20Template(orders[i].tokenAddress).reuseOrder(
                orders[i].orderTxId,
                orders[i]._providerFee
            );
        }
    }

    // helper functions to save number of transactions
    struct NftCreateData{
        string name;
        string symbol;
        uint256 templateIndex;
        string tokenURI;
    }
    struct ErcCreateData{
        uint256 templateIndex;
        string[] strings;
        address[] addresses;
        uint256[] uints;
        bytes[] bytess;
    }
    
    

    
  
    /**
     * @dev createNftWithErc20
     *      Creates a new NFT, then a ERC20,all in one call
     * @param _NftCreateData input data for nft creation
     * @param _ErcCreateData input data for erc20 creation
     
     */
    function createNftWithErc20(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData
    ) external nonReentrant returns (address erc721Address, address erc20Address){
        //we are adding ourselfs as a ERC20 Deployer, because we need it in order to deploy the pool
        erc721Address = deployERC721Contract(
            _NftCreateData.name,
            _NftCreateData.symbol,
            _NftCreateData.templateIndex,
            address(this),
            address(0),
            _NftCreateData.tokenURI);
        erc20Address = IERC721Template(erc721Address).createERC20(
            _ErcCreateData.templateIndex,
            _ErcCreateData.strings,
            _ErcCreateData.addresses,
            _ErcCreateData.uints,
            _ErcCreateData.bytess
        );
        // remove our selfs from the erc20DeployerRole
        IERC721Template(erc721Address).removeFromCreateERC20List(address(this));
    }

    struct PoolData{
        uint256[] ssParams;
        uint256[] swapFees;
        address[] addresses;
    }

    /**
     * @dev createNftWithErc20WithPool
     *      Creates a new NFT, then a ERC20, then a Pool, all in one call
     *      Use this carefully, because if Pool creation fails, you are still going to pay a lot of gas
     * @param _NftCreateData input data for NFT Creation
     * @param _ErcCreateData input data for ERC20 Creation
     * @param _PoolData input data for Pool Creation
     */
    function createNftWithErc20WithPool(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData,
        PoolData calldata _PoolData
    ) external nonReentrant returns (address erc721Address, address erc20Address, address poolAddress){
        _pullUnderlying(_PoolData.addresses[1],msg.sender,
                    address(this),
                    _PoolData.ssParams[4]);
        //we are adding ourselfs as a ERC20 Deployer, because we need it in order to deploy the pool
        erc721Address = deployERC721Contract(
            _NftCreateData.name,
            _NftCreateData.symbol,
            _NftCreateData.templateIndex,
            address(this),
            address(0),
             _NftCreateData.tokenURI);
        erc20Address = IERC721Template(erc721Address).createERC20(
            _ErcCreateData.templateIndex,
            _ErcCreateData.strings,
            _ErcCreateData.addresses,
            _ErcCreateData.uints,
            _ErcCreateData.bytess
        );
        // allow router to take the liquidity
        IERC20(_PoolData.addresses[1]).safeIncreaseAllowance(router,_PoolData.ssParams[4]);
      
        poolAddress = IERC20Template(erc20Address).deployPool(
            _PoolData.ssParams,
            _PoolData.swapFees,
           _PoolData.addresses
        );
        // remove our selfs from the erc20DeployerRole
        IERC721Template(erc721Address).removeFromCreateERC20List(address(this));
    
    }

    struct FixedData{
        address fixedPriceAddress;
        address[] addresses;
        uint256[] uints;
    }
    /**
     * @dev createNftWithErc20WithFixedRate
     *      Creates a new NFT, then a ERC20, then a FixedRateExchange, all in one call
     *      Use this carefully, because if Fixed Rate creation fails, you are still going to pay a lot of gas
     * @param _NftCreateData input data for NFT Creation
     * @param _ErcCreateData input data for ERC20 Creation
     * @param _FixedData input data for FixedRate Creation
     */
    function createNftWithErc20WithFixedRate(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData,
        FixedData calldata _FixedData
    ) external nonReentrant returns (address erc721Address, address erc20Address, bytes32 exchangeId){
        //we are adding ourselfs as a ERC20 Deployer, because we need it in order to deploy the fixedrate
        erc721Address = deployERC721Contract(
            _NftCreateData.name,
            _NftCreateData.symbol,
            _NftCreateData.templateIndex,
            address(this),
            address(0),
             _NftCreateData.tokenURI);
        erc20Address = IERC721Template(erc721Address).createERC20(
            _ErcCreateData.templateIndex,
            _ErcCreateData.strings,
            _ErcCreateData.addresses,
            _ErcCreateData.uints,
            _ErcCreateData.bytess
        );
        exchangeId = IERC20Template(erc20Address).createFixedRate(
            _FixedData.fixedPriceAddress,
            _FixedData.addresses,
            _FixedData.uints
            );
        // remove our selfs from the erc20DeployerRole
        IERC721Template(erc721Address).removeFromCreateERC20List(address(this));
    }

    struct DispenserData{
        address dispenserAddress;
        uint256 maxTokens;
        uint256 maxBalance;
        bool withMint;
        address allowedSwapper;
    }
    /**
     * @dev createNftWithErc20WithDispenser
     *      Creates a new NFT, then a ERC20, then a Dispenser, all in one call
     *      Use this carefully
     * @param _NftCreateData input data for NFT Creation
     * @param _ErcCreateData input data for ERC20 Creation
     * @param _DispenserData input data for Dispenser Creation
     */
    function createNftWithErc20WithDispenser(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData,
        DispenserData calldata _DispenserData
    ) external nonReentrant returns (address erc721Address, address erc20Address){
        //we are adding ourselfs as a ERC20 Deployer, because we need it in order to deploy the fixedrate
        erc721Address = deployERC721Contract(
            _NftCreateData.name,
            _NftCreateData.symbol,
            _NftCreateData.templateIndex,
            address(this),
            address(0),
             _NftCreateData.tokenURI);
        erc20Address = IERC721Template(erc721Address).createERC20(
            _ErcCreateData.templateIndex,
            _ErcCreateData.strings,
            _ErcCreateData.addresses,
            _ErcCreateData.uints,
            _ErcCreateData.bytess
        );
        IERC20Template(erc20Address).createDispenser(
            _DispenserData.dispenserAddress,
            _DispenserData.maxTokens,
            _DispenserData.maxBalance,
            _DispenserData.withMint,
            _DispenserData.allowedSwapper
            );
        // remove our selfs from the erc20DeployerRole
        IERC721Template(erc721Address).removeFromCreateERC20List(address(this));
    }


    
    struct MetaData {
        uint8 _metaDataState;
        string _metaDataDecryptorUrl;
        string _metaDataDecryptorAddress;
        bytes flags;
        bytes data;
        bytes32 _metaDataHash;
        IERC721Template.metaDataProof[] _metadataProofs;
    }

    /**
     * @dev createNftWithMetaData
     *      Creates a new NFT, then sets the metadata, all in one call
     *      Use this carefully
     * @param _NftCreateData input data for NFT Creation
     * @param _MetaData input metadata
     */
    function createNftWithMetaData(
        NftCreateData calldata _NftCreateData,
        MetaData calldata _MetaData
    ) external nonReentrant returns (address erc721Address){
        //we are adding ourselfs as a ERC20 Deployer, because we need it in order to deploy the fixedrate
        erc721Address = deployERC721Contract(
            _NftCreateData.name,
            _NftCreateData.symbol,
            _NftCreateData.templateIndex,
            address(0),
            address(this),
             _NftCreateData.tokenURI);
        // set metadata
        IERC721Template(erc721Address).setMetaData(_MetaData._metaDataState, _MetaData._metaDataDecryptorUrl
        , _MetaData._metaDataDecryptorAddress, _MetaData.flags, 
        _MetaData.data,_MetaData._metaDataHash, _MetaData._metadataProofs);
        // remove our selfs from the erc20DeployerRole
        IERC721Template(erc721Address).removeFromMetadataList(address(this));
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
