# worker.py
import uuid
import socket
import pickle
import numpy as np
from helper import send_data_in_chunks, receive_data_in_chunks
from time import sleep

worker_id = str(uuid.uuid4())  # Unique identifier for this worker

def worker_compute():
    host = '192.168.1.101'  # Master IP (localhost for testing)
    port = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print(f"Worker {worker_id} connected to master.")

            while True:
                task = receive_data_in_chunks(s)
                sleep(5)
                if task is None:
                    print(f"Worker {worker_id} received termination signal. Stopping.")
                    break

                a_block, b_block = task
                result = np.dot(a_block, b_block)
                # Send result along with worker ID
                send_data_in_chunks(s, (worker_id, result))
                print(f"Worker {worker_id} sent result to master. Ready for the next task.")
    except Exception as e:
        print(f"Error occurred in worker {worker_id}: {e}")

if __name__ == "__main__":
    worker_compute()
