import socket
import threading
import json # For sending structured data

HOST = '127.0.0.1' 
PORT = 65432       
clients = []

# Threading lock for safe thread access.
# Prevents race conditions if multiple clients try to read/write simultaneously.
clients_lock = threading.Lock()

def broadcast(message, sender_conn):
    # Broadcasts a message from a client to all other clients
    # 'message' contains the message that will be broadcasted.
    # 'sender_conn' the socket object of the sender, so they won't be sent their own actions.

    with clients_lock:  
        for client_conn in clients:  # Loop through all active clients
            if client_conn != sender_conn:
                try:
                    # Prepare message for sending by converting to JSON
                    # Then use utf-8 encoding to convert it to a byte stream
                    message_json = json.dumps(message)
                    message_bytes = message_json.encode('utf-8')

                    # Create a 4-byte prefix containing the message's length
                    length_prefix = len(message_bytes).to_bytes(4, 'big')

                    # Send the length-prefixed message to the client
                    client_conn.sendall(length_prefix + message_bytes)

                except socket.error:
                    # If an error occured, assume the client disconnected.
                    clients.remove(client_conn)
                    print(f"Client {client_conn.getpeername()} disconnected.")


def handle_client(conn, addr):
    # Handles connection from a single client.
    # Runs the entire time the client is connected.
    # Adds them to the client list, then listens for messages from them.
    # 'conn' contains the client's socket information.
    # 'addr' contains something.

    print(f"Connected by {addr}")
    with clients_lock:
        clients.append(conn)  # Add this client to the list of active clients

    try:
        while True:
            
            # Read 4 byte prefix containing message length.
            length_prefix = conn.recv(4)
            if not length_prefix:
                break  # Prefix not found, client disconnected
            
            # Convert the prefix to an integer
            message_length = int.from_bytes(length_prefix, 'big')
            
            # Read the message through chunks
            message_bytes = b''
            while len(message_bytes) < message_length:  # Loop until we receive the entire message

                # Receive the current chunk from the message
                chunk = conn.recv(message_length - len(message_bytes))
                if not chunk:
                    raise socket.error("Client disconnected during message receive")
                
                # Add the current chunk to the completed message
                message_bytes += chunk
                
            # Decode the message through utf-8 into a Python dictionary
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)

            # Broadcast the message to all other clients.
            print(f"Received from {addr}: {message}")
            broadcast(message, conn)

    except socket.error as e:
        # Generic socket error (bad packet, disconnect, etc.)
        print(f"Socket error with {addr}: {e}")
    except json.JSONDecodeError:
        # Received data was not in JSON format.
        print(f"Invalid JSON received from {addr}")

    finally:
        # Connection closed. Remove client from list and close out.
        print(f"Connection closed by {addr}")
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()

def start_server():
    # This function creates the server.

    # Create a new TCP socket (IPV4 addressing) using global HOST and PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        
        # Configure the socket to allow address reuse and bind it global HOST and PORT.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        
        # Start listening for incoming connections.
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            # Accept incoming clients in the current address.
            conn, addr = s.accept()

            # Start a new daemon thread for each client
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_server() 