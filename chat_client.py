import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
from protocol import *
import logging

class ChatApp:
	SERVER_ADDRESS = ("127.0.0.1", 12345)  # Adjust as needed

	def __init__(self):
		self.current_user = None
		self.chat_mode = "group"
		self.login_screen = None
		self.login_username = None
		self.root = None
		self.chat_list = None
		self.chat_display = None
		self.user_input = None

		logger.info("\n\nClient on")
		self.open_login_screen()

	def send_request(self, action, data={}):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
				logger.info(f"[USER] sent request: action is {action} data is {data}")
				client_socket.connect(self.SERVER_ADDRESS)
				request = {"action": action, **data}
				client_socket.send(json.dumps(request).encode())
				response = json.loads(client_socket.recv(1024).decode())
				logger.info(f"[USER] got response: {response}\n")
				return response
		except Exception as e:
			messagebox.showerror("Connection Error", f"An error occurred: {e}")
			return {"status": "error", "message": str(e)}


	def populate_language_list(self, lang_list):
		# for family, langs in LANGUAGE_TREE.items():
		# 	if isinstance(langs, dict):
		# 		for subfamily, sublangs in langs.items():
		# 			lang_list.insert(tk.END, f"{family} → {subfamily}")
		# 			for lang in sublangs:
		# 				lang_list.insert(tk.END, f"   {lang}")
		# 	else:
		# 		lang_list.insert(tk.END, family)
		for language in languages:
			lang_list.insert(tk.END, language)

	def login_user(self):
		username = self.login_username.get().strip()
		password = self.login_password.get()
		if username:
			response = self.send_request("login", {"username": username, "password": password})
			if response["status"] == "success":
				self.current_user = username
				messagebox.showinfo("Success", response["message"])
				self.login_screen.destroy()
				self.open_chat_window()
			else:
				messagebox.showerror("Error", response.get("message", "Unknown error."))
		else:
			messagebox.showerror("Error", "Username cannot be empty.")

	def switch_mode(self, mode):
		self.chat_mode = mode
		self.load_chats()

	def load_chats(self):
		self.chat_list.delete(0, tk.END)
		if self.chat_mode == "group":
			groups = base_groups or ["No groups available."]
			self.chat_list.insert(tk.END, *groups)
		elif self.chat_mode == "personal":
			response = self.send_request("get_users", {"user1": self.current_user})
			users = [user for user in response.get("users", []) if user != self.current_user]
			logger.info(f"[CLIENT] loading contacts, users are {users}")
			self.chat_list.insert(tk.END, *users or ["No users available for personal chat."])

	def send_message(self):
		try:
			recipient = self.chat_list.get(self.chat_list.curselection())
			content = self.user_input.get().strip()
			if not recipient or not content:
				messagebox.showerror("Error", "Please select a chat and enter a message.")
				return

			action = "send_group_message" if self.chat_mode == "group" else "send_personal_message"
			data = {
				"group_name" if self.chat_mode == "group" else "receiver": recipient,
				"sender": self.current_user,
				"content": content
			}
			response = self.send_request(action, data)
			if response["status"] == "success":
				self.load_messages(recipient)
				self.user_input.delete(0, tk.END)
			else:
				messagebox.showerror("Error", response.get("message", "Unknown error."))
		except tk.TclError:
			messagebox.showerror("Error", "Please select a chat.")

	def load_messages(self, chat_name):
		logger.info(f"[CLIENT] started loading messages from chat {chat_name}")
		self.chat_display.config(state=tk.NORMAL)
		self.chat_display.delete(1.0, tk.END)
		action = "get_group_messages" if self.chat_mode == "group" else "get_personal_messages"
		data = {
			"group_name" if self.chat_mode == "group" else "user2": chat_name,
			"user1": self.current_user
		}
		
		response = self.send_request(action, data)
		# logger.info(f"[CLIENT] loading messages from chat {chat_name} returned {response}")

		if response["status"] == "success":
			for sender, content, timestamp in response.get("messages", []):
				print(f"Message is {sender}, {content}")
				self.chat_display.insert(tk.END, f"{sender}: {content}\n{timestamp}\n")
		else:
			messagebox.showerror("Error", response.get("message", "Unknown error."))
		self.chat_display.config(state=tk.DISABLED)

	def open_chat_window(self):
		self.root = tk.Tk()
		self.root.title(f"Chat App - Logged in as {self.current_user}")
		self.root.geometry("600x600")

		mode_frame = tk.Frame(self.root)
		mode_frame.pack(fill=tk.X)
		tk.Label(mode_frame, text="Chat Mode:").pack(side=tk.LEFT, padx=10)
		mode_selector = ttk.Combobox(mode_frame, values=["Group", "Personal"], state="readonly")
		mode_selector.pack(side=tk.LEFT)
		mode_selector.current(0)
		mode_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_mode(mode_selector.get().lower()))

		main_frame = tk.Frame(self.root)
		main_frame.pack(expand=True, fill=tk.BOTH)
		self.chat_list = tk.Listbox(main_frame, width=20)
		self.chat_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
		self.chat_list.bind("<<ListboxSelect>>", lambda e: self.load_messages(self.chat_list.get(self.chat_list.curselection())))
		self.chat_display = scrolledtext.ScrolledText(main_frame, state=tk.DISABLED, wrap=tk.WORD)
		self.chat_display.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)

		input_frame = tk.Frame(self.root)
		input_frame.pack(fill=tk.X, padx=5, pady=5)
		self.user_input = tk.Entry(input_frame, font=("Arial", 14))
		self.user_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
		tk.Button(input_frame, text="Send", command=self.send_message, bg="#0078D7", fg="white").pack(side=tk.RIGHT)

		tk.Button(self.root, text="mistakes", command=self.open_mistakes_window, bg="green", fg="white").pack(side=tk.LEFT)
		
		self.load_chats()
		self.root.mainloop()

	def open_mistakes_window(self):
		self.mistakes_window = tk.Toplevel(self.root)
		self.mistakes_window.title("Register")
		self.mistakes_window.geometry("1600x900")

		self.mistakes_list = tk.Listbox(self.mistakes_window)
		self.mistakes_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

		self.understood_button = tk.Button(self.root, text="Understood", command=self.send_message, padx=5, pady=5).pack

		self.load_mistakes()

	def load_mistakes(self):
		response = self.send_request("get_mistakes", {"sender": self.current_user})
		typos = response.get("typos", [])
		mistakes_names = [f"typo {typo[0]} wrong word num {typo[1]}" for typo in typos]
		logger.info(f"[CLIENT] ready to show mistakes {mistakes_names}")
		self.mistakes_list.insert(tk.END, *mistakes_names)

	def register_user(self):
		def submit_registration():
			username = username_entry.get().strip()
			password = password_entry.get()
			selected_languages = [lang_list.get(i) for i in lang_list.curselection()]
			if not username:
				messagebox.showerror("Error", "Username cannot be empty.")
				return
			if not password:
				messagebox.showerror("Error", "Password cannot be empty")
			if not selected_languages:
				messagebox.showerror("Error", "You must select at least one language.")
				return

			response = self.send_request("register", {"username": username, "password": password, "languages": selected_languages})
			if response["status"] == "success":
				messagebox.showinfo("Success", "Registration successful.")
				register_window.destroy()
			else:
				messagebox.showerror("Error", response.get("message", "Unknown error."))

		register_window = tk.Toplevel(self.login_screen)
		register_window.title("Register")

		tk.Label(register_window, text="Username:").pack()
		username_entry = tk.Entry(register_window)
		username_entry.pack()
		tk.Label(register_window, text="Password:").pack()
		password_entry = tk.Entry(register_window)
		password_entry.pack()

		tk.Label(register_window, text="Select Languages:").pack()
		lang_list = tk.Listbox(register_window, selectmode=tk.MULTIPLE)
		self.populate_language_list(lang_list)
		lang_list.pack()

		tk.Button(register_window, text="Register", command=submit_registration).pack()

	def open_login_screen(self):
		self.login_screen = tk.Tk()
		self.login_screen.title("Login/Register")
		self.login_screen.geometry("400x300")

		tk.Label(self.login_screen, text="Login", font=("Arial", 14)).pack(pady=10)
		self.login_username = tk.Entry(self.login_screen, font=("Arial", 12))
		self.login_username.pack(pady=5)
		tk.Label(self.login_screen, text="Password", font=("Arial", 14)).pack(pady=10)
		self.login_password = tk.Entry(self.login_screen, font=("Arial", 12))
		self.login_password.pack(pady=5)
		tk.Button(self.login_screen, text="Login", command=self.login_user).pack(pady=10)
		
		tk.Label(self.login_screen, text="Register", font=("Arial", 14)).pack(pady=10)
		tk.Button(self.login_screen, text="Register", command=self.register_user).pack(pady=10)

		self.login_screen.mainloop()

if __name__ == "__main__":
	app = ChatApp()
