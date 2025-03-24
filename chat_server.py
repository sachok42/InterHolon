import socket
import threading
import sqlite3
import json
import numpy as np
from protocol import *
import pyscrypt
import random
from Message import Message
from sql_db_init import sql_db_init
from ChatServerUtilities import *


class ChatServer(ChatServerUtilities):
	def __init__(self, host="0.0.0.0", port=12345):
		logger.info("\n\nServer on")
		super(ChatServer, self).__init__()
		self.host = host
		self.port = port

		self.conn = sqlite3.connect("chat_server.db")
		self.messages_num = 0
		self.users_num = 0
		self.chats_num = 0

		self.initialize_db()

	def initialize_db(self):
		with sqlite3.connect("chat_server.db") as conn:
			cursor = conn.cursor()
			sql_db_init(cursor)

			for group_name in base_groups:
				cursor.execute("INSERT OR IGNORE INTO chats (name) VALUES (?)", (group_name,))

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

	def process_request(self, cursor, conn, action, request_data):
		logger.info(f"[SERVER] received request: action {action}, data {request_data}")
		try:
			response = {"status": "error", "message": "Invalid action"}
			match action:
				case "register":
					response = self.register_user(cursor, conn, request_data)
				case "login":
					response = self.login_user(cursor, request_data)
				case "send_group_message":
					response = self.send_group_message(cursor, conn, request_data)
				case "send_personal_message":
					response = self.send_personal_message(cursor, conn, request_data)
				case "get_group_messages":
					response = self.get_group_messages(cursor, conn, request_data)
				case "get_personal_messages":
					response = self.get_personal_messages(cursor, conn, request_data)
				case "get_users":
					response = self.get_users(cursor, conn, request_data)
				case "get_mistakes":
					response = self.get_mistakes(cursor, conn, request_data)
				case "load_typo_message":
					response = self.load_typo_message(cursor, conn, request_data)
				case "get_languages":
					response = self.get_user_languages(conn, request_data)
				case "get_requests":
					response = self.get_requests(conn, request_data)
				case "make_request":
					response = self.make_request(conn, request_data)
				case "accept_request":
					response = self.accept_request(conn, request_data)
				case "get_groups":
					response = self.get_groups(conn, request_data)
				case "create_group":
					response = self.create_group(conn, request_data)
		except Exception as e:
			response = {"status": "error", "message": "unknown error"}
			logger.error(f"[SERVER] error: {e}")

		# Add more actions as needed...
		logger.info(f"[SERVER] sent response: response is {response}")
		return response


	def get_groups(self, conn, request_data):
		user_id = self.get_user_id(conn, request_data["user"])
		cursor = conn.cursor()
		cursor.execute("""
			SELECT group_id FROM group_participants WHERE user_id = ?
			""", (user_id,))
		groups_ids = self.flatten_array(cursor.fetchall())
		logger.info(f"[SERVER] on get_groups: group_ids are {groups_ids}")
		groups = self.replenish_ids_with_chats_flat(conn, groups_ids)
		response = {"status": "success", "groups": groups}
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
		conn.commit()

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

		response = {
		"receiver": receiver,
		"content_start": pre_mistake,
		"content_mistake": wrong_word,
		"content_end": post_mistake,
		"timestamp": timestamp,
		"corrected_word": mistake[1]
		}

		return response

	def get_user_languages(self, conn, request_data):
		logger.info(f"[SERVER] on get_languages: request_data is {request_data}")
		cursor = conn.cursor()
		cursor.execute("""
			SELECT language_id FROM user_languages WHERE user_id = ?
			""", (self.get_user_id(conn, request_data["user"]),))
		ids = self.flatten_array(cursor.fetchall())
		languages = self.replenish_ids_with_languages_flat(conn, ids)
		response = {"status": "success", "languages": languages}
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

		messages, last_id = self.get_messages(conn, group_id, request_data["last_id"])
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
		
		messages, last_id = self.get_messages(conn, chat_id, request_data["last_id"])
		response = {"status": "success", "messages": messages, "last_id": last_id}
		return response

	def get_users(self, cursor, conn, request_data):
		logger.info("[SERVER] started gathering users")
		ID = self.get_user_id(conn, request_data["user"])
		cursor.execute("""
			SELECT id1, id2 FROM contacts WHERE id1 = ? OR id2 = ?
			""", (ID, ID))
		# logger.info(f"[SERVER] users are {users}")
		users = cursor.fetchall()
		logger.info(f"[SERVER] on get_users: users are {users}")
		users = list(set(self.flatten_array(users))) # flattened the list
		logger.info(f"[SERVER] on get_users: users are {users}")
		users = self.replenish_ids_with_usernames_flat(conn, users)
		logger.info(f"[SERVER] on get_users: users are {users}")
		# logger.info(f"[SERVER] flatted users to {users}")
		response = {"status": "sucess", "users": users}
		return response

	def add_group_member_ids(self, conn, group_id, user_id):
		cursor = conn.cursor()
		cursor.execute("""
			INSERT INTO group_participants (group_id, user_id) VALUES (?, ?)
			""", (group_id, user_id))
		return {"status": "success", "message": f"user id {user_id} added to group {group_id}"}

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
			salt = str(random.randint(1, 1000000000))
			# print(f"password is {password}")
			hashed_password = pyscrypt.hash(password=password.encode('utf-8'),\
			 salt=salt.encode('utf-8'), N=1024, r=1, p=1, dkLen=32)
			cursor.execute("""
				INSERT INTO users (username, hashed_password, salt) VALUES (?, ?, ?)
				""", (username, hashed_password, salt))
			logger.info(f"[SERVER] on register languages are {languages}")
			user_id = cursor.lastrowid
			cursor.executemany(
				"INSERT INTO user_languages (user_id, language_id) VALUES (?, ?)",
				[(user_id, cursor.execute("""
					SELECT id FROM languages WHERE name = ?
					""", (lang,)).fetchone()[0]) for lang in languages]
			)
			self.users_num += 1
			self.add_contact_by_id(conn, self.users_num, 1)
			for group in base_groups:
				logger.info(f"[SERVER] on register_user: added the user to the basic group {group}")
				self.add_group_member_ids(conn, self.get_chat_id(conn, group), self.users_num)
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

		if not pyscrypt.hash(password=request_data["password"].encode('utf-8'), \
		salt=salt.encode('utf-8'), N=1024, r=1, p=1, dkLen=32) == hashed_password:
			return {"status": "error", "message": "Wrong password"}         
		
		return {"status": "success", "message": "Login successful"}

	def send_message(self, conn, request_data, mode):
		logger.info(f"[SERVER] on send_message message is {request_data}")
		content = request_data.get("content")
		sender_id = self.get_user_id(conn, request_data.get("sender"))
		chat_id = request_data["chat_id"]
		language_id = self.get_language_id(conn, request_data["language"])

		cursor = conn.cursor()
		cursor.execute("""
			INSERT INTO messages (chat_type, sender_id, content, chat_id, language_id) VALUES (?, ?, ?, ?, ?)
			""", (mode, sender_id, content, chat_id, language_id))
		conn.commit()
		self.messages_num += 1
		ID = self.messages_num
		logger.info(f"ID is {ID}")
		message = Message(content, request_data["sender"], request_data.get("chat_id"), request_data["language"])
		# mistakes = self.analyze_message(content)
		mistakes_handler = threading.Thread(target=self.analyze_message_autonomous, args=(message, ID))
		mistakes_handler.start()
		return {"status": "success", "message": "Message sent"}

	def send_group_message(self, cursor, conn, request_data):
		group_name = request_data.get("group_name")
		sender = request_data.get("user")
		content = request_data.get("content")
		sender_id = self.get_user_id(conn, sender)
		cursor.execute("SELECT id FROM chats WHERE name = ?", (group_name,))
		group_id = cursor.fetchone()[0]
		request_data["chat_id"] = group_id
		logger.info(f"[SERVER] on send_group_message: sending a message to group id {group_id}")
		if group_id:
			return self.send_message(conn, request_data, "group")
			return {"status": "success", "message": "message sent"}

		return {"status": "error", "message": "Group does not exist."}

	def send_personal_message(self, cursor, conn, request_data):
		logger.info(f"[SERVER] on send_personal_message message is {request_data}")
		content = request_data.get("content")
		sender_id = self.get_user_id(conn, request_data.get("user"))
		receiver_id = self.get_user_id(conn, request_data.get("receiver"))
		cursor.execute("""
			SELECT chat_id FROM contacts WHERE id1 = ? AND id2 = ? OR id1 = ? AND id2 = ?
			""", (sender_id, receiver_id, receiver_id, sender_id))
		chat_id = cursor.fetchone()[0]
		request_data["chat_id"] = chat_id
		return self.send_message(conn, request_data, "personal")

	def make_request(self, conn, request_data):
		logger.info(f"[SERVER] on make_request")
		cursor = conn.cursor()
		sender_id = self.get_user_id(conn, request_data["user"])
		receiver_id = self.get_user_id(conn, request_data["receiver"])
		cursor.execute("""
			INSERT INTO requests (sender_id, receiver_id) VALUES (?, ?)
			""", (sender_id, receiver_id))
		conn.commit()
		return {"status": "success"}

	def get_requests(self, conn, request_data):
		cursor = conn.cursor()
		user_id = self.get_user_id(conn, request_data["user"])
		logger.info(f"[SERVER] on get_requests: user_id is {user_id}")
		if request_data["mode"] == "incoming":
			cursor.execute("""
				SELECT sender_id FROM requests WHERE receiver_id = ?
				""", (user_id,))
		else:
			cursor.execute("""
				SELECT receiver_id FROM requests WHERE sender_id = ?
				""", (user_id,))
		requests = cursor.fetchall()
		logger.info(f"[SERVER] on get_requests: ids are {requests}")
		requests = self.replenish_ids_with_usernames(conn, requests)
		return {"status": "success", "requesters": requests}

	def accept_request(self, conn, request_data):
		sender_id = self.get_user_id(conn, request_data["sender"])
		receiver_id = self.get_user_id(conn, request_data["user"])
		logger.info(f"[SERVER] on accept_request: sender id is {sender_id} and receiver id is {receiver_id}")
		self.add_contact_by_id(conn, sender_id, receiver_id)
		cursor = conn.cursor()
		cursor.execute("""
			DELETE FROM requests WHERE receiver_id = ? AND sender_id = ?
			""", (receiver_id, sender_id))
		conn.commit()
		return {"status": "success"}

	def get_request_data(self, conn, request_data):
		sender_id = self.get_user_id(conn, request_data["sender"])
		receiver_id = self.get_user_id(conn, request_data["receiver"])
		cursor = conn.cursor()
		cursor.execute("""
			SELECT id, sender_id, receiver_id FROM requests WHERE sender_id = ? AND receiver_id = ?
			""", (sender_id, receiver_id))
		request = cursor.fetchone()
		return {"status": "success", "username": self.get_user_id(conn, request[1])}

	def create_group_collective(self, conn, group_id):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT id FROM users
			""")
		ids = self.flatten_array(cursor.fetchall())
		self.create_group_by_ids(conn, group_name, ids)

	def create_group(self, conn, request_data):
		user_ids = self.replenish_usernames_with_ids_flat(conn, request_data["users"])
		group_name = request_data["name"]
		return self.create_group_by_ids(conn, group_name, user_ids)

	def create_group_by_ids(self, conn, group_name, participants_ids):
		self.add_chat(conn, group_name)
		group_id = self.get_chat_id(conn, group_name)
		cursor = conn.cursor()
		cursor.executemany("""
			INSERT INTO group_participants (group_id, user_id) VALUES (?, ?)
			""", [(group_id, user_id) for user_id in participants_ids])
		conn.commit()
		return {"status": "success", "message": f"group {group_name} created"}

	def handle_client(self, client_socket):
		private_key, public_key = generate_key()
		public_pem = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo
		)
		client_socket.send(public_pem)
		logger.info(f"[SERVER] sent pem starting {public_pem.hex()[:10]}")
		received_data = client_socket.recv(basic_buffer_size)
		logger.info(f"[SERVER] got pem starting {received_data.hex()[:10]}")
		public_key = serialization.load_pem_public_key(received_data)
		current_user = None
		with sqlite3.connect("chat_server.db") as conn:
			cursor = conn.cursor()
			try:
				while True:
					request = get_message_by_parts(client_socket, public_key)
					request = decrypt_message(request, private_key)
					if not request:
						break
					try:
						request_data = json.loads(request)
					except json.JSONDecodeError:
						message = encrypt_message(json.dumps({"status": "error", "message": "Invalid JSON"}), public_key)
						send_message_by_parts(client_socket, message, private_key)
						continue
					action = request_data.get("action")
					if action == "login":
						response = self.process_request(cursor, conn, action, request_data)
						if response["status"] == "success":
							current_user = request_data["username"]
					elif action != "register" and request_data["user"] != current_user:
						response = {"status": "error", "problem": "unchecked user"}
					else:
						response = self.process_request(cursor, conn, action, request_data)
					message = encrypt_message(json.dumps(response), public_key)
					# logger.info(f"[SERVER] on handle_client: message length is {len(message)}")
					send_message_by_parts(client_socket, message, private_key)
			except Exception as e:
				print(f"Error: {e}")
			finally:
				client_socket.close()

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
