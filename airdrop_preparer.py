import json
from decimal import Decimal, getcontext

# Set precision high enough to handle large token calculations
getcontext().prec = 50

def prepare_airdrop(json_file_path, tokens_to_airdrop):
    """
    Reads user points from a JSON file, calculates each user's share of the airdrop,
    and prints two lists: recipients and corresponding token amounts.

    Parameters:
    - json_file_path (str): Path to the JSON file containing user data.
    - tokens_to_airdrop (int or float): Total number of tokens to distribute.
    """
    # Load user data from JSON file
    try:
        with open(json_file_path, 'r') as file:
            user_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} does not exist.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file {json_file_path} is not a valid JSON file.")
        return

    # Extract points and addresses
    users = []
    total_points = Decimal(0)
    for username, info in user_data.items():
        points = Decimal(info.get("points", 0))
        wallet_address = info.get("wallet_address", "")
        if not wallet_address:
            print(f"Warning: User '{username}' does not have a wallet address. Skipping.")
            continue
        users.append({
            "username": username,
            "points": points,
            "wallet_address": wallet_address
        })
        total_points += points

    if total_points == 0:
        print("Error: Total points of all users is zero. Cannot perform airdrop.")
        return

    # Calculate token distribution
    recipients = []
    amounts = []
    scaling_factor = Decimal(10**18)
    tokens_to_airdrop_decimal = Decimal(tokens_to_airdrop)

    for user in users:
        fraction = user["points"] / total_points
        token_amount = (fraction * tokens_to_airdrop_decimal * scaling_factor).to_integral_value()
        recipients.append(f'"{user["wallet_address"]}"')
        amounts.append(str(token_amount))

    # Print the lists in Solidity array format
    print("\n// Recipients Array")
    print("address[] memory recipients = new address[](" + str(len(recipients)) + ");")
    for idx, address in enumerate(recipients):
        print(f"recipients[{idx}] = {address};")

    print("\n// Amounts Array")
    print("uint256[] memory amounts = new uint256[](" + str(len(amounts)) + ");")
    for idx, amount in enumerate(amounts):
        print(f"amounts[{idx}] = {amount};")

    # Alternatively, print as Solidity array literals
    print("\n// Alternatively, as Solidity array literals:")
    print("address[] memory recipients = [" + ", ".join(recipients) + "];")
    print("uint256[] memory amounts = [" + ", ".join(amounts) + "];")

if __name__ == "__main__":
    # Example usage:
    # Define the path to your JSON file
    json_file = "user_points.json"

    # Define the total tokens to airdrop (adjust as needed)
    total_tokens = 1000  # Example: 1000 tokens

    prepare_airdrop(json_file, total_tokens)
