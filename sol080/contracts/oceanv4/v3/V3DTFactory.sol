pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import '../utils/Deployer.sol';
import './IDataTokenTemplate.sol';

/**
 * @title DTFactory contract
 * @author Ocean Protocol Team
 *
 * @dev Implementation of Ocean DataTokens Factory
 *
 *      DTFactory deploys DataToken proxy contracts.
 *      New DataToken proxy contracts are links to the template contract's bytecode.
 *      Proxy contract functionality is based on Ocean Protocol custom implementation of ERC1167 standard.
 */
contract V3DTFactory is Deployer {
    address private tokenTemplate;
    address private communityFeeCollector;
    uint256 private currentTokenCount = 1;

    event TokenCreated(
        address indexed newTokenAddress,
        address indexed templateAddress,
        string indexed tokenName
    );

    event TokenRegistered(
        address indexed tokenAddress,
        string tokenName,
        string tokenSymbol,
        uint256 tokenCap,
        address indexed registeredBy,
        string indexed blob
    );

    /**
     * @dev constructor
     *      Called on contract deployment. Could not be called with zero address parameters.
     * @param _template refers to the address of a deployed DataToken contract.
     * @param _collector refers to the community fee collector address
     */
    constructor(
        address _template,
        address _collector
    ) public {
        require(
            _template != address(0) &&
            _collector != address(0),
            'DTFactory: Invalid template token/community fee collector address'
        );
        tokenTemplate = _template;
        communityFeeCollector = _collector;
    }

    /**
     * @dev Deploys new DataToken proxy contract.
     *      Template contract address could not be a zero address.
     * @param blob any string that hold data/metadata for the new token
     * @param name token name
     * @param symbol token symbol
     * @param cap the maximum total supply
     * @return token address of a new proxy DataToken contract
     */
    function createToken(
        string memory blob,
        string memory name,
        string memory symbol,
        uint256 cap
    )
        public
        returns (address token)
    {
        require(
            cap != 0,
            'DTFactory: zero cap is not allowed'
        );

        token = deploy(tokenTemplate);

        require(
            token != address(0),
            'DTFactory: Failed to perform minimal deploy of a new token'
        );
        IDataTokenTemplate tokenInstance = IDataTokenTemplate(token);
        require(
            tokenInstance.initialize(
                name,
                symbol,
                msg.sender,
                cap,
                blob,
                communityFeeCollector
            ),
            'DTFactory: Unable to initialize token instance'
        );
        emit TokenCreated(token, tokenTemplate, name);
        emit TokenRegistered(
            token,
            name,
            symbol,
            cap,
            msg.sender,
            blob
        );
        currentTokenCount += 1;
    }

    /**
     * @dev get the current token count.
     * @return the current token count
     */
    function getCurrentTokenCount() external view returns (uint256) {
        return currentTokenCount;
    }

    /**
     * @dev get the token template address
     * @return the template address
     */
    function getTokenTemplate() external view returns (address) {
        return tokenTemplate;
    }
}