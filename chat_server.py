import socket
import threading
import sqlite3
import json
import numpy as np
from protocol import *
import pyscrypt
import random
import spellchecker
from Message import Message
from sql_db_init import sql_db_init

class ChatServer:
	def __init__(self, host="0.0.0.0", port=12345):
		self.host = host
		self.port = port

		self.conn = sqlite3.connect("chat_server.db")
		self.my_spellchecker = spellchecker.SpellChecker()
		logger.info("\n\nServer on")
		self.initialize_db()

	def initialize_db(self):
		with sqlite3.connect("chat_server.db") as conn:
			cursor = conn.cursor()
			sql_db_init(cursor)
			for group_name in base_groups:
				cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (group_name,))
			for language_name in languages:
				cursor.execute("INSERT OR IGNORE INTO languages (name) VALUES (?)", (language_name,))

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

	def get_user_id(self, conn, cursor, user):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT id FROM users WHERE username = ?
			""", (user,))
		user_id = cursor.fetchone()[0]
		logger.info(f"[SERVER] user {user} id {user_id}")
		return user_id

	def process_request(self, cursor, conn, action, request_data):
		response = {"status": "error", "message": "Invalid action"}
		logger.info(f"[SERVER] received request: action {action}, data {request_data}")
		if action == "register":
			response = self.register_user(cursor, conn, request_data)
		elif action == "login":
			response = self.login_user(cursor, request_data)
		elif action == "send_group_message":
			response = self.send_group_message(cursor, conn, request_data)
		elif action == "send_personal_message":
			response = self.send_personal_message(cursor, conn, request_data)
		elif action == "get_group_messages":
			response = self.get_group_messages(cursor, conn, request_data)
		elif action == "get_personal_messages":
			response = self.get_personal_messages(cursor, conn, request_data)
		elif action == "get_users":
			response = self.get_users(cursor, conn, request_data)
		elif action == "get_mistakes":
			response = self.get_mistakes(cursor, conn, request_data)
		# Add more actions as needed...
		logger.info(f"[SERVER] sent response: response is {response}")
		return response

	def get_mistakes(self, cursor, conn, request_data):
		# cursor = conn.cursor()
		logger.info(f"[SERVER] on get_mistakes started the function")
		cursor.execute("""
			SELECT message_id, word_number, corrected_word FROM typos WHERE user_id = ?
			""", (self.get_user_id(conn, cursor, request_data['sender']),))
		logger.info(f"[SERVER] on get_mistakes started fetching")
		typos = cursor.fetchall()
		logger.info(f"[SERVER] on get_mistakes: sender is {request_data['sender']} found mistakes are {typos}")
		response = {"status": "success", "typos": typos}
		return response

	def get_group_messages(self, cursor, conn, request_data):
		cursor = conn.cursor()
		logger.info(f"[SERVER] on get_group_messages: started id decryption, request_data {request_data}")		
		cursor.execute("SELECT id FROM groups WHERE name = ?", (request_data["group_name"],))
		group_id = cursor.fetchone()[0]
		print(f"group_id is {group_id}")
		logger.info("[SERVER] on get_group_messages: passed id decryption")
		cursor.execute("SELECT sender, content, timestamp FROM messages WHERE chat_type = 'group' AND chat_id = ?", (group_id,))
		messages = cursor.fetchall()
		response = {"status": "success", "messages": messages}
		return response

	def get_personal_messages(self, cursor, conn, request_data):
		logger.info(f"[SERVER] getting personal messages of {request_data['user1']} and {request_data['user2']}")
		cursor.execute("SELECT sender, content, timestamp FROM messages WHERE sender = ? AND receiver = ?", (request_data["user1"], request_data["user2"]))
		sent = cursor.fetchall()
		cursor.execute("SELECT sender, content, timestamp FROM messages WHERE sender = ? AND receiver = ?", (request_data["user2"], request_data["user1"]))
		received = cursor.fetchall()
		logger.info(f"[SERVER] received are {received}\nand sent are {sent}")
		response = {"status": "success", "received": received, "sent": sent, "messages": sorted(received + sent, key=lambda element: element[2])}
		return response

	def get_users(self, cursor, conn, request_data):
		# logger.log("[SERVER] started gathering users")
		cursor.execute("SELECT username FROM users")
		# logger.log(f"[SERVER] users are {users}")
		users = cursor.fetchall()
		users = np.array(users).flatten().tolist() # flattened the list
		# logger.log(f"[SERVER] flatted users to {users}")
		response = {"status": "sucess", "users": users}
		return response

	def register_user(self, cursor, conn, request_data):
		username = request_data.get("username")
		password = request_data.get("password")
		languages = request_data.get("languages", [])
		if not username:
			return {"status": "error", "message": "Username cannot be empty."}
		if not languages:
			return {"status": "error", "message": "You must select at least one language."}
		try:
			salt = str(random.randint(1, 1e9))
			# print(f"password is {password}")
			hashed_password = pyscrypt.hash(password=password.encode('utf-8'), salt=salt.encode('utf-8'), N=1024, r=1, p=1, dkLen=32)
			cursor.execute("INSERT INTO users (username, hashed_password, salt) VALUES (?, ?, ?)", (username, hashed_password, salt))
			logger.info(f"[SERVER] on register languages are {languages}")
			user_id = cursor.lastrowid
			cursor.executemany(
				"INSERT INTO user_languages (user_id, language_id) VALUES (?, ?)",
				[(user_id, cursor.execute("SELECT id FROM languages WHERE name = ?", (lang,)).fetchone()[0]) for lang in languages]
			)
			conn.commit()
			return {"status": "success", "message": "Registration successful"}
		except sqlite3.IntegrityError:
			return {"status": "error", "message": "Username already exists."}

	def login_user(self, cursor, request_data):
		username = request_data.get("username")
		cursor.execute("SELECT id, hashed_password, salt FROM users WHERE username = ?", (username,))
		user_data = cursor.fetchone()
		print(f"user data is {user_data}")
		ID, hashed_password, salt = user_data
		if not user_data:
			return {"status": "error", "message": "Invalid username"}

		if not pyscrypt.hash(password=request_data["password"].encode('utf-8'), salt=salt.encode('utf-8'), N=1024, r=1, p=1, dkLen=32) == hashed_password:
			return {"status": "error", "message": "Wrong password"}			
		
		return {"status": "success", "message": "Login successful"}

	def send_group_message(self, cursor, conn, request_data):
		group_name = request_data.get("group_name")
		sender = request_data.get("sender")
		content = request_data.get("content")
		cursor.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
		group_id = cursor.fetchone()
		if group_id:
			cursor.execute("""
				SELECT id FROM messages
				""")
			ID = len(cursor.fetchall())
			cursor.execute("""
				INSERT INTO messages (chat_type, chat_id, sender, content)
				VALUES ('group', ?, ?, ?)
			""", (group_id[0], sender, content))
			conn.commit()
			mistakes = self.analyze_message(content)
			logger.info(f"[SERVER] on send_group_message: mistakes are {mistakes}")
			cursor.executemany("""
				INSERT INTO typos (user_id, language_id, message_id, word_number, corrected_word) VALUES (?, ?, ?, ?, ?)
				""", [(self.get_user_id(conn, cursor, request_data["sender"]), 1, ID, mistake["word_number"], mistake["corrected_word"]) for mistake in mistakes])
			return {"status": "success", "message": "Message sent"}
		return {"status": "error", "message": "Group does not exist."}

	def send_personal_message(self, cursor, conn, request_data):
		sender = request_data.get("sender")
		content = request_data.get("content")
		receiver = request_data.get("receiver")
		cursor.execute("INSERT INTO messages (chat_type, sender, receiver, content) VALUES ('personal', ?, ?, ?)", (sender, receiver, content))
		mistakes = self.analyze_message(content)
		print("type of mistakes", type(mistakes))
		cursor.executemany("""
			INSERT INTO typos (user_id, language_id, message_id, word_number, corrected_word) VALUES (?, ?, ?, ?, ?)
			""", [(self.get_user_id(conn, cursor, request_data["sender"]), 1, ID, mistake["word_number"], mistake["corrected_word"]) for mistake in mistakes])
		return {"status": "success", "message": "Message sent"}

	def analyze_message(self, message):
		return Message(message).analyze(self.my_spellchecker)

	def start_server(self):
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.bind((self.host, self.port))
		server.listen(5)
		print(f"Server is listening on port {self.port}...")

		while True:
			client_socket, addr = server.accept()
			print(f"Connection established with {addr}")
			logger.info(f"[SERVER] Connection established with {addr}")
			client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
			client_handler.start()

if __name__ == "__main__":
	server = ChatServer()
	server.start_server()
