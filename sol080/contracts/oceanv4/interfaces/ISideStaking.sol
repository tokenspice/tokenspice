// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

pragma solidity >=0.5.7;

interface ISideStaking {


    function newDataTokenCreated(
        address datatokenAddress,
        address basetokenAddress,
        address poolAddress,
        address publisherAddress,
        uint256[] calldata ssParams
    ) external returns (bool);

    function getDataTokenCirculatingSupply(address datatokenAddress)
        external
        view
        returns (uint256);

    function getPublisherAddress(address datatokenAddress)
        external
        view
        returns (address);

    function getBaseTokenAddress(address datatokenAddress)
        external
        view
        returns (address);

    function getPoolAddress(address datatokenAddress)
        external
        view
        returns (address);

    function getBaseTokenBalance(address datatokenAddress)
        external
        view
        returns (uint256);

    function getDataTokenBalance(address datatokenAddress)
        external
        view
        returns (uint256);

    function getvestingEndBlock(address datatokenAddress)
        external
        view
        returns (uint256);

    function getvestingAmount(address datatokenAddress)
        external
        view
        returns (uint256);

    function getvestingLastBlock(address datatokenAddress)
        external
        view
        returns (uint256);

    function getvestingAmountSoFar(address datatokenAddress)
        external
        view
        returns (uint256);



    function canStake(
        address datatokenAddress,
        address stakeToken,
        uint256 amount
    ) external view returns (bool);

    function Stake(
        address datatokenAddress,
        address stakeToken,
        uint256 amount
    ) external;

    function canUnStake(
        address datatokenAddress,
        address stakeToken,
        uint256 amount
    ) external view returns (bool);

    function UnStake(
        address datatokenAddress,
        address stakeToken,
        uint256 amount,
        uint256 poolAmountIn
    ) external;

    function notifyFinalize(address datatokenAddress) external;


    function swapExactAmountIn(
        address datatokenAddress,
        address userAddress,
        address tokenIn,
        uint256 tokenAmountIn,
        address tokenOut,
        uint256 minAmountOut
    ) external returns (uint256 tokenAmountOut);

    function swapExactAmountOut(
        address datatokenAddress,
        address userAddress,
        address tokenIn,
        uint256 maxTokenAmountIn,
        address tokenOut,
        uint256 amountOut
    ) external returns (uint256 tokenAmountIn);
}
