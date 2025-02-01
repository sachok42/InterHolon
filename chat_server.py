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
from ChatServerUtilities import *


class ChatServer(ChatServerUtilities):
	def __init__(self, host="0.0.0.0", port=12345):
		self.host = host
		self.port = port

		self.conn = sqlite3.connect("chat_server.db")
		self.my_spellchecker = spellchecker.SpellChecker()
		logger.info("\n\nServer on")
		self.messages_num = 0
		self.users_num = 0
		self.chats_num = 0

		self.initialize_db()

	def initialize_db(self):
		with sqlite3.connect("chat_server.db") as conn:
			cursor = conn.cursor()
			sql_db_init(cursor)

			self.users_num = cursor.execute("""
				SELECT COUNT(*) FROM users
				""").fetchone()[0]
			self.messages_num = cursor.execute("""
				SELECT COUNT(*) FROM messages
				""").fetchone()[0]
			self.chat_num = cursor.execute("""
				SELECT COUNT(*) FROM chats
				""").fetchone()[0]

			self.register_user(cursor, conn, {"password": "admin", "username": "admin", "languages": ["English"]})
			conn.commit()

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
		elif action == "load_typo_message":
			response = self.load_typo_message(cursor, conn, request_data)
		# Add more actions as needed...
		logger.info(f"[SERVER] sent response: response is {response}")
		return response

	def add_chat(self, conn, chat_name, chat_type='group'):
		cursor = conn.cursor()
		cursor.execute("""
			INSERT INTO chats (name, type) VALUES (?, ?)
			""", (chat_name, chat_type))
		self.chat_num += 1
		logger.info(f"[SERVER] on add_chat: chat {chat_name} type {chat_type} added")

	def add_contact_by_id(self, conn, id1, id2):
		logger.info(f"[SERVER] on add_contact_by_id: id1 is {id1} and id2 is {id2}")
		cursor = conn.cursor()
		self.add_chat(conn, f"{id1}-{id2}", 'personal')
		cursor.execute("""
			INSERT INTO contacts (id1, id2, chat_id) VALUES (?, ?, ?)
			""", (id1, id2, self.chat_num))

	def load_typo_message(self, cursor, conn, request_data):
		cursor.execute("""
			SELECT word_number, corrected_word, message_id FROM typos WHERE id = ?
			""", (request_data["id"],))
		mistake = cursor.fetchone()
		logger.info(f"[SERVER] on load_typo_message mistake is {mistake}")
		word_number = mistake[0]
		message_id = mistake[2]
		cursor.execute("""
			SELECT content, chat_type, chat_id, timestamp, sender_id FROM messages WHERE id = ?
			""", (message_id,))
		message = cursor.fetchone()
		logger.info(f"[SERVER] on load_typo_message message is {message}")
		words = message[0].split()
		pre_mistake = " ".join(words[:word_number])
		wrong_word = words[word_number]
		post_mistake = " ".join(words[word_number + 1:])
		print("Before the func")
		receiver = self.get_chat_name(conn, message[2])
		timestamp = message[3]

		response = {"receiver": receiver, "content_start": pre_mistake, "content_mistake": wrong_word, "content_end": post_mistake, "timestamp": timestamp, "corrected_word": mistake[1]}

		return response

	def get_mistakes(self, cursor, conn, request_data):
		# cursor = conn.cursor()
		logger.info(f"[SERVER] on get_mistakes started the function")
		cursor.execute("""
			SELECT id, message_id, word_number, corrected_word FROM typos WHERE user_id = ?
			""", (self.get_user_id(conn, request_data['sender']),))
		logger.info(f"[SERVER] on get_mistakes started fetching")
		typos = cursor.fetchall()
		logger.info(f"[SERVER] on get_mistakes: sender is {request_data['sender']} found mistakes are {typos}")
		response = {"status": "success", "typos": typos}
		return response

	def get_group_messages(self, cursor, conn, request_data):
		logger.info(f"[SERVER] on get_group_messages: request_data is {request_data}")
		cursor = conn.cursor()	
		cursor.execute("SELECT id FROM chats WHERE name = ?", (request_data["group_name"],))
		group_id = cursor.fetchone()[0]

		messages, last_id = self.get_messages(conn, group_id)
		response = {"status": "success", "messages": messages, "last_id": last_id}
		return response

	def get_personal_messages(self, cursor, conn, request_data):
		logger.info(f"[SERVER] getting personal messages of {request_data['user1']} and {request_data['user2']}")
		id1 = self.get_user_id(conn, request_data['user1'])
		id2 = self.get_user_id(conn, request_data['user2'])
		cursor.execute("""
			SELECT chat_id FROM contacts WHERE id1 = ? AND id2 = ? OR id1 = ? AND id2 = ? 
			""", (id1, id2, id2, id1))
		chat_id = cursor.fetchone()[0]
		
		messages, last_id = self.get_messages(conn, chat_id)
		response = {"status": "success", "messages": messages, "last_id": last_id}
		return response

	def get_users(self, cursor, conn, request_data):
		logger.info("[SERVER] started gathering users")
		ID = self.get_user_id(conn, request_data["user1"])
		cursor.execute("""
			SELECT id1, id2 FROM contacts WHERE id1 = ? OR id2 = ?
			""", (ID, ID))
		# logger.info(f"[SERVER] users are {users}")
		users = cursor.fetchall()
		logger.info(f"[SERVER] on get_users: users are {users}")
		users = self.flatten_array(users) # flattened the list
		logger.info(f"[SERVER] on get_users: users are {users}")
		users = self.replenish_ids_with_usernames_flat(conn, users)
		logger.info(f"[SERVER] on get_users: users are {users}")
		# logger.info(f"[SERVER] flatted users to {users}")
		response = {"status": "sucess", "users": users}
		return response

	def register_user(self, cursor, conn, request_data):
		logger.info(f"[SERVER] on register_user: user is {request_data['username']}")
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
			self.users_num += 1
			self.add_contact_by_id(conn, self.users_num, 1)
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

	def send_message(self, conn, request_data):
		logger.info(f"[SERVER] on send_personal_message message if {request_data}")
		content = request_data.get("content")
		sender_id = self.get_user_id(conn, request_data.get("sender"))
		receiver_id = self.get_user_id(conn, request_data.get("receiver"))
		cursor = conn.cursor()
		cursor.execute("""
			SELECT chat_id FROM contacts WHERE id1 = ? AND id2 = ? OR id1 = ? AND id2 = ?
			""", (sender_id, receiver_id, receiver_id, sender_id))
		chat_id = cursor.fetchone()[0]

		cursor.execute("INSERT INTO messages (chat_type, sender_id, receiver_id, content, chat_id) VALUES ('personal', ?, ?, ?, ?)", (sender_id, receiver_id, content, chat_id))
		self.messages_num += 1
		ID = self.messages_num
		logger.info(f"ID is {ID}")
		message = Message(content, request_data["sender"], None, None, request_data["receiver"])
		# mistakes = self.analyze_message(content)
		mistakes_handler = threading.Thread(target=self.analyze_message_autonomous, args=(message, ID))
		mistakes_handler.start()
		return {"status": "success", "message": "Message sent"}


	def send_group_message(self, cursor, conn, request_data):
		group_name = request_data.get("group_name")
		sender = request_data.get("sender")
		content = request_data.get("content")
		sender_id = self.get_user_id(conn, sender)
		cursor.execute("SELECT id FROM chats WHERE name = ?", (group_name,))
		group_id = cursor.fetchone()[0]
		logger.info(f"[SERVER] on send_group_message: sending a message to group id {group_id}")
		if group_id:
			cursor.execute("""
				INSERT INTO messages (chat_type, chat_id, sender_id, content)
				VALUES ('group', ?, ?, ?)
			""", (group_id, sender_id, content))
			conn.commit()
			cursor.execute("SELECT COUNT(*) FROM messages")
			ID = cursor.fetchone()[0]
			# mistakes = self.analyze_message(content)

			message = Message(content, sender, None, group_id, None)
			mistakes_handler = threading.Thread(target=self.analyze_message_autonomous, args=(message, ID))
			mistakes_handler.start()

			return {"status": "success", "message": "message sent"}

		return {"status": "error", "message": "Group does not exist."}

	def send_personal_message(self, cursor, conn, request_data):
		logger.info(f"[SERVER] on send_personal_message message if {request_data}")
		content = request_data.get("content")
		sender_id = self.get_user_id(conn, request_data.get("sender"))
		receiver_id = self.get_user_id(conn, request_data.get("receiver"))
		cursor.execute("""
			SELECT chat_id FROM contacts WHERE id1 = ? AND id2 = ? OR id1 = ? AND id2 = ?
			""", (sender_id, receiver_id, receiver_id, sender_id))
		chat_id = cursor.fetchone()[0]
		request_data["chat_id"] = chat_id
		return self.send_message(conn, request_data)

	def analyze_message(self, message):
		message = Message(message)
		return message.analyze(self.my_spellchecker)

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
