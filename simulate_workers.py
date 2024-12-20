# simulate_workers.py
import threading
import subprocess

def start_worker():
    subprocess.run(["python", "worker.py"])

if __name__ == "__main__":
    num_workers = 4  # Number of worker nodes to simulate
    threads = []

    for _ in range(num_workers):
        thread = threading.Thread(target=start_worker)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
