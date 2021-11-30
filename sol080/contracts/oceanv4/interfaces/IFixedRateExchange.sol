pragma solidity >=0.5.7;

interface IFixedRateExchange {
    function createWithDecimals(
        address dataToken,
        address[] calldata addresses, // [baseToken,owner,marketFeeCollector]
        uint256[] calldata uints // [baseTokenDecimals,dataTokenDecimals, fixedRate, marketFee]
    ) external returns (bytes32 exchangeId);

    function buyDT(bytes32 exchangeId, uint256 dataTokenAmount, uint256 maxBaseTokenAmount) external;
    function sellDT(bytes32 exchangeId, uint256 dataTokenAmount, uint256 minBaseTokenAmount) external;

    function getAllowedSwapper(bytes32 exchangeId) external view returns (address allowedSwapper);
    function getExchange(bytes32 exchangeId)
        external
        view
        returns (
            address exchangeOwner,
            address dataToken,
            uint256 dtDecimals,
            address baseToken,
            uint256 btDecimals,
            uint256 fixedRate,
            bool active,
            uint256 dtSupply,
            uint256 btSupply,
            uint256 dtBalance,
            uint256 btBalance,
            bool withMint
            //address allowedSwapper
        );

    function getFeesInfo(bytes32 exchangeId)
        external
        view
        returns (
            uint256 marketFee,
            address marketFeeCollector,
            uint256 opfFee,
            uint256 marketFeeAvailable,
            uint256 oceanFeeAvailable
        );

    function isActive(bytes32 exchangeId) external view returns (bool);

    function calcBaseInGivenOutDT(bytes32 exchangeId, uint256 dataTokenAmount)
        external
        view
        returns (
            uint256 baseTokenAmount,
            uint256 baseTokenAmountBeforeFee,
            uint256 oceanFeeAmount,
            uint256 marketFeeAmount
        );
    function updateMarketFee(bytes32 exchangeId, uint256 _newMarketFee) external;
    function updateMarketFeeCollector(bytes32 exchangeId, address _newMarketCollector) external;
    function setAllowedSwapper(bytes32 exchangeId, address newAllowedSwapper) external;
}
