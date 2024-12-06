import pickle
def send_data_in_chunks(conn, data):
    """Send data in manageable chunks."""
    serialized_data = pickle.dumps(data)
    data_length = len(serialized_data)
    conn.sendall(data_length.to_bytes(8, 'big'))  # Send the size of the data first
    conn.sendall(serialized_data)  # Send the actual data


def receive_data_in_chunks(sock):
    """Receive data in manageable chunks."""
    data_length = int.from_bytes(sock.recv(8), 'big')  # First receive the size
    data = b""
    while len(data) < data_length:
        packet = sock.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)
