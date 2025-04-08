import tkinter as tk
import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 65432        
sock = None
drawing_color = "black"
line_width = 2

def send_message(message):
    # sends json message prefixed with its length
    global sock
    if sock:
        try:
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            length_prefix = len(message_bytes).to_bytes(4, 'big')
            sock.sendall(length_prefix + message_bytes)
        except socket.error as e:
            print(f"Error sending message: {e}")
            close_connection()

def receive_messages(canvas):
    global sock
    while sock:
        try:
            length_prefix = sock.recv(4)
            if not length_prefix:
                print("Server disconnected.")
                break

            message_length = int.from_bytes(length_prefix, 'big')

            message_bytes = b''
            while len(message_bytes) < message_length:
                chunk = sock.recv(message_length - len(message_bytes))
                if not chunk:
                    raise socket.error("Server disconnected during message receive")
                message_bytes += chunk

            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)

            # draw command here
            # Missing: handle_draw_command(canvas, message)

        except socket.error as e:
            print(f"Socket error receiving: {e}")
            break
        except json.JSONDecodeError:
            print("Invalid JSON received from server.")
        except Exception as e:
            print(f"Unexpected error receiving message: {e}")
            break 

    print("Receive thread exiting.")
    close_connection() 

# connections
def connect_to_server(canvas, status_label):
    global sock
    if sock is None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            status_label.config(text=f"Connected to {HOST}:{PORT}", fg="green")
            print(f"Successfully connected to {HOST}:{PORT}")

            receive_thread = threading.Thread(target=receive_messages, args=(canvas,), daemon=True)
            receive_thread.start()
        except socket.error as e:
            sock = None
            status_label.config(text=f"Failed to connect: {e}", fg="red")
            print(f"Failed to connect to server: {e}")
    else:
        print("Already connected.")


def close_connection(status_label=None):
    global sock
    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR) 
        except OSError:
            pass
        finally:
           sock.close()
           sock = None
           print("Connection closed.")
           if status_label:
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