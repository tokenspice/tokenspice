pragma solidity >=0.5.7;
pragma experimental ABIEncoderV2;
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


}
