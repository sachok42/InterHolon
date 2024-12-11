import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
from protocol import *

server_address = ("127.0.0.1", 12345)  # Adjust as needed

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
    def submit_registration():
        username = username_entry.get().strip()
        selected_languages = [lang_list.get(i) for i in lang_list.curselection()]
        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return
        if not selected_languages:
            messagebox.showerror("Error", "You must select at least one language.")
            return

        response = send_request("register", {"username": username, "languages": selected_languages})
        if response["status"] == "success":
            messagebox.showinfo("Success", "Registration successful.")
            register_window.destroy()
        else:
            messagebox.showerror("Error", response["message"])

    register_window = tk.Toplevel(login_screen)
    register_window.title("Register")

    tk.Label(register_window, text="Username:").pack()
    username_entry = tk.Entry(register_window)
    username_entry.pack()

    tk.Label(register_window, text="Select Languages:").pack()
    lang_list = tk.Listbox(register_window, selectmode=tk.MULTIPLE)
    for family, langs in LANGUAGE_TREE.items():
        if isinstance(langs, dict):
            for subfamily, sublangs in langs.items():
                lang_list.insert(tk.END, f"{family} → {subfamily}")
                for lang in sublangs:
                    lang_list.insert(tk.END, f"   {lang}")
        else:
            lang_list.insert(tk.END, family)
    lang_list.pack()

    tk.Button(register_window, text="Register", command=submit_registration).pack()


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

# Switch chat mode
def switch_mode(mode):
	global chat_mode
	chat_mode = mode
	if chat_mode == "group":
		load_groups()
	elif chat_mode == "personal":
		load_users()

# Load group chats
def load_groups():
	chat_list.delete(0, tk.END)
	groups = base_groups
	if groups:
		for group in groups:
			chat_list.insert(tk.END, group)
	else:
		chat_list.insert(tk.END, "No groups available.")

# Load user list for personal chats
def load_users():
	chat_list.delete(0, tk.END)
	response = send_request("get_users", {})
	if response["status"] == "success" and response["users"]:
		for user in response["users"]:
			if user != current_user:  # Exclude current user
				chat_list.insert(tk.END, user)
	else:
		chat_list.insert(tk.END, "No users available for personal chat.")

# Send a message
def send_message():
	recipient = chat_list.get(chat_list.curselection())
	content = user_input.get().strip()
	
	if not recipient or not content:
		messagebox.showerror("Invalid entry", "Ensure all inputs")
	
	if not recipient or not content:
		messagebox.showerror("Error", "Please select a chat and enter a message.")
		return

	if chat_mode == "group":
		response = send_request("send_group_message", {
			"group_name": recipient,
			"sender": current_user,
			"content": content
		})
	elif chat_mode == "personal":
		response = send_request("send_personal_message", {
			"sender": current_user,
			"receiver": recipient,
			"content": content
		})

	if response["status"] == "success":
		load_messages(recipient)
		user_input.delete(0, tk.END)
	else:
		messagebox.showerror("Error", response["message"])

# Load chat messages
def load_messages(chat_name):
	if not chat_name:
		messagebox.showerror("Error", "No chat selected.")
		return

	chat_display.config(state=tk.NORMAL)
	chat_display.delete(1.0, tk.END)

	if chat_mode == "group":
		response = send_request("get_group_messages", {"group_name": chat_name})
	elif chat_mode == "personal":
		response = send_request("get_personal_messages", {"user1": current_user, "user2": chat_name})

	if response["status"] == "success":
		for sender, content in response["messages"]:
			chat_display.insert(tk.END, f"{sender}: {content}\n")
	else:
		messagebox.showerror("Error", response["message"])

	chat_display.config(state=tk.DISABLED)

# Update the chat list selection event
def on_chat_select(event):
	try:
		for idx in range(chat_list.size()):
			chat_list.itemconfig(idx, bg="white")  # Reset background color
		selected_idx = chat_list.curselection()[0]
		chat_list.itemconfig(selected_idx, bg="#d3d3d3")  # Highlight selected chat
		selected_chat = chat_list.get(selected_idx)
		load_messages(selected_chat)
	except tk.TclError:
		pass

# Chat window
def open_chat_window():
	global chat_mode, chat_list, chat_display, user_input

	chat_mode = "group"
	root = tk.Tk()
	root.title(f"Chat App - Logged in as {current_user}")
	root.geometry("600x600")

	# Top frame: mode selection
	mode_frame = tk.Frame(root)
	mode_frame.pack(fill=tk.X)

	tk.Label(mode_frame, text="Chat Mode:").pack(side=tk.LEFT, padx=10)
	mode_selector = ttk.Combobox(mode_frame, values=["Group", "Personal"], state="readonly")
	mode_selector.pack(side=tk.LEFT)
	mode_selector.current(0)
	mode_selector.bind("<<ComboboxSelected>>", lambda e: switch_mode(mode_selector.get().lower()))

	# Middle frame: chat list and messages
	main_frame = tk.Frame(root)
	main_frame.pack(expand=True, fill=tk.BOTH)

	chat_list = tk.Listbox(main_frame, width=20)
	chat_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
	chat_list.bind("<<ListboxSelect>>", lambda e: load_messages(chat_list.get(chat_list.curselection())))

	chat_display = scrolledtext.ScrolledText(main_frame, state=tk.DISABLED, wrap=tk.WORD)
	chat_display.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)

	# Bottom frame: message input
	input_frame = tk.Frame(root)
	input_frame.pack(fill=tk.X, padx=5, pady=5)

	user_input = tk.Entry(input_frame, font=("Arial", 14))
	user_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
	tk.Button(input_frame, text="Send", command=send_message, bg="#0078D7", fg="white").pack(side=tk.RIGHT)

	load_groups()  # Load default mode

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
	tk.Button(login_screen, text="Login", command=login_user).pack(pady=10)

	tk.Label(login_screen, text="Register", font=("Arial", 14)).pack(pady=10)
	register_username = tk.Entry(login_screen, font=("Arial", 12))
	register_username.pack(pady=5)
	tk.Button(login_screen, text="Register", command=register_user).pack(pady=10)

	login_screen.mainloop()

current_user = None
open_login_screen()
