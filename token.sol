// SPDX-License-Identifier: MIT
pragma solidity ^ 0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract AirdropToken is ERC20, Ownable {
    // Total token supply fixed at deployment
    uint256 public constant MAX_SUPPLY = 1_000_000 * 10 ** 18;

    // Mapping to track user claim amounts for each airdrop
    mapping(uint256 => mapping(address => uint256)) public claimableAmount;
    // Tracks whether a user has claimed tokens for a specific airdrop
    mapping(uint256 => mapping(address => bool)) public hasClaimed;

    // Current airdrop ID
    uint256 public currentAirdropId;

    // Event for airdrop setup
    event AirdropCreated(uint256 indexed airdropId, uint256 totalTokens);
    // Event for claiming tokens
    event TokensClaimed(uint256 indexed airdropId, address indexed user, uint256 amount);

    constructor() ERC20("Simba", "SBM") Ownable(msg.sender) {
        // Mint the full supply to the owner's wallet
        _mint(msg.sender, MAX_SUPPLY);
    }

    /**
     * @dev Setup an airdrop with allocations for users.
     * Only callable by the owner.
     * @param recipients Array of recipient addresses.
     * @param amounts Array of token amounts for each recipient.
     */
    function setupAirdrop(address[] calldata recipients, uint256[] calldata amounts) external onlyOwner {
        require(recipients.length == amounts.length, "Recipients and amounts mismatch");

        uint256 totalTokens = 0;

        for (uint256 i = 0; i < recipients.length; i++) {
            address recipient = recipients[i];
            uint256 amount = amounts[i];

            require(balanceOf(msg.sender) >= amount, "Not enough tokens for allocation");

            claimableAmount[currentAirdropId][recipient] = amount;
            totalTokens += amount;
        }

        require(balanceOf(msg.sender) >= totalTokens, "Insufficient tokens for airdrop");

        emit AirdropCreated(currentAirdropId, totalTokens);

        // Increment the airdrop ID for the next round
        currentAirdropId++;
    }

    /**
     * @dev Users claim their airdrop tokens.
     * @param airdropId The ID of the airdrop to claim from.
     */
    function claimTokens(uint256 airdropId) external {
        require(airdropId < currentAirdropId, "Invalid airdrop ID");
        require(!hasClaimed[airdropId][msg.sender], "Tokens already claimed");

        uint256 amount = claimableAmount[airdropId][msg.sender];
        require(amount > 0, "No tokens to claim");

        hasClaimed[airdropId][msg.sender] = true;

        _transfer(owner(), msg.sender, amount);

        emit TokensClaimed(airdropId, msg.sender, amount);
    }

    /**
     * @dev Withdraw unclaimed tokens from airdrops.
     * Callable by the owner after the airdrop ends.
     * @param airdropId The ID of the airdrop to recover tokens from.
     * @param recipients Array of recipient addresses to check.
     */
    function recoverUnclaimedTokens(uint256 airdropId, address[] calldata recipients) external onlyOwner {
        require(airdropId < currentAirdropId, "Invalid airdrop ID");

        uint256 unclaimedTokens = 0;

        for (uint256 i = 0; i < recipients.length; i++) {
            address recipient = recipients[i];

            if (!hasClaimed[airdropId][recipient]) {
                unclaimedTokens += claimableAmount[airdropId][recipient];
                claimableAmount[airdropId][recipient] = 0;
            }
        }

        emit AirdropCreated(airdropId, unclaimedTokens);
    }
}