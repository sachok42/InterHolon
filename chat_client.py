import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import json

server_address = ("127.0.0.1", 12345)  # Change if the server is on another machine

# Function to send requests to the server
def send_request(action, data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(server_address)
        request = {"action": action}
        request.update(data)
        client_socket.send(json.dumps(request).encode())
        response = json.loads(client_socket.recv(1024).decode())
        return response

# Register a new user
def register_user():
    username = register_username.get().strip()
    if username:
        response = send_request("register", {"username": username})
        messagebox.showinfo("Response", response["message"])
    else:
        messagebox.showerror("Error", "Username cannot be empty.")

# Log in as a user
def login_user():
    global current_user
    username = login_username.get().strip()
    if username:
        response = send_request("login", {"username": username})
        if response["status"] == "success":
            current_user = username
            messagebox.showinfo("Success", response["message"])
            login_screen.destroy()
            open_chat_window()
        else:
            messagebox.showerror("Error", response["message"])
    else:
        messagebox.showerror("Error", "Username cannot be empty.")

# Switch chats and load messages
def switch_chat(chat_name):
    global current_chat
    current_chat = chat_name
    response = send_request("get_messages", {"chat_name": current_chat})
    if response["status"] == "success":
        chat_area.config(state=tk.NORMAL)
        chat_area.delete(1.0, tk.END)
        for sender, content in response["messages"]:
            tag = "user_message" if sender == current_user else "other_message"
            chat_area.insert(tk.END, f"{sender}: {content}\n", tag)
        chat_area.config(state=tk.DISABLED)

# Send a message
def send_message():
    message = user_input.get().strip()
    if message:
        response = send_request("send_message", {"chat_name": current_chat, "sender": current_user, "content": message})
        if response["status"] == "success":
            chat_area.config(state=tk.NORMAL)
            chat_area.insert(tk.END, f"{current_user}: {message}\n", "user_message")
            chat_area.config(state=tk.DISABLED)
            user_input.delete(0, tk.END)
            chat_area.see(tk.END)

# Open the chat window
def open_chat_window():
    global chat_area, user_input, header_label
    root = tk.Tk()
    root.title("Chat Client")
    root.geometry("600x700")

    # Header (top bar)
    header_frame = tk.Frame(root, bg="#0078D7", height=50)
    header_frame.pack(fill=tk.X)
    header_label = tk.Label(header_frame, text=f"{current_user} - Select a Chat", font=("Helvetica", 16), bg="#0078D7", fg="white")
    header_label.pack(side=tk.LEFT, padx=10)

    # Sidebar for chats
    sidebar_frame = tk.Frame(root, bg="#f5f5f5", width=150)
    sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
    tk.Label(sidebar_frame, text="Chats", font=("Arial", 12, "bold"), bg="#f5f5f5", fg="#333").pack(pady=10)

    for chat in ["Family", "Work", "Friends"]:
        tk.Button(sidebar_frame, text=chat, font=("Arial", 10), bg="white", relief=tk.FLAT,
                  command=lambda c=chat: switch_chat(c)).pack(fill=tk.X, padx=10, pady=5)

    # Main chat area
    main_frame = tk.Frame(root, bg="white")
    main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    chat_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#f5f5f5", font=("Arial", 12), relief=tk.FLAT)
    chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    chat_area.tag_configure("user_message", foreground="#0078D7", justify="right")
    chat_area.tag_configure("other_message", foreground="#333333", justify="left")

    # Input and send button
    input_frame = tk.Frame(main_frame, bg="white")
    input_frame.pack(fill=tk.X, padx=10, pady=10)
    user_input = tk.Entry(input_frame, font=("Arial", 14), bg="#f0f0f0", relief=tk.FLAT)
    user_input.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
    input_frame.columnconfigure(0, weight=1)

    send_button = tk.Button(input_frame, text="Send", command=send_message, bg="#0078D7", fg="white", font=("Arial", 12), relief=tk.FLAT)
    send_button.grid(row=0, column=1, padx=5)

    root.mainloop()

# Login/Register screen
def open_login_screen():
    global login_screen, login_username, register_username
    login_screen = tk.Tk()
    login_screen.title("Login/Register")
    login_screen.geometry("400x300")

    tk.Label(login_screen, text="Login", font=("Arial", 14)).pack(pady=10)
    login_username = tk.Entry(login_screen, font=("Arial", 12))
    login_username.pack(pady=5)
    tk.Button(login_screen, text="Login", command=login_user, font=("Arial", 12), bg="#0078D7", fg="white").pack(pady=10)

    tk.Label(login_screen, text="Register", font=("Arial", 14)).pack(pady=10)
    register_username = tk.Entry(login_screen, font=("Arial", 12))
    register_username.pack(pady=5)
    tk.Button(login_screen, text="Register", command=register_user, font=("Arial", 12), bg="#28A745", fg="white").pack(pady=10)

    login_screen.mainloop()

current_user = None
current_chat = None
open_login_screen()
