import socket
import threading
import json # For sending structured data

HOST = '127.0.0.1' 
PORT = 65432       
clients = []
clients_lock = threading.Lock()

def broadcast(message, sender_conn):
    """Sends a message to all clients except the sender."""
    with clients_lock:
        for client_conn in clients:
            if client_conn != sender_conn:
                try:
                    # Prefix message 
                    message_json = json.dumps(message)
                    message_bytes = message_json.encode('utf-8')
                    length_prefix = len(message_bytes).to_bytes(4, 'big')
                    client_conn.sendall(length_prefix + message_bytes)
                except socket.error:
                    # Assume client disconnected
                    clients.remove(client_conn)
                    print(f"Client {client_conn.getpeername()} disconnected.")


def handle_client(conn, addr):
    """Handles connection for a single client."""
    print(f"Connected by {addr}")
    with clients_lock:
        clients.append(conn)

    try:
        while True:
            # read message length prefix
            length_prefix = conn.recv(4)
            if not length_prefix:
                break 
            
            message_length = int.from_bytes(length_prefix, 'big')
            
            # read message
            message_bytes = b''
            while len(message_bytes) < message_length:
                chunk = conn.recv(message_length - len(message_bytes))
                if not chunk:
                    raise socket.error("Client disconnected during message receive")
                message_bytes += chunk
                
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)
            
            print(f"Received from {addr}: {message}")
            # broadcast the drawing action 
            broadcast(message, conn)

    except socket.error as e:
        print(f"Socket error with {addr}: {e}")
    except json.JSONDecodeError:
        print(f"Invalid JSON received from {addr}")
    finally:
        print(f"Connection closed by {addr}")
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            # Start a new thread for each client
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_server() 