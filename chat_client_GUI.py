from chat_client_logic import *
import time
from textblob import TextBlob


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
		self.most_recent_id = None
		self.loading_period = 1
		self.tagging = True

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

	def switch_chat_mode(self, mode):
		self.chat_mode = mode
		self.load_chats()

	def load_chats(self):
		self.chat_list.delete(0, tk.END)
		if self.chat_mode == "group":
			response = self.send_request("get_groups")
			groups = response.get("groups")
			groups = groups or ["No groups available."]
			self.chat_list.insert(tk.END, *groups)
		elif self.chat_mode == "personal":
			response = self.send_request("get_users")
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
		if self.tagging:
			for sender, content, timestamp in messages:
				print(f"Message is {sender}, {content}")
				self.chat_display.insert(tk.END, f"{sender}: ")
				blob = TextBlob(content)
				parsed_text = blob.parse().split()[0]
				print("parsed_text is", parsed_text)
				for word, POS_tag, something1, something2 in parsed_text:
					# word, POS_tag, something1, something2 = piece.split("/")
					self.chat_display.insert(tk.END, f"{word} ", POS_tag)
				self.chat_display.insert(tk.END, f"\n{timestamp}\n")
			for POS in POS_painting:
				self.chat_display.tag_config(POS, foreground=POS_painting[POS])
		else:
			print(f"Message is {sender}, {content}")
			for sender, content, timestamp in messages:
				self.chat_display.insert(tk.END, f"{sender}")
				self.chat_display.insert(tk.END, f": {content}\n")
				self.chat_display.insert(tk.END, f"{timestamp}\n")
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
		mode_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_chat_mode(mode_selector.get().lower()))

		main_frame = tk.Frame(self.root)
		main_frame.pack(expand=True, fill=tk.BOTH)
		self.chat_list = tk.Listbox(main_frame, width=20)
		self.chat_list.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
		self.chat_list.bind("<<ListboxSelect>>", lambda e: self.load_messages_GUI(self.chat_list.get(self.chat_list.curselection())))
		
		display_and_top_bar_frame = tk.Frame(main_frame)
		display_and_top_bar_frame.pack(expand=True, fill=tk.BOTH, side=tk.RIGHT)
		top_bar_frame = tk.Frame(display_and_top_bar_frame)
		top_bar_frame.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
		tk.Button(top_bar_frame, text="Mistakes", command=self.open_mistakes_window, bg="green", fg="white").grid(column=0, row=0, pady=10, padx=10)
		tk.Button(top_bar_frame, text="Profile", command=self.open_profile, bg="green", fg="white").grid(column=1, row=0, pady=10, padx=10)
		tk.Button(top_bar_frame, text="More messages", command=self.load_more, bg="#0078D7", fg="white").grid(column=2, row=0, pady=10, padx=10)
		tk.Button(top_bar_frame, text="Requests", command=self.open_requests_window, bg="#0078D7", fg="white").grid(column=3, row=0, pady=10, padx=10)
		tk.Button(top_bar_frame, text="Make group", command=self.open_group_creation_window, bg="blue", fg="white").grid(column=4, row=0, pady=10, padx=10)

		display_frame = tk.Frame(display_and_top_bar_frame)
		display_frame.pack(expand=True, fill=tk.BOTH, side=tk.BOTTOM)
		self.chat_display = scrolledtext.ScrolledText(display_frame, state=tk.DISABLED, wrap=tk.WORD)
		self.chat_display.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH, padx=5, pady=5)

		input_frame = tk.Frame(self.root)
		input_frame.pack(fill=tk.X, padx=5, pady=5)
		self.user_input = tk.Entry(input_frame, font=standard_font)
		self.user_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
		tk.Button(input_frame, text="Send", command=self.send_message, bg="#0078D7", fg="white").pack(side=tk.RIGHT)
		
		self.load_chats()
		self.root.mainloop()

	def switch_request_mode(self, mode):
		if mode == "incoming":
			self.accept_request_button.pack()
		elif mode == "outgoing":
			self.accept_request_button.pack_forget()
		self.requests_mode = mode
		self.load_requests()

	def load_request_data(self, request):
		self.chosen_request = request
		self.send_request("load_request", {"requester": request})

	def make_request(self):
		name = self.request_input.get()
		response = self.send_request("make_request", {"sender": self.current_user, "receiver": name})
		messagebox.showinfo("request result", f"make_request status: {response['status']}")

	def accept_request(self):
		response = self.send_request("accept_request", {"receiver": self.current_user, "sender": self.chosen_request})

	def open_requests_window(self):
		self.requests_window = tk.Toplevel(self.root)
		self.requests_window.title("Requests")
		self.requests_window.geometry("800x450")
		
		mode_selector = ttk.Combobox(self.requests_window, values=["Incoming", "Outgoing"], state="readonly")
		mode_selector.pack(side=tk.LEFT)
		mode_selector.current(0)
		mode_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_request_mode(mode_selector.get().lower()))
		self.requests_mode = "incoming"

		self.requests_frame = tk.Frame(self.requests_window)
		self.requests_frame.pack(expand=True, fill=tk.BOTH)
		self.requests_list = tk.Listbox(self.requests_frame)
		self.requests_list.pack(side=tk.LEFT)

		self.requests_list.bind("<<ListboxSelect>>", lambda e: self.load_request_data(self.requests_list.get(self.requests_list.curselection())))
		self.request_display = scrolledtext.ScrolledText(self.requests_frame, state=tk.DISABLED, wrap=tk.WORD)
		self.request_display.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)
		self.request_input = tk.Entry(self.requests_window, font=standard_font)
		self.request_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5, pady=5)
		self.send_request_button = tk.Button(self.requests_window, text="Send request", command=self.make_request, bg="#0078D7", fg="white")
		self.send_request_button.pack(side=tk.TOP)
		self.accept_request_button = tk.Button(self.requests_window, text="Accept request", command=self.accept_request, bg="#0078D7", fg="white")
		
		self.load_requests()


	def open_group_creation_window(self):
		def make_group():
			name = self.group_entry.get().strip()
			selected_users = [self.users_list.get(i) for i in self.users_list.curselection()]
			messagebox.showinfo("group status", self.send_request("create_group", {"name": name, "users": selected_users}))
			self.groups_window.destroy()

		self.groups_window = tk.Toplevel(self.root)
		self.groups_window.title("Creating a group")
		self.groups_window.geometry("800x450")

		tk.Label(self.groups_window, text="group_name")
		self.group_entry = tk.Entry(self.groups_window, font=standard_font)
		self.group_entry.pack()

		self.users_list = tk.Listbox(self.groups_window, selectmode=tk.MULTIPLE)
		self.users_list.pack()

		response = self.send_request("get_users")
		self.users_list.insert(tk.END, *response["users"])

		self.group_submit_button = tk.Button(self.groups_window, text="Submit", command=make_group, padx=5, pady=5)
		self.group_submit_button.pack()

	def load_requests(self):
		self.requests_list.delete(0, tk.END)
		response = self.send_request("get_requests", {"user": self.current_user, "mode": self.requests_mode})
		requests = response.get("requesters", [])
		requests_names = [request[0] for request in requests] # names
		self.requests_list.insert(tk.END, *requests_names)

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

		self.understood_button = tk.Button(self.mistakes_frame, text="Understood", command=self.send_message, padx=5, pady=5).pack()

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

		tk.Label(self.login_screen, text="Login", font=standard_font).pack(pady=10)
		self.login_username = tk.Entry(self.login_screen, font=("Arial", 12))
		self.login_username.pack(pady=5)
		tk.Label(self.login_screen, text="Password", font=standard_font).pack(pady=10)
		self.login_password = tk.Entry(self.login_screen, font=("Arial", 12))
		self.login_password.pack(pady=5)
		tk.Button(self.login_screen, text="Login", command=self.login_user).pack(pady=10)
		
		tk.Label(self.login_screen, text="Register", font=standard_font).pack(pady=10)
		tk.Button(self.login_screen, text="Register", command=self.register_user).pack(pady=10)

		self.login_screen.mainloop()

	def get_languages(self):
		response = self.send_request("get_languages", {"user1": self.current_user})
		return response["languages"]

	def open_profile(self):
		self.profile_screen = tk.Toplevel(self.root)
		self.profile_screen.title("Profile")
		self.profile_screen.geometry("400x300")

		tk.Label(self.profile_screen, text=f"Username: {self.current_user}", font=standard_font).pack(pady=10)
		languages = self.get_languages()
		language_list = tk.Listbox(self.profile_screen)
		# tk.END(language)
		language_list.pack()


if __name__ == "__main__":
	app = ChatAppGUI()
