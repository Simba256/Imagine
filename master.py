import socket
import pickle
import threading
import queue
import numpy as np
import os
from singleSystem import split_matrices, aggregate_results
from helper import send_data_in_chunks, receive_data_in_chunks
from check import check, check_result
from user_points import load_user_points, save_user_points











matrix_size = 40
block_size = 4
global num_workers
num_workers = 0

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

# Inside master.py
user_points = {}  # To track points for each worker ID

def worker_handler(conn, addr, task_queue, results, lock):
    worker_ip = addr[0]
    worker_port = addr[1]
    print(f"Worker connected from {worker_ip}:{worker_port}")

    try:
        with conn:
            while True:
                task = task_queue.get() if not task_queue.empty() else None
                if task is None:
                    send_data_in_chunks(conn, None)  # Send termination signal
                    print(f"No more tasks. Terminating worker {worker_ip}:{worker_port}.")
                    break

                send_data_in_chunks(conn, task)
                print(f"Task sent to worker {worker_ip}:{worker_port}")

                # Receive result from worker
                try:
                    worker_id, result = receive_data_in_chunks(conn)
                except Exception as e:
                    print(f"Failed to receive result from worker {worker_ip}:{worker_port}: {e}")
                    task_queue.put(task)  # Requeue task
                    break

                if worker_id not in user_points:
                    user_points[worker_id] = 0  # Initialize points for new worker

                if check(np.array(task[0]), np.array(task[1]), np.array(result),
                         block_size, block_size, block_size, matrix_size, matrix_size, block_size) == 1:
                    with lock:
                        results.append(result)
                        user_points[worker_id] += 1
                    print(f"Result accepted from Worker {worker_id}. Points: {user_points[worker_id]}")
                else:
                    task_queue.put(task)  # Requeue task
                    print(f"Incorrect result from Worker {worker_id}. Task requeued.")
    except Exception as e:
        print(f"Error with worker {worker_ip}:{worker_port}: {e}")
    finally:
        print(f"Worker handler for {worker_ip}:{worker_port} exiting.")


# Fix the distribute_task function to manage multiple worker connections

def distribute_task():
    port = int(os.environ.get("PORT", 65432))  # Default to 65432 for local testing
    master_ip = "0.0.0.0"  # Bind to all available interfaces for public access

    print(f"Master node is running on IP: {master_ip}, Port: {port}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((master_ip, port))
        s.listen()
        print("Master node is waiting for workers to connect...")

        # Task setup
        matrix_a = np.random.randint(0, 10, size=(matrix_size, matrix_size))
        matrix_b = np.random.randint(0, 10, size=(matrix_size, matrix_size))
        print("Matrix A:")
        print(matrix_a)
        print("Matrix B:")
        print(matrix_b)

        a_blocks, b_blocks = split_matrices(matrix_a, matrix_b, block_size)
        task_queue = queue.Queue()
        for task in zip(a_blocks, b_blocks):
            task_queue.put(task)

        results = []
        lock = threading.Lock()
        threads = []
        global num_workers  # Ensure `num_workers` is global
        num_workers = 0

        try:
            while not task_queue.empty():
                s.settimeout(10.0)  # Timeout to accept new connections
                try:
                    conn, addr = s.accept()
                    print(f"Worker connected from {addr}")
                    worker_thread = threading.Thread(
                        target=worker_handler, args=(conn, addr, task_queue, results, lock)
                    )
                    worker_thread.start()
                    threads.append(worker_thread)
                    with lock:
                        num_workers += 1
                        print(f"Thread started for worker {addr}, Total workers: {num_workers}")
                except socket.timeout:
                    # No new connections within timeout, continue to next iteration
                    pass

            # Ensure all threads complete
            print("All tasks distributed. Waiting for worker threads to complete...")
            for thread in threads:
                thread.join()
                print(f"Thread {thread.name} has completed.")
        except Exception as e:
            print(f"Error in master node: {e}")
        finally:
            # Aggregate results
            if results:
                final_result = aggregate_results(results, matrix_a.shape, matrix_b.shape, block_size)
                print("Final aggregated matrix multiplication result:")
                print(final_result)
            else:
                print("No results received from workers.")

if __name__ == "__main__":
    try:
        user_points = load_user_points()
        distribute_task()
    finally:
        save_user_points(user_points)
        print("User points saved. Final points distribution:")
        print(user_points)
