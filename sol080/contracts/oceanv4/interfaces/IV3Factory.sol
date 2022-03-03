pragma solidity 0.8.10;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

interface IV3Factory {
        
      function newBPool( 
        address controller, 
        address datatokenAddress, 
        address baseTokenAddress, 
        address publisherAddress, 
        uint256 burnInEndBlock,
        uint256[] memory ssParams) external
        returns (address bpool);
}