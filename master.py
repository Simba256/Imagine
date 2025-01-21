# master.py
import socket
import pickle
import threading
import queue
import numpy as np
import logging
import requests  # For HTTP communication
from singleSystem import split_matrices, aggregate_results
from helper import send_data_in_chunks, receive_data_in_chunks
from check import check
from itertools import product  # For generating task combinations

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(threadName)s: %(message)s',
    handlers=[
        logging.FileHandler("master.log"),
        logging.StreamHandler()
    ]
)

# Master Node Configuration
MASTER_IP = "0.0.0.0"  # Bind to all interfaces
MASTER_PORT = 65432
DATA_SERVER_IP = "192.168.1.4"  # Data Server IP
DATA_SERVER_PORT = 5001
DATA_SERVER_URL = f"http://{DATA_SERVER_IP}:{DATA_SERVER_PORT}"

matrix_size = 4000  # Size of the matrices (400x400)
block_size = 4     # Size of each block (4x4)

# Retry Configuration
MAX_RETRIES = 3  # Maximum number of retries per task

def get_local_ip():
    """
    Retrieves the local IP address of the master node.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Doesn't need to be reachable
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

# Global Task Queue
task_queue = queue.Queue()

# Assigned Tasks Tracking
assigned_tasks = {}
task_lock = threading.Lock()

def worker_handler(conn, addr):
    """
    Handles communication with a connected worker.
    """
    worker_ip, worker_port = addr
    thread_name = threading.current_thread().name
    logging.info(f"Worker connected from {worker_ip}:{worker_port}")

    try:
        with conn:
            # Receive username upon connection
            try:
                data = receive_data_in_chunks(conn)
                if not data or len(data) != 1:
                    raise ValueError("Expected username upon connection.")
                username = data[0]
                logging.info(f"Worker for user '{username}' connected from {worker_ip}:{worker_port}")
            except Exception as e:
                logging.error(f"Failed to receive username from {worker_ip}:{worker_port}: {e}")
                return

            # Validate user via Data Server
            try:
                response = requests.get(f"{DATA_SERVER_URL}/get_points", params={'username': username}, timeout=5)
                logging.debug(f"Data Server response for '/get_points': Status {response.status_code}, Body {response.text}")
                if response.status_code != 200:
                    raise ValueError(f"User '{username}' not recognized.")
                points = response.json().get('points', 0)
                logging.info(f"User '{username}' is valid with {points} points.")
            except Exception as e:
                logging.error(f"Validation failed for user '{username}': {e}")
                send_data_in_chunks(conn, None)  # Send termination signal
                return

            while True:
                try:
                    # Fetch a task from the global queue
                    task = task_queue.get_nowait()
                    a_block, b_block, retry_count = task
                    logging.debug(f"Assigning task to user '{username}': Retry Count: {retry_count}")

                    # Record the assignment
                    with task_lock:
                        assigned_tasks[thread_name] = task

                    # Send task to worker
                    send_data_in_chunks(conn, (a_block, b_block))
                    logging.debug(f"Sent task to worker '{username}': {task}")

                    # Receive result from worker
                    data = receive_data_in_chunks(conn)
                    if not data or len(data) != 2:
                        raise ValueError("Expected tuple of (username, result).")

                    received_username, result = data
                    if received_username != username:
                        raise ValueError(f"Username mismatch: {received_username} != {username}")

                    logging.debug(f"Received result from user '{username}': {result}")

                    # Validate the result
                    try:
                        is_valid = check(np.array(a_block), np.array(b_block), np.array(result))
                    except Exception as e:
                        logging.error(f"Validation error for user '{username}': {e}")
                        is_valid = 0

                    if is_valid == 1:
                        # Increment user's points via Data Server
                        try:
                            new_points = points + 1
                            update_response = requests.post(f"{DATA_SERVER_URL}/update_points", json={
                                'username': username,
                                'points': new_points
                            }, timeout=5)
                            logging.debug(f"Data Server response for '/update_points': Status {update_response.status_code}, Body {update_response.text}")
                            if update_response.status_code != 200:
                                raise ValueError("Failed to update points.")
                            points = new_points
                            logging.info(f"Valid result from user '{username}'. Points updated to {points}.")
                            # Send updated points to worker
                            send_data_in_chunks(conn, points)
                            logging.debug(f"Sent updated points ({points}) to user '{username}'.")
                        except Exception as e:
                            logging.error(f"Failed to update/send points for user '{username}': {e}")
                            # Requeue the task for reassignment
                            task_queue.put((a_block, b_block, retry_count))
                            continue  # Proceed to the next iteration
                    else:
                        # Requeue the task due to invalid result
                        if retry_count < MAX_RETRIES:
                            new_retry_count = retry_count + 1
                            task_queue.put((a_block, b_block, new_retry_count))
                            logging.warning(f"Invalid result from user '{username}'. Task requeued with retry count {new_retry_count}.")
                        else:
                            logging.error(f"Task failed after {MAX_RETRIES} retries. Discarding task: {task}")
                    
                    # Remove the task from assigned_tasks
                    with task_lock:
                        del assigned_tasks[thread_name]

                except queue.Empty:
                    # No more tasks available
                    send_data_in_chunks(conn, None)  # Send termination signal
                    logging.info(f"No more tasks available. Terminating worker '{username}'.")
                    break
                except Exception as e:
                    logging.error(f"Error during task assignment or result processing for user '{username}': {e}")
                    # If a task was assigned but not processed, requeue it
                    with task_lock:
                        if thread_name in assigned_tasks:
                            task = assigned_tasks[thread_name]
                            task_queue.put(task)
                            del assigned_tasks[thread_name]
                    break

    except Exception as e:
        logging.error(f"Error handling worker {thread_name}: {e}")

def distribute_tasks():
    """
    Initializes the master node, sets up the server to accept worker connections,
    and manages task distribution.
    """
    master_ip = MASTER_IP
    master_port = MASTER_PORT

    logging.info(f"Master node is running on IP: {get_local_ip()}, Port: {master_port}")

    # Generate matrices and split into blocks once
    matrix_a = np.random.randint(0, 10, size=(matrix_size, matrix_size))
    matrix_b = np.random.randint(0, 10, size=(matrix_size, matrix_size))
    try:
        a_blocks, b_blocks = split_matrices(matrix_a, matrix_b, block_size)
        logging.info(f"Split matrices into {len(a_blocks)} row blocks and {len(b_blocks)} column blocks.")
    except Exception as e:
        logging.error(f"Error splitting matrices: {e}")
        return

    # Enqueue n^2 tasks
    total_tasks = 0
    for a_block, b_block in product(a_blocks, b_blocks):
        task_queue.put((a_block, b_block, 0))  # Initial retry_count=0
        total_tasks += 1
    logging.info(f"Enqueued a total of {total_tasks} tasks into the global task queue.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((master_ip, master_port))
        s.listen()
        logging.info("Master node is waiting for workers to connect...")

        while True:
            try:
                conn, addr = s.accept()
                logging.info(f"Accepted connection from {addr}")
                worker_thread = threading.Thread(
                    target=worker_handler, args=(conn, addr),
                    name=f"WorkerHandler-{addr}"
                )
                worker_thread.start()
            except Exception as e:
                logging.error(f"Error accepting connections: {e}")

if __name__ == "__main__":
    distribute_tasks()
