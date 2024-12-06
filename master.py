import socket
import pickle
import threading
import queue
import numpy as np
from singleSystem import split_matrices, aggregate_results
from helper import send_data_in_chunks, receive_data_in_chunks

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def worker_handler(conn, addr, task_queue, results, lock):
    """Handle communication with a single worker."""
    worker_ip = addr[0]
    print(f"Worker connected from {worker_ip}")

    try:
        with conn:
            while True:
                # Fetch a task from the queue
                task = task_queue.get() if not task_queue.empty() else None
                if task is None:
                    conn.sendall(pickle.dumps(None))  # Send termination signal
                    print(f"No more tasks. Terminating worker from {worker_ip}.")
                    break

                # Send the task to the worker
                send_data_in_chunks(conn, task)
                print(f"Task sent to worker {worker_ip}")

                # Receive the result from the worker
                result = receive_data_in_chunks(conn)

                # Store the result in the shared results list
                with lock:
                    results.append(result)
                print(f"Result received from worker {worker_ip}")
    except Exception as e:
        print(f"Error with worker {worker_ip}: {e}")
    finally:
        print(f"Worker {worker_ip} handler exiting.")

def distribute_task():
    port = 65432
    master_ip = get_local_ip()
    print(f"Master node is running on IP: {master_ip}, Port: {port}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((master_ip, port))
        s.listen()
        print("Master node is waiting for workers to connect...")

        # Generate matrices and split into tasks
        matrix_size = 1000
        block_size = 100
        matrix_a = np.random.randint(0, 10, size=(matrix_size, matrix_size))
        matrix_b = np.random.randint(0, 10, size=(matrix_size, matrix_size))

        print("Matrix A:")
        print(matrix_a)
        print("Matrix B:")
        print(matrix_b)

        file1 = open("input.txt", "w")
        for i in range(matrix_size):
            for j in range(matrix_size):
                file1.write(str(matrix_a[i][j]))
                file1.write(" ")
            file1.write("\n")
        file1.write("\n")
        for i in range(matrix_size):
            for j in range(matrix_size):
                file1.write(str(matrix_b[i][j]))
                file1.write(" ")
            file1.write("\n")
        file1.close()

        a_blocks, b_blocks = split_matrices(matrix_a, matrix_b, block_size)
        task_queue = queue.Queue()
        for task in zip(a_blocks, b_blocks):
            task_queue.put(task)

        results = []
        lock = threading.Lock()
        threads = []

        try:
            while not task_queue.empty():
                s.settimeout(10.0)  # Add timeout to avoid indefinite blocking
                try:
                    conn, addr = s.accept()
                    worker_thread = threading.Thread(
                        target=worker_handler, args=(conn, addr, task_queue, results, lock)
                    )
                    worker_thread.start()
                    threads.append(worker_thread)
                    print(f"Thread started for worker {addr[0]}")
                except socket.timeout:
                    print("No new connections within timeout. Continuing...")

            # Ensure all threads complete after tasks are exhausted
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
                file2 = open("output.txt", "w")
                for i in range(matrix_size):
                    for j in range(matrix_size):
                        file2.write(str(final_result[i][j]))
                        file2.write(" ")
                    file2.write("\n")
                file2.close()

            else:
                print("No results received from workers.")

if __name__ == "__main__":
    distribute_task()
