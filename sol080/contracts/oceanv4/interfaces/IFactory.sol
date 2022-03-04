pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

interface IFactory {
    function initialize(
        string calldata _name,
        string calldata _symbol,
        address _minter,
        uint256 _cap,
        string calldata blob,
        address collector
    ) external returns (bool);



    function isInitialized() external view returns (bool);


    function createToken(
        uint256 _templateIndex,
        string[] calldata strings,
        address[] calldata addresses,
        uint256[] calldata uints,
        bytes[] calldata bytess
    ) external returns (address token);
    

    function addToERC721Registry(address ERC721address) external;

    function erc721List(address ERC721address) external returns (address);

    function erc20List(address erc20dt) external view returns(bool);


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

    struct PoolData{
        uint256[] ssParams;
        uint256[] swapFees;
        address[] addresses;
    }

    struct FixedData{
        address fixedPriceAddress;
        address[] addresses;
        uint256[] uints;
    }

    struct DispenserData{
        address dispenserAddress;
        uint256 maxTokens;
        uint256 maxBalance;
        bool withMint;
        address allowedSwapper;
    }
    
    function createNftWithErc20(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData
    ) external returns (address , address);

    function createNftWithErc20WithPool(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData,
        PoolData calldata _PoolData
    ) external returns (address, address , address);

    
    function createNftWithErc20WithFixedRate(
         NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData,
        FixedData calldata _FixedData
    ) external returns (address, address , bytes32 );

    
    function createNftWithErc20WithDispenser(
        NftCreateData calldata _NftCreateData,
        ErcCreateData calldata _ErcCreateData,
        DispenserData calldata _DispenserData
    ) external returns (address, address);
}
