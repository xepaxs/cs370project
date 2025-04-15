import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import json
import sys

# Default to localhost, but allow command line override
HOST = '127.0.0.1'  # Default host
PORT = 65432        
sock = None

if len(sys.argv) > 1:
    HOST = sys.argv[1]  # Allow IP address to be passed as command line argument

# Temporary globals for testing only
drawing_color = "black"
line_width = 2

def send_message(message):
    # Sends json message prefixed with its length to the socket.
    global sock 
    if sock:  # Perform if connection exists
        try:
            # Convert message to json
            message_json = json.dumps(message)  
            # Encode message to bytes
            message_bytes = message_json.encode('utf-8')
            # Prefix message with its length
            length_prefix = len(message_bytes).to_bytes(4, 'big')
            # Send message to server
            sock.sendall(length_prefix + message_bytes)
        except socket.error as e:
            print(f"Error sending message: {e}")
            close_connection()
            messagebox.showerror("Connection Error", "Lost connection to server. Please reconnect.")

def receive_messages(canvas, status_label):
    # Runs the entire time the client is connected.
    global sock
    while sock:   # Run while connection is not closed
        try:
            # Receive message length prefix
            length_prefix = sock.recv(4)
            if not length_prefix:
                print("Server disconnected.")
                break
            
            # Convert length prefix to integer
            message_length = int.from_bytes(length_prefix, 'big')
            
            # Receive message
            message_bytes = b''
            while len(message_bytes) < message_length:
                # Receive chunk of message
                chunk = sock.recv(message_length - len(message_bytes))
                if not chunk:
                    raise socket.error("Server disconnected during message receive")
                message_bytes += chunk

            # Decode message
            message_json = message_bytes.decode('utf-8')
            message = json.loads(message_json)

            # Handle received commands based on their type
            msg_type = message.get('type')
            if msg_type == 'draw':
                canvas.after_idle(draw_command, canvas, message)
            elif msg_type == 'clear':
                canvas.after_idle(clear_command, canvas)
            elif msg_type == 'system':
                status_label.after_idle(lambda: status_label.config(
                    text=f"Connected to {HOST}:{PORT} - {message.get('message')}",
                    fg="green"
                ))

        except socket.error as e:
            print(f"Socket error receiving: {e}")
            break
        except json.JSONDecodeError:
            print("Invalid JSON received from server.")
        except Exception as e:
            print(f"Unexpected error receiving message: {e}")
            break 

    print("Receive thread exiting.")
    canvas.after_idle(lambda: close_connection(status_label))

# Connection functions 

def connect_to_server(canvas, status_label):
    global sock, HOST
    if sock is None:
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to server
            sock.connect((HOST, PORT))

            # Update status label
            status_label.config(text=f"Connected to {HOST}:{PORT}", fg="green")
            print(f"Successfully connected to {HOST}:{PORT}")

            # Start receive thread 
            receive_thread = threading.Thread(target=receive_messages, args=(canvas, status_label), daemon=True)
            receive_thread.start()

        except socket.error as e:
            # Close socket
            sock = None
            # Update status label
            error_msg = f"Failed to connect: {e}"
            status_label.config(text=error_msg, fg="red")
            print(error_msg)
            messagebox.showerror("Connection Error", f"Could not connect to {HOST}:{PORT}\n{e}")
    else:
        print("Already connected.")

def close_connection(status_label=None):
    global sock
    if sock:
        try:
            # Shutdown socket
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            # Close socket
            sock.close()
            sock = None
            print("Connection closed.")
            if status_label:
                status_label.config(text="Disconnected", fg="red")

# draw command (called when receiving data from server)
def draw_command(canvas, command):
    # Draws a line segment based on message received from server
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

# Clear command
def clear_command(canvas):
    canvas.delete("all")

# mouse event handlers
last_x, last_y = None, None

# Set coordinates on mouse press
def mouse_down(event):
    global last_x, last_y
    last_x, last_y = (event.x, event.y)

# Draws line segment locally, then sends draw message to server
def mouse_drag(event, canvas):
    global last_x, last_y, drawing_color, line_width

    if last_x is not None and last_y is not None:   # If mouse still down
        # Draw line segment locally
        canvas.create_line(last_x, last_y, event.x, event.y,
                          fill=drawing_color, width=line_width,
                          capstyle=tk.ROUND, smooth=tk.TRUE)

        # Prepare message to send
        draw_message = {
            'type': 'draw',
            'x1': last_x, 'y1': last_y,
            'x2': event.x, 'y2': event.y,
            'color': drawing_color, 'width': line_width
        }
        send_message(draw_message)

        # Update last position
        last_x, last_y = event.x, event.y

# Reset coordinates on mouse unpress
def on_mouse_up(event):
    global last_x, last_y
    last_x, last_y = None, None
    
    
# Color selection
def set_color(new_color):
    global drawing_color
    drawing_color = new_color
    print(f"Color set to: {drawing_color}")

# Width selection
def set_width(new_width):
    global line_width
    line_width = new_width
    print(f"Width set to: {line_width}")


def main():
    root = tk.Tk()
    root.title(f"Collaborative Drawing Board - {HOST}:{PORT}")

    # --- Menu Bar ---
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    connection_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Connection", menu=connection_menu)
    
    # --- Control Frame ---
    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # Connection Status Label with more details
    status_label = tk.Label(control_frame, text="Disconnected", fg="red")
    status_label.pack(side=tk.LEFT, padx=5)

    # Server IP Entry
    ip_var = tk.StringVar(value=HOST)
    ip_label = tk.Label(control_frame, text="Server IP:")
    ip_label.pack(side=tk.LEFT, padx=2)
    ip_entry = tk.Entry(control_frame, textvariable=ip_var, width=15)
    ip_entry.pack(side=tk.LEFT, padx=2)
    
    def update_host():
        global HOST
        HOST = ip_var.get()
        root.title(f"Collaborative Drawing Board - {HOST}:{PORT}")
    
    ip_entry.bind('<Return>', lambda e: update_host())
    
    # Connect button with updated command
    connect_button = tk.Button(control_frame, text="Connect", 
                             command=lambda: (update_host(), connect_to_server(canvas, status_label)))
    connect_button.pack(side=tk.LEFT, padx=5)

    # Disconnect button
    disconnect_button = tk.Button(control_frame, text="Disconnect", 
                                command=lambda: close_connection(status_label))
    disconnect_button.pack(side=tk.LEFT, padx=5)

    # --- Drawing Canvas ---
    canvas = tk.Canvas(root, bg="white", width=800, height=600)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Color Buttons in a separate frame
    colors_frame = tk.Frame(control_frame)
    colors_frame.pack(side=tk.LEFT, padx=5)
    
    colors = ["black", "red", "green", "blue", "yellow", "orange", "purple", "white"]
    for color in colors:
        btn = tk.Button(colors_frame, bg=color, width=2, command=lambda c=color: set_color(c))
        btn.pack(side=tk.LEFT, padx=2)

    # Width Scale
    width_scale = tk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL, 
                          label="Width", command=lambda w: set_width(int(w)))
    width_scale.set(line_width)
    width_scale.pack(side=tk.LEFT, padx=5)

    # Clear button
    clear_button = tk.Button(control_frame, text="Clear All", 
                            command=lambda: (clear_command(canvas), send_message({"type": "clear"})))
    clear_button.pack(side=tk.LEFT, padx=5)

    # Mouse bindings
    canvas.bind("<Button-1>", mouse_down)
    canvas.bind("<B1-Motion>", lambda event: mouse_drag(event, canvas))
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            close_connection(status_label)
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 