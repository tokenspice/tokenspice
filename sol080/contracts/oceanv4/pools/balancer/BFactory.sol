pragma solidity 0.8.10;
// Copyright Balancer, BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "./BPool.sol";
import "./BConst.sol";
import "../../utils/Deployer.sol";
import "../../interfaces/ISideStaking.sol";
import "../../interfaces/IERC20.sol";

/*
 * @title BFactory contract
 * @author Ocean Protocol (with code from Balancer Labs)
 *
 * @dev Ocean implementation of Balancer BPool Factory
 *      BFactory deploys BPool proxy contracts.
 *      New BPool proxy contracts are links to the template contract's bytecode.
 *      Proxy contract functionality is based on Ocean Protocol custom
 *        implementation of ERC1167 standard.
 */
contract BFactory is BConst, Deployer {
    address public opcCollector;

    // mapping(address => bool) internal poolTemplates;
    address[] public poolTemplates;

    event BPoolCreated(
        address indexed newBPoolAddress,
        address indexed registeredBy,
        address indexed datatokenAddress,
        address baseTokenAddress,
        address bpoolTemplateAddress,
        address ssAddress
    );

    event PoolTemplateAdded(
        address indexed caller,
        address indexed contractAddress
    );
    event PoolTemplateRemoved(
        address indexed caller,
        address indexed contractAddress
    );

    /* @dev Called on contract deployment. Cannot be called with zero address.
       @param _bpoolTemplate -- address of a deployed BPool contract. 
       @param _preCreatedPools list of pre-created pools. 
                          It can be only used in case of migration from an old factory contract.
    */
    constructor(
        address _bpoolTemplate,
        address _opcCollector,
        address[] memory _preCreatedPools
    ) public {
        require(
            _bpoolTemplate != address(0),
            "BFactory: invalid bpool template zero address"
        );
        require(_opcCollector != address(0), "BFactory: zero address");

        opcCollector = _opcCollector;
        _addPoolTemplate(_bpoolTemplate);

        if (_preCreatedPools.length > 0) {
            for (uint256 i = 0; i < _preCreatedPools.length; i++) {
                emit BPoolCreated(
                    _preCreatedPools[i],
                    msg.sender,
                    address(0),
                    address(0),
                    address(0),
                    address(0)
                );
            }
        }
    }

    /** 
     * @dev Deploys new BPool proxy contract. 
       Template contract address could not be a zero address. 

     * @param tokens [datatokenAddress, baseTokenAddress]
     * publisherAddress user which will be assigned the vested amount.
     * @param ssParams params for the ssContract. 
     * @param swapFees swapFees (swapFee, swapMarketFee), swapOceanFee will be set automatically later
       marketFeeCollector marketFeeCollector address
       @param addresses // array of addresses passed by the user
       [controller,baseTokenAddress,baseTokenSender,publisherAddress, marketFeeCollector,poolTemplate address]
      @return bpool address of a new proxy BPool contract 
     */

    function newBPool(
        address[2] memory tokens,
        uint256[] memory ssParams,
        uint256[] memory swapFees,
        address[] memory addresses
    ) internal returns (address bpool) {
        require(isPoolTemplate(addresses[5]), "BFactory: Wrong Pool Template");
        address[2] memory feeCollectors = [addresses[4], opcCollector];

        bpool = deploy(addresses[5]);

        require(bpool != address(0), "BFactory: invalid bpool zero address");
        BPool bpoolInstance = BPool(bpool);

        require(
            bpoolInstance.initialize(
                addresses[0], // ss is the pool controller
                address(this),
                swapFees,
                false,
                false,
                tokens,
                feeCollectors
            ),
            "ERR_INITIALIZE_BPOOL"
        );

        //  emit BPoolCreated(bpool, msg.sender,datatokenAddress,baseTokenAddress,bpoolTemplate,controller);

        // requires approval first from baseTokenSender
        require(
            ISideStaking(addresses[0]).newDatatokenCreated(
                tokens[0],
                tokens[1],
                bpool,
                addresses[3], //publisherAddress
                ssParams
            ),
            "ERR_INITIALIZE_SIDESTAKING"
        );

        return bpool;
    }

    /**
     * @dev _addPoolTemplate
     *      Adds an address to the list of pools templates
     *  @param poolTemplate address Contract to be added
     */
    function _addPoolTemplate(address poolTemplate) internal {
        require(
            poolTemplate != address(0),
            "FactoryRouter: Invalid poolTemplate address"
        );
        if (!isPoolTemplate(poolTemplate)) {
            poolTemplates.push(poolTemplate);
            emit PoolTemplateAdded(msg.sender, poolTemplate);
        }
    }

    /**
     * @dev _removeFixedRateContract
     *      Removes an address from the list of pool templates
     *  @param poolTemplate address Contract to be removed
     */
    function _removePoolTemplate(address poolTemplate) internal {
        uint256 i;
        for (i = 0; i < poolTemplates.length; i++) {
            if (poolTemplates[i] == poolTemplate) break;
        }
        if (i < poolTemplates.length) {
            // it's in the array
            for (uint256 c = i; c < poolTemplates.length - 1; c++) {
                poolTemplates[c] = poolTemplates[c + 1];
            }
            poolTemplates.pop();
            emit PoolTemplateRemoved(msg.sender, poolTemplate);
        }
    }

    /**
     * @dev isPoolTemplate
     *      Removes true if address exists in the list of templates
     *  @param poolTemplate address Contract to be checked
     */
    function isPoolTemplate(address poolTemplate) public view returns (bool) {
        for (uint256 i = 0; i < poolTemplates.length; i++) {
            if (poolTemplates[i] == poolTemplate) return true;
        }
        return false;
    }

    /**
     * @dev getPoolTemplates
     *      Returns the list of pool templates
     */
    function getPoolTemplates() public view returns (address[] memory) {
        return (poolTemplates);
    }
}
