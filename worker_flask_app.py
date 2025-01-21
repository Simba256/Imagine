# worker_flask_app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import socket
import threading
import pickle
import json
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from time import sleep
import struct
import numpy as np 


# Global variables
active_connections = {}  # { username: socket_object }

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("worker_flask_app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = 'another_secure_secret_key'  # Replace with a secure secret key

# Data Server URL
DATA_SERVER_URL = 'http://192.168.1.4:5001'  # Ensure this is correct

# Worker Node's Master Server Details
MASTER_SERVER_IP = '192.168.1.4'  # Replace with actual master server IP
MASTER_SERVER_PORT = 65432

# Thread-safe storage for user points
points_lock = threading.Lock()
points_map = {}

def connect_to_master(username):
    global active_connections
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((MASTER_SERVER_IP, MASTER_SERVER_PORT))
        
        # Store the connection reference so we can close it later if needed
        active_connections[username] = sock

        logging.info(f"Connected to master server at {MASTER_SERVER_IP}:{MASTER_SERVER_PORT}")

        # Send username to master
        send_data_in_chunks(sock, [username])
        logging.debug(f"Sent username '{username}' to master server.")

        while True:
            task = receive_data_in_chunks(sock)
            if task is None:
                logging.info("No more tasks received. Closing connection.")
                break

            a_block, b_block = task
            logging.debug(f"Received task: a_block={a_block}, b_block={b_block}")

            # Perform computation
            result = perform_computation(a_block, b_block)
            logging.debug(f"Computed result: {result}")

            # Send result back to master
            send_data_in_chunks(sock, [username, result])
            logging.debug(f"Sent result back to master for user '{username}'.")

            # Receive updated points
            updated_points = receive_data_in_chunks(sock)
            if updated_points is None:
                logging.warning("No points received from master.")
                continue

            # Update points_map in a thread-safe manner
            with points_lock:
                points_map[username] = updated_points
                logging.info(f"Updated points for user '{username}': {updated_points}")

    except Exception as e:
        logging.error(f"Error connecting to master server: {e}")
    finally:
        # Always clean up the socket
        try:
            sock.close()
            logging.info("Socket connection closed.")
        except:
            pass

        # Remove from active_connections if still present
        if username in active_connections:
            del active_connections[username]

def perform_computation(a_block, b_block):
    """
    Performs matrix multiplication on the received blocks.

    Parameters:
    - a_block (list): Sub-matrix from matrix A.
    - b_block (list): Sub-matrix from matrix B.

    Returns:
    - list: Resulting sub-matrix after multiplication.
    """
    try:
        a_np = np.array(a_block)
        b_np = np.array(b_block)
        result_np = np.dot(a_np, b_np)
        return result_np.tolist()
    except Exception as e:
        logging.error(f"Error during computation: {e}")
        return []

def send_data_in_chunks(conn, data):
    """
    Serialize and send data with a fixed-length header indicating the data size.
    """
    try:
        serialized_data = pickle.dumps(data)
        data_length = len(serialized_data)
        header = struct.pack('!I', data_length)  # 4-byte unsigned int, network byte order
        conn.sendall(header + serialized_data)
        logging.debug(f"Sent data of length {data_length} bytes.")
    except Exception as e:
        logging.error(f"Error sending data: {e}")
        raise

def receive_data_in_chunks(conn):
    """
    Receive data sent with a fixed-length header indicating the data size.
    """
    try:
        # First, receive the header
        header = recvall(conn, 4)
        if not header:
            logging.warning("No header received.")
            return None
        data_length = struct.unpack('!I', header)[0]
        logging.debug(f"Expecting to receive {data_length} bytes of data.")

        # Then, receive the actual data
        serialized_data = recvall(conn, data_length)
        if not serialized_data:
            logging.warning("No serialized data received.")
            return None
        data = pickle.loads(serialized_data)
        logging.debug(f"Received data: {data}")
        return data
    except Exception as e:
        logging.error(f"Error receiving data: {e}")
        return None

def recvall(conn, n):
    """
    Helper function to receive exactly n bytes or return None if EOF is hit.
    """
    data = b''
    try:
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                logging.warning("Connection closed by the other side.")
                return None
            data += packet
        return data
    except Exception as e:
        logging.error(f"Error in recvall: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Handle user login and registration on the same page.
    """
    if request.method == "POST":
        if 'register' in request.form:
            # Handle registration
            username = request.form.get("username")
            password = request.form.get("password")
            if not username or not password:
                flash("Username and password are required for registration.", "danger")
                return redirect(url_for('index'))
            # Send registration request to data server
            try:
                response = requests.post(f"{DATA_SERVER_URL}/register", json={
                    'username': username,
                    'password': password
                })
                if response.status_code == 201:
                    flash("Registration successful! Please log in.", "success")
                    logging.info(f"User '{username}' registered successfully.")
                else:
                    flash(response.json().get('message', 'Registration failed.'), "danger")
                    logging.warning(f"Registration failed for user '{username}': {response.json().get('message')}")
            except Exception as e:
                flash("Error connecting to data server.", "danger")
                logging.error(f"Error connecting to data server during registration: {e}")
            return redirect(url_for('index'))
        elif 'login' in request.form:
            # Handle login
            username = request.form.get("username")
            password = request.form.get("password")
            if not username or not password:
                flash("Username and password are required for login.", "danger")
                return redirect(url_for('index'))
            # Send login request to data server
            try:
                response = requests.post(f"{DATA_SERVER_URL}/login", json={
                    'username': username,
                    'password': password
                })
                if response.status_code == 200:
                    session['username'] = username
                    session['points'] = response.json().get('points', 0)
                    session['wallet_address'] = response.json().get('wallet_address', None)
                    flash("Logged in successfully!", "success")
                    logging.info(f"User '{username}' logged in successfully.")
                    return redirect(url_for('dashboard'))
                else:
                    flash(response.json().get('message', 'Login failed.'), "danger")
                    logging.warning(f"Login failed for user '{username}': {response.json().get('message')}")
            except Exception as e:
                flash("Error connecting to data server.", "danger")
                logging.error(f"Error connecting to data server during login: {e}")
            return redirect(url_for('index'))
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    """
    Display user dashboard with points and connect button.
    """
    if 'username' not in session:
        flash("Please log in to access the dashboard.", "danger")
        return redirect(url_for('index'))
    username = session['username']

    # Fetch latest points and wallet_address from data server
    try:
        response = requests.get(f"{DATA_SERVER_URL}/get_points", params={'username': username}, timeout=5)
        if response.status_code == 200:
            user_info = response.json()
            points = user_info.get('points', 0)
            wallet_address = user_info.get('wallet_address', None)
            # Update session
            session['points'] = points
            session['wallet_address'] = wallet_address
        else:
            flash("Failed to retrieve user info.", "danger")
            points = session.get('points', 0)
            wallet_address = session.get('wallet_address', None)
    except Exception as e:
        flash("Error connecting to data server.", "danger")
        logging.error(f"Error fetching user info for '{username}': {e}")
        points = session.get('points', 0)
        wallet_address = session.get('wallet_address', None)

    return render_template("dashboard.html", username=username, points=points, wallet_address=wallet_address)

@app.route("/connect", methods=["POST"])
def connect_network_route():
    if 'username' not in session:
        flash("Please log in to connect to the network.", "danger")
        return redirect(url_for('index'))

    username = session['username']
    flash("Connecting to the network...", "info")
    
    # Start a new thread to handle socket connection
    thread = threading.Thread(target=connect_to_master, args=(username,), daemon=True)
    thread.start()

    # Mark user as connected
    session['connected'] = True

    flash("Connected to the network and started receiving tasks.", "success")
    return redirect(url_for('dashboard'))


@app.route("/disconnect", methods=["POST"])
def disconnect_network_route():
    if 'username' not in session:
        flash("Please log in to disconnect from the network.", "danger")
        return redirect(url_for('index'))

    username = session['username']
    
    # Attempt to close the user's socket if it exists
    if username in active_connections:
        try:
            active_connections[username].close()
            del active_connections[username]
            flash("Disconnected from the network.", "success")
        except Exception as e:
            logging.error(f"Error disconnecting user '{username}': {e}")
            flash("Failed to disconnect properly.", "danger")
    else:
        flash("No active connection found for this user.", "warning")

    # Mark user as no longer "connected" in session
    session['connected'] = False
    return redirect(url_for('dashboard'))


@app.route("/connect_wallet", methods=["POST"])
def connect_wallet():
    """
    Receive the wallet address from the client and set it in the data server.
    Expects JSON payload with 'wallet_address'.
    """
    if 'username' not in session:
        return jsonify({'message': 'Not authenticated.'}), 401

    data = request.get_json()
    if not data or not data.get('wallet_address'):
        return jsonify({'message': 'wallet_address is required.'}), 400

    wallet_address = data['wallet_address']
    username = session['username']

    # Validate wallet_address format (basic validation)
    if not isinstance(wallet_address, str) or not wallet_address.startswith('0x') or len(wallet_address) != 42:
        return jsonify({'message': 'Invalid wallet address format.'}), 400

    # Optionally, verify the wallet address using web3.py and Sepolia endpoint

    # For now, just send to data_server.py via '/set_wallet'
    try:
        response = requests.post(f"{DATA_SERVER_URL}/set_wallet", json={
            'username': username,
            'wallet_address': wallet_address
        }, timeout=5)
        if response.status_code == 200:
            # Update session with new wallet address
            session['wallet_address'] = wallet_address
            flash("Wallet connected successfully!", "success")
            logging.info(f"User '{username}' connected wallet: {wallet_address}")
            return jsonify({'message': 'Wallet connected successfully.'}), 200
        else:
            return jsonify({'message': response.json().get('message', 'Failed to set wallet address.')}), response.status_code
    except Exception as e:
        logging.error(f"Error connecting wallet for user '{username}': {e}")
        return jsonify({'message': 'Error connecting wallet.'}), 500

@app.route("/logout")
def logout():
    """Log the user out."""
    session.pop('username', None)
    session.pop('points', None)
    session.pop('wallet_address', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Run the Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
