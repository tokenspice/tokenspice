// SPDX-License-Identifier: Unknown
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

pragma solidity 0.8.10;

interface IPool {
    function getDataTokenAddress() external view returns (address);

    function getBaseTokenAddress() external view returns (address);

    function getController() external view returns (address);

    function setup(
        address dataTokenAaddress,
        uint256 dataTokenAmount,
        uint256 dataTokenWeight,
        address baseTokenAddress,
        uint256 baseTokenAmount,
        uint256 baseTokenWeight
    ) external;

    function swapExactAmountIn(
        address[3] calldata tokenInOutMarket, //[tokenIn,tokenOut,marketFeeAddress]
        uint256[4] calldata amountsInOutMaxFee //[tokenAmountIn,minAmountOut,maxPrice,_swapMarketFee]
    ) external returns (uint256 tokenAmountOut, uint256 spotPriceAfter);

    function swapExactAmountOut(
        address[3] calldata tokenInOutMarket, // [tokenIn,tokenOut,marketFeeAddress]
        uint256[4] calldata amountsInOutMaxFee // [maxAmountIn,tokenAmountOut,maxPrice,_swapMarketFee]
    ) external returns (uint256 tokenAmountIn, uint256 spotPriceAfter);

    function getAmountInExactOut(
        address tokenIn,
        address tokenOut,
        uint256 tokenAmountOut,
        uint256 _swapMarketFee
    ) external view returns (uint256 tokenAmountIn);

    function getAmountOutExactIn(
        address tokenIn,
        address tokenOut,
        uint256 tokenAmountIn,
        uint256 _swapMarketFee
    )
        external
        view
        returns (
            //  _viewlock_
            uint256 tokenAmountOut
        );

    function setSwapFee(uint256 swapFee) external;
}
