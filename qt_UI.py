from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
	QMessageBox, QListWidget, QTextEdit, QComboBox, QScrollArea
)
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QTimer
import sys
from chat_client_logic import ChatAppLogic
from protocol import *
from messagebox import PushNotification

class ChatAppGUI(ChatAppLogic, QMainWindow):
	def __init__(self):
		super().__init__()
		QMainWindow.__init__(self)
		self.current_user = None
		self.chat_mode = "group"
		self.login_screen = None
		self.login_username = None
		self.setWindowTitle("Chat App")
		self.setGeometry(100, 100, 600, 600)
		self.chat_list = None
		self.chat_display = None
		self.user_input = None
		self.most_recent_id = None
		self.loading_period = 1
		self.tagging = True
		self.current_language = "English"
		self.current_chat = None
		self.requests_mode = None

		self.open_login_screen()

	def open_login_screen(self):
		self.login_screen = QWidget()
		self.setCentralWidget(self.login_screen)

		layout = QVBoxLayout()

		self.login_username = QLineEdit()
		self.login_username.setPlaceholderText("Enter username")
		layout.addWidget(self.login_username)

		self.login_password = QLineEdit()
		self.login_password.setPlaceholderText("Enter password")
		self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
		layout.addWidget(self.login_password)

		login_button = QPushButton("Login")
		login_button.clicked.connect(self.login_user)
		layout.addWidget(login_button)

		register_button = QPushButton("Register")
		register_button.clicked.connect(self.register_user)
		layout.addWidget(register_button)

		self.login_screen.setLayout(layout)
		print("created login window")

	def login_user(self):
		username = self.login_username.text().strip()
		password = self.login_password.text()
		if username:
			response = self.send_request("login", {"username": username, "password": password})
			if response["status"] == "success":
				self.current_user = username
				QMessageBox.information(self, "Success", response["message"])
				self.open_chat_window()
			else:
				QMessageBox.critical(self, "Error", response.get("message", "Unknown error."))
		else:
			QMessageBox.critical(self, "Error", "Username cannot be empty.")

	def switch_chat_mode(self, mode):
		logger.info(f"[GUI] on switch_chat_mode mode is {mode}")
		self.chat_mode = mode
		self.load_chats()

	def load_chats(self):
		try:
			logger.info(f"[GUI] on load_chats started loading chats mode {self.chat_mode}")
			self.chat_list.clear()
			if self.chat_mode == "group":
				response = self.send_request("get_groups")
				groups = response.get("groups", ["No groups available."])
				self.chat_list.addItems(groups)
			elif self.chat_mode == "personal":
				response = self.send_request("get_users")
				users = [user for user in response.get("users", []) if user != self.current_user]
				self.chat_list.addItems(users or ["No users available for personal chat."])
		except Exception as e:
			logger.error(f"[GUI] error on load_chats is {e}")

	def automatic_load(self):
		QTimer.singleShot(self.loading_period * 1000, self.load_chats)

	def send_message(self):
		recipient = self.current_chat
		content = self.user_input.toPlainText().strip()
		if not recipient or not content:
			QMessageBox.critical(self, "Error", "Please select a chat and enter a message.")
			return

		action = "send_group_message" if self.chat_mode == "group" else "send_personal_message"
		data = {
			"group_name" if self.chat_mode == "group" else "receiver": recipient,
			"sender": self.current_user,
			"content": content,
			"language": self.current_language
		}
		response = self.send_request(action, data)
		if response["status"] == "success":
			self.load_messages_GUI(recipient)
			self.user_input.clear()
		else:
			QMessageBox.critical(self, "Error", response.get("message", "Unknown error."))

	def pack_tags(self, words, tags):
		# print(f"packing tags: words are {words}, tags are {tags}")
		return [(words[i], tags[i]) for i in range(len(words))]

	def load_messages_GUI(self, chat_name):
		self.current_chat = chat_name
		self.chat_display.clear()
		messages = self.load_messages(chat_name)
		custom_log(f"[CLIENT] on load_messages_GUI: started loading messages")

		cursor = self.chat_display.textCursor()
		cursor.movePosition(QTextCursor.MoveOperation.Start)
		end_cursor = self.chat_display.textCursor()
		
		if self.tagging:
			for message in messages:
				custom_log(f"[CLIENT] on load_messages_GUI: started loading message {message}")
				sender, timestamp, content, POS_tags = message
				cursor.movePosition(QTextCursor.MoveOperation.End)

				if POS_tags:
					parsed_text = self.pack_tags(content.split(), POS_tags.split())

					# cursor.movePosition(QTextCursor.MoveOperation.End)
					for word, POS_tag in parsed_text:
						# self.chat_display.insertPlainText(f'<{POS_tag}>{word}</{POS_tag}> ')
						if POS_tag == "PUNCT" and word != "—":
							cursor.deletePreviousChar()

						text_format = QTextCharFormat()
						text_format.setForeground(QColor(POS_color_map[POS_tag]))
						cursor.mergeCharFormat(text_format)
						position_start = cursor.position()
						cursor.insertText(f'{word} ')
						# custom_log(f"[CLIENT] on load_messages_GUI tag-coloring: word is {word}")
						# custom_log(f"Selected text is {cursor.selectedText()}, POS_tag is {POS_tag}, POS_color is {POS_color_map[POS_tag]}")
					cursor.movePosition(QTextCursor.MoveOperation.End)
					text_format = QTextCharFormat()
					text_format.setForeground(QColor("white"))	
					cursor.mergeCharFormat(text_format)
					cursor.insertText(f"\n{timestamp}\n\n")

					# self.chat_display.append(f"\n{timestamp}\n")
					custom_log(f"[CLIENT] on load_messages_GUI: message is loaded tagged")

				else:
					custom_log(f"[CLIENT] on load_messages_GUI: message is loaded monotone")
					self.load_message_monotone(message)
		else:
			for message in messages:
				self.load_message_monotone(message)

	def load_message_monotone(self, message):
		sender, timestamp, content, POS_tags = message
		self.chat_display.append(f"{sender}: {content}\n{timestamp}\n")

	def load_more(self):
		def insert_text_at_beginning(text, display):
			current_text = display.toPlainText()
			display.setPlainText(text + current_text)

		messages = self.load_messages(self.current_chat, True)
		cursor = self.chat_display.textCursor()
		cursor.movePosition(QTextCursor.MoveOperation.Start)
		# cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, len + 1)
		for sender, timestamp, content, POS_tags in messages:
			if POS_tags:
				cursor.insertText(f"{sender}\n")
				words = self.pack_tags(content.split(), POS_tags.split())
				for word, POS_tag in words:
					text_format = QTextCharFormat()
					text_format.setForeground(QColor(POS_color_map[POS_tag]))
					cursor.mergeCharFormat(text_format)
					cursor.insertText(f"{word} ")

				text_format.setForeground(QColor(POS_color_map[POS_tag]))
				cursor.mergeCharFormat(text_format)			
				cursor.insertText(f"\n{timestamp}\n\n")
			else:
				insert_text_at_beginning(f"{sender}: {content}\n{timestamp}\n", self.chat_display)


	def open_chat_window(self):
		central_widget = QWidget()
		self.setCentralWidget(central_widget)

		main_layout = QVBoxLayout(central_widget)

		mode_frame = QHBoxLayout()
		main_layout.addLayout(mode_frame)

		mode_label = QLabel("Chat Mode:")
		mode_frame.addWidget(mode_label)

		mode_selector = QComboBox()
		mode_selector.addItems(["Group", "Personal"])
		mode_selector.setCurrentIndex(0)
		mode_selector.currentIndexChanged.connect(lambda: self.switch_chat_mode(mode_selector.currentText().lower()))
		mode_frame.addWidget(mode_selector)

		chat_layout = QHBoxLayout()
		main_layout.addLayout(chat_layout)

		self.chat_list = QListWidget()
		self.chat_list.itemSelectionChanged.connect(lambda: self.load_messages_GUI(self.chat_list.currentItem().text()))
		chat_layout.addWidget(self.chat_list)

		right_layout = QVBoxLayout()
		chat_layout.addLayout(right_layout)

		top_bar_frame = QHBoxLayout()
		right_layout.addLayout(top_bar_frame)

		mistakes_button = QPushButton("Mistakes")
		mistakes_button.clicked.connect(self.open_mistakes_window)
		top_bar_frame.addWidget(mistakes_button)

		profile_button = QPushButton("Profile")
		profile_button.clicked.connect(self.open_profile)
		top_bar_frame.addWidget(profile_button)

		more_messages_button = QPushButton("More messages")
		more_messages_button.clicked.connect(self.load_more)
		top_bar_frame.addWidget(more_messages_button)

		requests_button = QPushButton("Requests")
		requests_button.clicked.connect(self.open_requests_window)
		top_bar_frame.addWidget(requests_button)

		make_group_button = QPushButton("Make group")
		make_group_button.clicked.connect(self.open_group_creation_window)
		top_bar_frame.addWidget(make_group_button)

		self.chat_display = QTextEdit()
		self.chat_display.setReadOnly(True)
		right_layout.addWidget(self.chat_display)

		input_frame = QHBoxLayout()
		main_layout.addLayout(input_frame)

		self.user_input = QTextEdit()
		input_frame.addWidget(self.user_input)

		send_button = QPushButton("Send")
		send_button.clicked.connect(self.send_message)
		input_frame.addWidget(send_button)

		self.language_selector = QComboBox()
		self.language_selector.addItems(languages)
		self.language_selector.currentIndexChanged.connect(lambda: self.choose_language(self.language_selector.currentText()))
		input_frame.addWidget(self.language_selector)

		self.load_chats()

	def accept_request(self):
		response = self.send_request("accept_request", {"receiver": self.current_user, "sender": self.chosen_request})

	def load_request_data(self, request):
		self.chosen_request = request
		self.send_request("load_request", {"requester": request})
	
	def open_requests_window(self):
		def make_request():
			name = self.request_input.text()
			response = self.send_request("make_request", {"sender": self.current_user, "receiver": name})
			QMessageBox.information("Request sent")
			# messagebox.showinfo("request result", f"make_request status: {response['status']}")

		self.requests_window = QWidget()
		self.requests_window.setWindowTitle("Requests")
		self.requests_window.resize(800, 450)
		
		layout = QVBoxLayout()

		mode_selector = QComboBox()
		mode_selector.addItems(["Incoming", "Outgoing"])
		mode_selector.setCurrentIndex(0)
		mode_selector.currentIndexChanged.connect(lambda: self.switch_request_mode(mode_selector.currentText().lower()))
		layout.addWidget(mode_selector)

		self.requests_list = QListWidget()
		self.requests_list.itemSelectionChanged.connect(lambda: self.load_request_data(self.requests_list.currentItem().text()))
		layout.addWidget(self.requests_list)

		self.request_display = QTextEdit()
		self.request_display.setReadOnly(True)
		layout.addWidget(self.request_display)

		self.request_input = QLineEdit()
		layout.addWidget(self.request_input)

		self.send_request_button = QPushButton("Send request")
		self.send_request_button.setStyleSheet("background-color: #0078D7; color: white;")
		self.send_request_button.clicked.connect(make_request)
		layout.addWidget(self.send_request_button)

		self.accept_request_button = QPushButton("Accept request")
		self.accept_request_button.setStyleSheet("background-color: #0078D7; color: white;")
		self.accept_request_button.clicked.connect(self.accept_request)
		layout.addWidget(self.accept_request_button)

		self.requests_window.setLayout(layout)
		self.requests_window.show()
		self.requests_mode = "Incoming"
		self.load_requests()

	def open_group_creation_window(self):
		def make_group():
			name = self.group_entry.text().strip()
			selected_users = [item.text() for item in self.users_list.selectedItems()]
			# QMessageBox.information(self, "group status", self.send_request("create_group", {"name": name, "users": selected_users}))
			# item.text() for item in lang_list.selectedItems()
			self.groups_window.close()

		self.groups_window = QWidget()
		self.groups_window.setWindowTitle("Creating a group")
		self.groups_window.resize(800, 450)

		layout = QVBoxLayout()

		group_label = QLabel("Group name:")
		layout.addWidget(group_label)

		self.group_entry = QLineEdit()
		layout.addWidget(self.group_entry)

		self.users_list = QListWidget()
		self.users_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
		layout.addWidget(self.users_list)

		response = self.send_request("get_users")
		self.users_list.addItems(response["users"])

		submit_button = QPushButton("Submit")
		submit_button.clicked.connect(make_group)
		layout.addWidget(submit_button)

		self.groups_window.setLayout(layout)
		self.groups_window.show()

	def load_requests(self):
		self.requests_list.clear()
		response = self.send_request("get_requests", {"user": self.current_user, "mode": self.requests_mode})
		requests = response.get("requesters", [])
		requests_names = [request[0] for request in requests] # names
		self.requests_list.addItems(requests_names)

	def load_mistake_data(self, mistake_header):
		# self.mistake_display.config(state=tk.NORMAL)
		# self.mistake_display.delete(1.0, tk.END)

		ID = int(mistake_header.split()[1])
		
		response = self.send_request("load_typo_message", {"id": ID})

		self.mistake_display.clear()
		self.mistake_display.insertPlainText(f"{response['receiver']}:")
		self.mistake_display.insertPlainText(f"{response['content_start']}")
		self.mistake_display.insertPlainText(f" {response['content_mistake'].upper()} ")
		self.mistake_display.insertPlainText(f"{response['content_end']}\n")
		self.mistake_display.insertPlainText(f"{response['corrected_word']}\n")
		self.mistake_display.insertPlainText(f"{response['timestamp']}\n")

		self.mistake_display.insertPlainText("the end\n")
		# self.mistake_display.config(state=tk.DISABLED)

	def open_mistakes_window(self):
		self.mistakes_window = QWidget()
		self.mistakes_window.setWindowTitle("Mistakes")
		self.mistakes_window.resize(800, 450)

		layout = QVBoxLayout()

		self.mistakes_list = QListWidget()
		self.mistakes_list.itemSelectionChanged.connect(lambda: self.load_mistake_data(self.mistakes_list.currentItem().text()))
		layout.addWidget(self.mistakes_list)

		self.mistake_display = QTextEdit()
		self.mistake_display.setReadOnly(True)
		layout.addWidget(self.mistake_display)

		understood_button = QPushButton("Understood")
		understood_button.clicked.connect(self.send_message)
		layout.addWidget(understood_button)

		self.mistakes_window.setLayout(layout)
		self.mistakes_window.show()
		self.load_mistakes()

	def load_mistakes(self):
		response = self.send_request("get_mistakes", {"sender": self.current_user})
		typos = response.get("typos", [])
		mistakes_names = [f"typo {typo[0]} message {typo[1]} wrong word num {typo[2]}" for typo in typos]
		logger.info(f"[CLIENT] ready to show mistakes {mistakes_names}")
		self.mistakes_list.addItems(mistakes_names)

	def populate_language_list(self, lang_list):
		for language in languages:
			lang_list.addItem(language)

	def register_user(self):
		def submit_registration():
			username = username_entry.text().strip()
			password = password_entry.text()
			selected_languages = [item.text() for item in lang_list.selectedItems()]
			print(f"selected_languages are {selected_languages}")
			if not username:
				QMessageBox.critical(self, "Error", "Username cannot be empty.")
				return
			if not password:
				QMessageBox.critical(self, "Error", "Password cannot be empty")
				return
			if not selected_languages:
				QMessageBox.critical(self, "Error", "You must select at least one language.")
				return

			response = self.send_request("register", {"username": username, "password": password, "languages": selected_languages})
			if response["status"] == "success":
				QMessageBox.information(self, "Success", "Registration successful.")
				register_window.close()
			else:
				QMessageBox.critical(self, "Error", response.get("message", "Unknown error."))

		register_window = QWidget()
		register_window.setWindowTitle("Register")

		layout = QVBoxLayout()

		username_label = QLabel("Username:")
		layout.addWidget(username_label)
		username_entry = QLineEdit()
		layout.addWidget(username_entry)

		password_label = QLabel("Password:")
		layout.addWidget(password_label)
		password_entry = QLineEdit()
		password_entry.setEchoMode(QLineEdit.EchoMode.Password)
		layout.addWidget(password_entry)

		lang_label = QLabel("Select Languages:")
		layout.addWidget(lang_label)

		lang_list = QListWidget()
		lang_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
		self.populate_language_list(lang_list)
		layout.addWidget(lang_list)

		register_button = QPushButton("Register")
		register_button.clicked.connect(submit_registration)
		layout.addWidget(register_button)

		register_window.setLayout(layout)
		register_window.show()

	def open_profile(self):
		self.profile_screen = QWidget()
		self.profile_screen.setWindowTitle("Profile")
		self.profile_screen.resize(400, 300)

		layout = QVBoxLayout()

		username_label = QLabel(f"Username: {self.current_user}")
		layout.addWidget(username_label)

		languages_label = QLabel("Languages:")
		layout.addWidget(languages_label)

		language_list = QListWidget()
		languages = self.get_languages()
		language_list.addItems(languages)
		layout.addWidget(language_list)

		self.profile_screen.setLayout(layout)
		self.profile_screen.show()

if __name__ == "__main__":
	try:
		app = QApplication(sys.argv)
		GUI = ChatAppGUI()
		print(GUI)
		GUI.show()
		sys.exit(app.exec())
	except Exception as e:
		custom_log(f"[CLIENT] error {e} happened")