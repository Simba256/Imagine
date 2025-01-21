# helper.py
import pickle
import struct
import logging

def send_data_in_chunks(conn, data):
    """
    Serialize and send data with a fixed-length header indicating the data size.
    
    Parameters:
    - conn (socket.socket): The socket connection to send data through.
    - data (any): The data to serialize and send.
    
    Raises:
    - Exception: Propagates any exceptions encountered during sending.
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
    
    Parameters:
    - conn (socket.socket): The socket connection to receive data from.
    
    Returns:
    - any: The deserialized data received.
    - None: If no data is received.
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
    
    Parameters:
    - conn (socket.socket): The socket connection to receive data from.
    - n (int): The exact number of bytes to receive.
    
    Returns:
    - bytes: The received bytes.
    - None: If the connection is closed before receiving n bytes.
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
