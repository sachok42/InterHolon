from chat_client_logic import *
import time


class ChatAppGUI(ChatAppLogic):
	def __init__(self):
		super(ChatAppGUI, self).__init__()
		self.current_user = None
		self.chat_mode = "group"
		self.login_screen = None
		self.login_username = None
		self.root = None
		self.chat_list = None
		self.chat_display = None
		self.user_input = None

		self.loading_period = 1

		self.open_login_screen()

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

	def automatic_load(self):
		time.sleep(self.loading_period)
		self.load_chats()

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
				self.load_messages_GUI(recipient)
				self.user_input.delete(0, tk.END)
			else:
				messagebox.showerror("Error", response.get("message", "Unknown error."))
		except tk.TclError:
			messagebox.showerror("Error", "Please select a chat.")

	def load_messages_GUI(self, chat_name):
		self.chat_name = chat_name
		self.chat_display.config(state=tk.NORMAL)
		self.chat_display.delete(1.0, tk.END)
		messages = self.load_messages(chat_name)
		for sender, content, timestamp in messages:
			print(f"Message is {sender}, {content}")
			self.chat_display.insert(tk.END, f"{sender}: {content}\n{timestamp}\n")
		self.chat_display.config(state=tk.DISABLED)

	def load_mistake_data(self, mistake_header):
		self.mistake_display.config(state=tk.NORMAL)
		self.mistake_display.delete(1.0, tk.END)

		ID = int(mistake_header.split()[1])
		
		response = self.send_request("load_typo_message", {"id": ID})

		self.mistake_display.insert(tk.END, f"{response['receiver']}:")
		self.mistake_display.insert(tk.END, f"{response['content_start']}")
		self.mistake_display.insert(tk.END, f" {response['content_mistake'].upper()} ")
		self.mistake_display.insert(tk.END, f"{response['content_end']}\n")
		self.mistake_display.insert(tk.END, f"{response['corrected_word']}\n")
		self.mistake_display.insert(tk.END, f"{response['timestamp']}\n")

		self.mistake_display.insert(tk.END, "the end\n")
		self.mistake_display.config(state=tk.DISABLED)

	def load_more(self):
		self.chat_display.config(state=tk.NORMAL)
		messages = self.load_messages(self.chat_name, True)
		for sender, content, timestamp in messages[-1::-1]:
			print(f"Message is {sender}, {content}")
			self.chat_display.insert(1.0, f"{sender}: {content}\n{timestamp}\n")

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
		self.chat_list.bind("<<ListboxSelect>>", lambda e: self.load_messages_GUI(self.chat_list.get(self.chat_list.curselection())))
		
		display_and_top_bar_frame = tk.Frame(main_frame)
		display_and_top_bar_frame.pack(expand=True, fill=tk.BOTH, side=tk.RIGHT)
		top_bar_frame = tk.Frame(display_and_top_bar_frame)
		top_bar_frame.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
		tk.Button(top_bar_frame, text="Mistakes", command=self.open_mistakes_window, bg="green", fg="white").grid(column=0, row=0, pady=5, padx=5)
		tk.Button(top_bar_frame, text="Profile", command=self.open_profile, bg="green", fg="white").grid(column=1, row=0, pady=5, padx=5)
		tk.Button(top_bar_frame, text="More messages", command=self.load_more, bg="#0078D7", fg="white").grid(column=2, row=0, pady=5, padx=5)

		display_frame = tk.Frame(display_and_top_bar_frame)
		display_frame.pack(expand=True, fill=tk.BOTH, side=tk.BOTTOM)
		self.chat_display = scrolledtext.ScrolledText(display_frame, state=tk.DISABLED, wrap=tk.WORD)
		self.chat_display.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, padx=5, pady=5)

		input_frame = tk.Frame(self.root)
		input_frame.pack(fill=tk.X, padx=5, pady=5)
		self.user_input = tk.Entry(input_frame, font=("Arial", 14))
		self.user_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
		tk.Button(input_frame, text="Send", command=self.send_message, bg="#0078D7", fg="white").pack(side=tk.RIGHT)
		
		self.load_chats()
		self.root.mainloop()

	def open_mistakes_window(self):
		self.mistakes_window = tk.Toplevel(self.root)
		self.mistakes_window.title("Mistakes")
		self.mistakes_window.geometry("800x450")

		self.mistakes_frame = tk.Frame(self.mistakes_window)
		self.mistakes_frame.pack(expand=True, fill=tk.BOTH)
		self.mistakes_list = tk.Listbox(self.mistakes_frame)
		self.mistakes_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

		self.mistakes_list.bind("<<ListboxSelect>>", lambda e: self.load_mistake_data(self.mistakes_list.get(self.mistakes_list.curselection())))
		self.mistake_display = scrolledtext.ScrolledText(self.mistakes_frame, state=tk.DISABLED, wrap=tk.WORD)
		self.mistake_display.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)

		self.understood_button = tk.Button(self.root, text="Understood", command=self.send_message, padx=5, pady=5).pack

		self.load_mistakes()

	def load_mistakes(self):
		response = self.send_request("get_mistakes", {"sender": self.current_user})
		typos = response.get("typos", [])
		mistakes_names = [f"typo {typo[0]} message {typo[1]} wrong word num {typo[2]}" for typo in typos]
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

	def get_languages(self):
		response = self.send_request("get_languages", {"user1": self.current_user})
		return response["languages"]

	def open_profile(self):
		self.profile_screen = tk.Toplevel(self.root)
		self.profile_screen.title("Profile")
		self.profile_screen.geometry("400x300")

		tk.Label(self.profile_screen, text=f"Username: {self.current_user}", font=("Arial", 14)).pack(pady=10)
		languages = self.get_languages()
		language_list = tk.Listbox(self.profile_screen)
		# tk.END(language)
		language_list.pack()


if __name__ == "__main__":
	app = ChatAppGUI()
