import socket
import threading
import json # For sending structured data

# Board history, used to mass dump onto new users on the board
board_history = []
history_lock = threading.Lock()

HOST = '0.0.0.0'  # Listen on all network interfaces
PORT = 65432       
clients = []

# Threading lock for safe thread access.
# Prevents race conditions if multiple clients try to read/write simultaneously.
clients_lock = threading.Lock()

def broadcast(message, sender_conn):
    # Broadcasts a message from a client to all other clients
    # If sender_conn is None, send to all clients including sender

    # Append the draw command to the board history
    if message.get("type") == "draw":
        with history_lock:
            board_history.append(message)
    elif message.get("type") == "clear":
        with history_lock:
            board_history.clear()

    # Send the message out to every client
    disconnected_clients = []
    with clients_lock:  
        for client_conn in clients:
            if sender_conn is None or client_conn != sender_conn:
                try:
                    message_json = json.dumps(message)
                    message_bytes = message_json.encode('utf-8')
                    length_prefix = len(message_bytes).to_bytes(4, 'big')
                    client_conn.sendall(length_prefix + message_bytes)
                except socket.error as e:
                    print(f"Failed to send to client {client_conn.getpeername()}: {e}")
                    disconnected_clients.append(client_conn)

        # Remove disconnected clients
        for client in disconnected_clients:
            if client in clients:
                clients.remove(client)
                try:
                    client.close()
                except:
                    pass
                print(f"Removed disconnected client {client.getpeername()}")

def handle_client(conn, addr):
    # Handles connection from a single client.
    # Runs the entire time the client is connected.
    # Adds them to the client list, then listens for messages from them.
    # 'conn' contains the client's socket information.
    # 'addr' contains something.

    print(f"New client connected from {addr}")
    with clients_lock:
        clients.append(conn)  # Add this client to the list of active clients
    
    # Send welcome message to all clients
    welcome_msg = {
        "type": "system",
        "message": f"New user joined from {addr[0]}"
    }
    broadcast(welcome_msg, None)  # None means send to all including sender

    # Sending the new client the board history.
    with history_lock:
        for message in board_history:
            try:
                message_json = json.dumps(message)
                message_bytes = message_json.encode('utf-8')
                length_prefix = len(message_bytes).to_bytes(4, 'big')
                conn.sendall(length_prefix + message_bytes)
            except socket.error:
                print(f"Failed to send history to {addr}")
                break

    # Now we listen for incoming messages from the new user.
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
    try:
        # Create a new TCP socket (IPV4 addressing) using global HOST and PORT
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Configure the socket to allow address reuse and bind it global HOST and PORT.
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            
            # Start listening for incoming connections.
            s.listen(5)  # Allow up to 5 pending connections
            print(f"Server listening on {HOST}:{PORT}")
            print("Ready for multiple clients to connect!")

            while True:
                try:
                    # Accept incoming clients in the current address.
                    conn, addr = s.accept()
                    print(f"Accepted connection from {addr}")

                    # Start a new daemon thread for each client
                    thread = threading.Thread(target=handle_client, args=(conn, addr))
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    print(f"Error accepting client connection: {e}")
                    continue
    except Exception as e:
        print(f"Server error: {e}")
        print("Server shutting down...")
    finally:
        # Clean up all client connections
        with clients_lock:
            for client in clients:
                try:
                    client.close()
                except:
                    pass
            clients.clear()

if __name__ == "__main__":
    start_server() 