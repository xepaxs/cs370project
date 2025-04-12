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
            # Handle received commands based on their type
            if message.get('type') == 'draw':
                # Schedule the drawing on the main Tkinter thread
                canvas.after_idle(draw_command, canvas, message)
            # Add handling for other message types if needed (e.g., clear, user join/leave)
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

# draw command (called when receiving data from server)
def draw_command(canvas, command):
    """Draws a line segment on the canvas based on a received command."""
    try:
        x1 = command['x1']
        y1 = command['y1']
        x2 = command['x2']
        y2 = command['y2']
        color = command['color']
        width = command['width']
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width, capstyle=tk.ROUND, smooth=tk.TRUE)
    except KeyError as e:
        print(f"Received incomplete draw command: missing {e}")
    except Exception as e:
        print(f"Error executing draw command: {e}")

# mouse event handlers
last_x, last_y = None, None

# Need to pass event object
def mouse_down(event):
    global last_x, last_y
    last_x, last_y = (event.x, event.y)

# Need to pass event and canvas
def mouse_drag(event, canvas):
    global last_x, last_y, drawing_color, line_width
    if last_x is not None and last_y is not None:
        # Draw line segment locally
        canvas.create_line(last_x, last_y, event.x, event.y,
                          fill=drawing_color, width=line_width,
                          capstyle=tk.ROUND, smooth=tk.TRUE)

        # Prepare message to send
        draw_message = {
            'type': 'draw',
            'x1': last_x,
            'y1': last_y,
            'x2': event.x,
            'y2': event.y,
            'color': drawing_color,
            'width': line_width
        }
        send_message(draw_message)

        # Update last position
        last_x, last_y = event.x, event.y

def on_mouse_up(event):
    global last_x, last_y
    last_x, last_y = None, None # Reset last position
    
    
# color and width selection
def set_color(new_color):
    global drawing_color
    drawing_color = new_color
    print(f"Color set to: {drawing_color}")

def set_width(new_width):
    global line_width
    line_width = new_width
    print(f"Width set to: {line_width}")


def main():
    root = tk.Tk()
    root.title("Collaborative Drawing Board")

    # --- Control Frame ---
    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Connection Status Label
    status_label = tk.Label(control_frame, text="Disconnected", fg="red")
    status_label.pack(side=tk.LEFT, padx=5)

    # --- Drawing Canvas (define early for button command) ---
    canvas = tk.Canvas(root, bg="white", width=800, height=600)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Now create the connect button using the defined canvas
    connect_button = tk.Button(control_frame, text="Connect", command=lambda: connect_to_server(canvas, status_label))
    connect_button.pack(side=tk.LEFT, padx=5)

    # Color Buttons
    colors = ["black", "red", "green", "blue", "yellow", "orange", "purple", "white"]
    for color in colors:
        btn = tk.Button(control_frame, bg=color, width=2, command=lambda c=color: set_color(c))
        btn.pack(side=tk.LEFT, padx=2)

    # Width Scale
    width_scale = tk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL, label="Width",
                           command=lambda w: set_width(int(w)))
    width_scale.set(line_width) # Set initial value
    width_scale.pack(side=tk.LEFT, padx=5)

    clear_button = tk.Button(control_frame, text="Clear All", command=lambda: send_message({"action": "clear"}))
    clear_button.pack(side=tk.LEFT, padx=5)


    # Bind mouse events - use correct function names
    canvas.bind("<Button-1>", mouse_down)
    canvas.bind("<B1-Motion>", lambda event: mouse_drag(event, canvas)) # Needs lambda for canvas
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    # Handle window closing
    def on_closing():
        close_connection(status_label)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main() 