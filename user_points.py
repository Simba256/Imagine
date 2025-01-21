# user_points.py
import json
import os
import logging

POINTS_FILE = 'user_points.json'

def load_user_points():
    """
    Load user points and wallet addresses from a JSON file.
    
    Returns:
    - dict: A dictionary mapping usernames to their respective points and wallet addresses.
    """
    if not os.path.exists(POINTS_FILE):
        logging.info(f"{POINTS_FILE} does not exist. Starting with empty data.")
        return {}
    with open(POINTS_FILE, 'r') as f:
        try:
            data = json.load(f)
            # Ensure each user's data has 'points' and 'wallet_address'
            user_points = {}
            for user, info in data.items():
                points = info.get('points', 0)
                wallet_address = info.get('wallet_address', None)
                user_points[str(user)] = {
                    "points": int(points),
                    "wallet_address": wallet_address
                }
            logging.info(f"Loaded user points and wallet addresses from {POINTS_FILE}.")
            return user_points
        except json.JSONDecodeError:
            logging.error("Points file is corrupted. Starting with empty data.")
            return {}

def save_user_points(user_points):
    """
    Save user points and wallet addresses to a JSON file.
    
    Parameters:
    - user_points (dict): A dictionary mapping usernames to their respective points and wallet addresses.
    """
    try:
        with open(POINTS_FILE, 'w') as f:
            json.dump(user_points, f, indent=4)
        logging.info(f"Saved user points and wallet addresses to {POINTS_FILE}.")
    except Exception as e:
        logging.error(f"Error saving user points: {e}")

def set_wallet_address(username, wallet_address):
    """
    Set the wallet address for a user.
    
    Parameters:
    - username (str): The username.
    - wallet_address (str): The wallet address to set.
    """
    if username in user_points:
        user_points[username]['wallet_address'] = wallet_address
        save_user_points(user_points)
        logging.info(f"Set wallet address for user '{username}' to {wallet_address}.")
    else:
        logging.error(f"User '{username}' not found when setting wallet address.")

def get_wallet_address(username):
    """
    Get the wallet address for a user.
    
    Parameters:
    - username (str): The username.
    
    Returns:
    - str or None: The wallet address or None if not set.
    """
    return user_points.get(username, {}).get('wallet_address', None)

# Initialize user_points
user_points = load_user_points()
