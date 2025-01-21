# data_server.py
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import json
import os
import logging
from user_points import load_user_points, save_user_points, set_wallet_address, get_wallet_address

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("data_server.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes

# User Data File
USER_DATA_FILE = 'users.json'

# Load or initialize user data
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

# Load user points
user_points = load_user_points()  # Maps usernames to points and wallet addresses

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    Expects JSON payload with 'username' and 'password'.
    """
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    if username in users:
        return jsonify({'message': 'Username already exists.'}), 400

    hashed_password = generate_password_hash(password)
    users[username] = hashed_password
    save_users()

    user_points[username] = {"points": 0, "wallet_address": None}  # Initialize points and wallet
    save_user_points(user_points)

    logging.info(f"User registered: {username}")
    return jsonify({'message': 'Registration successful.'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Login an existing user.
    Expects JSON payload with 'username' and 'password'.
    """
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    if username not in users or not check_password_hash(users[username], password):
        return jsonify({'message': 'Invalid username or password.'}), 401

    points = user_points.get(username, {}).get('points', 0)
    wallet_address = user_points.get(username, {}).get('wallet_address', None)
    logging.info(f"User logged in: {username}")
    return jsonify({'message': 'Login successful.', 'points': points, 'wallet_address': wallet_address}), 200

@app.route('/get_points', methods=['GET'])
def get_points():
    """
    Retrieve points and wallet address for a given user.
    Expects 'username' as a query parameter.
    """
    username = request.args.get('username')
    if not username:
        return jsonify({'message': 'Username is required.'}), 400

    if username not in user_points:
        return jsonify({'message': 'User does not exist.'}), 400

    user_info = user_points.get(username, {})
    points = user_info.get('points', 0)
    wallet_address = user_info.get('wallet_address', None)
    return jsonify({'username': username, 'points': points, 'wallet_address': wallet_address}), 200

@app.route('/update_points', methods=['POST'])
def update_points():
    """
    Update points for a given user.
    Expects JSON payload with 'username' and 'points'.
    """
    data = request.get_json()
    if not data or not data.get('username') or 'points' not in data:
        return jsonify({'message': 'Username and points are required.'}), 400

    username = data['username']
    points = data['points']

    if username not in users:
        return jsonify({'message': 'User does not exist.'}), 400

    user_points[username]['points'] = points
    save_user_points(user_points)

    logging.info(f"Points updated for user '{username}': {points}")
    return jsonify({'message': 'Points updated successfully.'}), 200

@app.route('/set_wallet', methods=['POST'])
def set_wallet():
    """
    Set the wallet address for a given user.
    Expects JSON payload with 'username' and 'wallet_address'.
    """
    data = request.get_json()
    if not data or not data.get('username') or not data.get('wallet_address'):
        return jsonify({'message': 'Username and wallet_address are required.'}), 400

    username = data['username']
    wallet_address = data['wallet_address']

    # Validate wallet_address format (basic validation)
    if not isinstance(wallet_address, str) or not wallet_address.startswith('0x') or len(wallet_address) != 42:
        return jsonify({'message': 'Invalid wallet address format.'}), 400

    if username not in user_points:
        return jsonify({'message': 'User does not exist.'}), 400

    user_points[username]['wallet_address'] = wallet_address
    save_user_points(user_points)

    logging.info(f"Wallet address set for user '{username}': {wallet_address}")
    return jsonify({'message': 'Wallet address updated successfully.'}), 200

def save_users():
    """Save user data to the JSON file."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)
    logging.info("User data saved.")

if __name__ == '__main__':
    # Run the Flask app on port 5001 to differentiate from master.py
    app.run(host='0.0.0.0', port=5001, debug=False)
