import socket
import pickle
import numpy as np
from helper import send_data_in_chunks, receive_data_in_chunks


def worker_compute():
    host = '10.1.153.119'  # Replace with master IP
    port = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print("Connected to master.")

            while True:
                task = receive_data_in_chunks(s)
                if task is None:
                    print("Termination signal received. Stopping worker.")
                    break

                a_block, b_block = task
                result = np.dot(a_block, b_block)
                send_data_in_chunks(s, result)
                print("Result sent to master. Ready for the next task.")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    worker_compute()
