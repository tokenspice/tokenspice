pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './IDataTokenTemplate.sol';


/**
* @title Metadata
*  
* @dev Metadata stands for Decentralized Document. It allows publishers
*      to publish their dataset metadata in decentralized way.
*      It follows the Ocean DID Document standard: 
*      https://github.com/oceanprotocol/OEPs/blob/master/7/v0.2/README.md
*/
contract V3Metadata {

    event MetadataCreated(
        address indexed dataToken,
        address indexed createdBy,
        bytes flags,
        bytes data
    );
    event MetadataUpdated(
        address indexed dataToken,
        address indexed updatedBy,
        bytes flags,
        bytes data
    );

    modifier onlyDataTokenMinter(address dataToken)
    {
        IDataTokenTemplate token = IDataTokenTemplate(dataToken);
        require(
            token.minter() == msg.sender,
            'Metadata: Invalid DataToken Minter'
        );
        _;
    }

    /**
     * @dev create
     *      creates/publishes new metadata/DDO document on-chain. 
     * @param dataToken refers to data token address
     * @param flags special flags associated with metadata
     * @param data referes to the actual metadata
     */
    function create(
        address dataToken,
        bytes calldata flags,
        bytes calldata data
    ) 
        external
        onlyDataTokenMinter(dataToken)
    {
        emit MetadataCreated(
            dataToken,
            msg.sender,
            flags,
            data
        );
    }

    /**
     * @dev update
     *      allows only datatoken minter(s) to update the DDO/metadata content
     * @param dataToken refers to data token address
     * @param flags special flags associated with metadata
     * @param data referes to the actual metadata
     */
    function update(
        address dataToken,
        bytes calldata flags,
        bytes calldata data
    ) 
        external
        onlyDataTokenMinter(dataToken)
    {
        emit MetadataUpdated(
            dataToken,
            msg.sender,
            flags,
            data
        );
    }
}