import tkinter as tk
import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 65432        
sock = None

# Temporary globals for testing only
drawing_color = "black"
line_width = 2

def send_message(message):
    # Sends json message prefixed with its length to the socket.

    global sock 
    if sock:  # Perform if connection exists
        try:
            # Convert the message to a bytestream through utf-8
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')

            # Create a 4-byte prefix containing the message's length
            length_prefix = len(message_bytes).to_bytes(4, 'big')

            # Send the length-prefixed message to the socket
            sock.sendall(length_prefix + message_bytes)

        # If any socket operations fail, print error and close connection
        except socket.error as e:
            print(f"Error sending message: {e}")
            close_connection()

def receive_messages(canvas):
    # Runs the entire time the client is connected.
    # Receives messages from the sock and handles them on the client side.

    global sock
    while sock:   # Run while connection is not closed
        try:
            # Recieve message length prefix
            length_prefix = sock.recv(4)
            if not length_prefix:
                # Prefix not found, client has disconnected
                print("Server disconnected.")
                break

            # Convert the prefix to an integer representing message length
            message_length = int.from_bytes(length_prefix, 'big')

            # Receive the full message in chunks
            message_bytes = b''
            while len(message_bytes) < message_length:  # Loop until we receive the entire message

                # Receive the current chunk from the message
                chunk = sock.recv(message_length - len(message_bytes))
                if not chunk:
                    raise socket.error("Server disconnected during message receive")
                
                # Add the current chunk to the completed message
                message_bytes += chunk

            # Decode the message through utf-8 into a Python dictionary
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)


            ##############################################################################

            # Insert draw command here based on what the message contained
            # Basically, the drawing app will interpret the message as instructions to draw on the canvas.
            # Missing: handle_draw_command(canvas, message)

            ##############################################################################

        except socket.error as e:
            # Generic socket error (bad packet, disconnect, etc.)
            print(f"Socket error receiving: {e}")
            break
        except json.JSONDecodeError:
            # Received data was not in JSON format.
            print("Invalid JSON received from server.")
        except Exception as e:
            # Any other error.
            print(f"Unexpected error receiving message: {e}")
            break 

    # Socket connection has ended, either intentionally or otherwise.
    print("Receive thread exiting.")
    close_connection() 

### Connection functions ###

def connect_to_server(canvas, status_label):
    # Attempt to form a connection to the server.
    # 'canvas' represents the drawing area that will be updated by clients.
    # 'status_label' is used in the GUI.

    global sock
    if sock is None:   # Attempt connection if not already connected.
        try:
            # Create a new TCP socket (IPV4 addressing) using global HOST and PORT
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))

            # Update the GUI and terminal when a connection is successful
            status_label.config(text=f"Connected to {HOST}:{PORT}", fg="green")
            print(f"Successfully connected to {HOST}:{PORT}")

            # Create a daemon thread to run the 'receive_messages' function in the background
            # A daemon thread runs in the background, thus does not obstruct program exit.
            receive_thread = threading.Thread(target=receive_messages, args=(canvas,), daemon=True)
            receive_thread.start()

        except socket.error as e:
            # Update GUI and terminal to reflect a failed connection.
            sock = None
            status_label.config(text=f"Failed to connect: {e}", fg="red")
            print(f"Failed to connect to server: {e}")

    else:
        # The socket exists, we're already connected.
        print("Already connected.")

def close_connection(status_label=None):
    # This function attempts to close the connection.

    global sock
    if sock:   # Only attempt to close a connection if there is one.
        try:
            # Attempt a clean read/write shutdown.
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            # If the socket is already shut down somehow, just move on.
            pass
        finally:
           # Close the socket and print closure message.
           sock.close()
           sock = None
           print("Connection closed.")
           if status_label:
               # Update GUI with 'Disconnected' message.
               status_label.config(text="Disconnected", fg="red")

# draw command

# mouse event handlers
last_x, last_y = None, None

def mouse_down():

def mouse_drag():
    
    
# color and width selection
def set_color():

def set_width():


def main():

if __name__ == "__main__":
    main() 