pragma solidity >=0.6.0;


interface IV3Factory {
        
      function newBPool( 
        address controller, 
        address datatokenAddress, 
        address basetokenAddress, 
        address publisherAddress, 
        uint256 burnInEndBlock,
        uint256[] memory ssParams) external
        returns (address bpool);
}