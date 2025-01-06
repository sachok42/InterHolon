import socket
import threading
import sqlite3
import json
from protocol import *

class ChatServer:
	def __init__(self, host="0.0.0.0", port=12345):
		self.host = host
		self.port = port
		self.initialize_db()

	def initialize_db(self):
		with sqlite3.connect("chat_server.db") as conn:
			cursor = conn.cursor()
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT UNIQUE NOT NULL
				)
			""")
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS groups (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					name TEXT UNIQUE NOT NULL
				)
			""")
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS messages (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					chat_type TEXT CHECK(chat_type IN ('group', 'personal')),
					chat_id INTEGER,
					sender TEXT,
					receiver TEXT,
					content TEXT,
					timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
					FOREIGN KEY (chat_id) REFERENCES groups (id),
					FOREIGN KEY (receiver) REFERENCES users (username)
				)
			""")
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS user_languages (
					user_id INTEGER,
					language TEXT,
					PRIMARY KEY (user_id, language),
					FOREIGN KEY (user_id) REFERENCES users (id)
				)
			""")
			for group_name in base_groups:
				cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (group_name,))

	@staticmethod
	def find_related_languages(language):
		related_languages = set()
		def traverse(tree, target):
			for key, value in tree.items():
				if key == target:
					related_languages.update(value if isinstance(value, list) else [])
					return True
				if isinstance(value, dict) and traverse(value, target):
					related_languages.add(key)
					related_languages.update(value if isinstance(value, list) else [])
					return True
			return False
		traverse(LANGUAGE_TREE, language)
		return related_languages

	def handle_client(self, client_socket):
		with sqlite3.connect("chat_server.db") as conn:
			cursor = conn.cursor()
			try:
				while True:
					request = client_socket.recv(1024).decode()
					if not request:
						break
					try:
						request_data = json.loads(request)
					except json.JSONDecodeError:
						client_socket.send(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
						continue

					action = request_data.get("action")
					response = self.process_request(cursor, conn, action, request_data)
					client_socket.send(json.dumps(response).encode())
			except Exception as e:
				print(f"Error: {e}")
			finally:
				client_socket.close()

	def process_request(self, cursor, conn, action, request_data):
		response = {"status": "error", "message": "Invalid action"}
		if action == "register":
			response = self.register_user(cursor, conn, request_data)
		elif action == "login":
			response = self.login_user(cursor, request_data)
		elif action == "send_group_message":
			response = self.send_group_message(cursor, conn, request_data)
		elif action == "send_personal_message":
			pass
		elif action == "get_group_messages":
			response = self.send_group_message(cursor, conn, request_data)
		elif action == "get_personal_messages":
			response = self.get_personal_messages(cursor, conn, request_data)
		elif action == "get_users":
			response = self.get_users(cursor, conn, request_data)
		# Add more actions as needed...
		logger.info(f"[SERVER] sent response: response is {response}")
		return response

	def get_group_messages(self, cursor, conn, request_data):
		cursor.execute("SELECT id FROM groups WHERE name = ?", (request_data["group_name"]))
		group_id = cursor.fetchone()
		cursor.execute("SELECT * FROM messages WHERE chat_type = 'group' AND groups = ?", (group_id))
		messages = cursor.fetchall()
		response = {"status": "success", "messages": messages}
		return response

	def get_personal_messages(self, cursor, conn, request_data):
		cursor.execute("SELECT * FROM messages WHERE sender = ? AND receiver = ?", (request_data["user1"], request_data["user2"],))
		sent = cursor.fetchall()
		cursor.execute("SELECT * FROM messages WHERE sender = ? AND receiver = ?", (request_data["user2"], request_data["user1"],))
		received = cursor.fetchall()
		response = {"status": "success", "received": received, "sent": sent, "all_messages": received + sent}
		return response

	def get_users(self, cursor, conn, request_data):
		cursor.execute("SELECT username FROM users")
		users = cursor.fetchall()
		response = {"status": "sucess", "users": users}
		return response

	def register_user(self, cursor, conn, request_data):
		username = request_data.get("username")
		languages = request_data.get("languages", [])
		if not username:
			return {"status": "error", "message": "Username cannot be empty."}
		if not languages:
			return {"status": "error", "message": "You must select at least one language."}
		try:
			cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
			user_id = cursor.lastrowid
			cursor.executemany(
				"INSERT INTO user_languages (user_id, language) VALUES (?, ?)",
				[(user_id, lang) for lang in languages]
			)
			conn.commit()
			return {"status": "success", "message": "Registration successful"}
		except sqlite3.IntegrityError:
			return {"status": "error", "message": "Username already exists."}

	def login_user(self, cursor, request_data):
		username = request_data.get("username")
		cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
		if cursor.fetchone():
			return {"status": "success", "message": "Login successful"}
		return {"status": "error", "message": "Invalid username"}

	def send_group_message(self, cursor, conn, request_data):
		group_name = request_data.get("group_name")
		sender = request_data.get("sender")
		content = request_data.get("content")
		cursor.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
		group_id = cursor.fetchone()
		if group_id:
			cursor.execute("""
				INSERT INTO messages (chat_type, chat_id, sender, content)
				VALUES ('group', ?, ?, ?)
			""", (group_id[0], sender, content))
			conn.commit()
			return {"status": "success", "message": "Message sent"}
		return {"status": "error", "message": "Group does not exist."}

	def start_server(self):
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.bind((self.host, self.port))
		server.listen(5)
		print(f"Server is listening on port {self.port}...")

		while True:
			client_socket, addr = server.accept()
			print(f"Connection established with {addr}")
			client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
			client_handler.start()

if __name__ == "__main__":
	server = ChatServer()
	server.start_server()
