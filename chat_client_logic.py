import socket
import json
from protocol import *
import logging
import random

class ChatAppLogic:
	def __init__(self):
		self.SERVER_ADDRESS = (input() or "127.0.0.1", 12345)  # Adjust as needed
		custom_log("\n\nClient on")
		self.last_id = 1e9
		self.private_key, self.public_key = generate_key()
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect(self.SERVER_ADDRESS)
		# self.update_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# self.update_socket.connect(self.SERVER_ADDRESS)
		public_pem = self.public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
			)
		self.client_socket.send(public_pem)
		custom_log(f"[CLIENT] sent pem starting {public_pem.hex()[:10]}")
		received_data = self.client_socket.recv(basic_buffer_size)
		custom_log(f"[CLIENT] got pem starting {received_data.hex()[:10]}")
		self.public_key = serialization.load_pem_public_key(received_data)
		self.biggest_id = -1
		# custom_log(f"[CLIENT] my ")

	def get_languages(self):
		response = self.send_request("get_languages")
		return response["languages"]

	def choose_language(self, language):
		self.current_language = language

	def send_request(self, action, data={}):
		try:
			data["user"] = self.current_user
			request = {"action": action, **data}
			message = encrypt_message(json.dumps(request), self.public_key)
			send_message_by_parts(self.client_socket, message, self.private_key)
			custom_log(f"[CLIENT] sent request: action is {action} data is {data}")
			encrypted_message = get_message_by_parts(self.client_socket, self.public_key)
			custom_log(f"[CLIENT] on send_request: encrypted_message length is {len(encrypted_message)}")
			response = json.loads(decrypt_message(encrypted_message, self.private_key))
			custom_log(f"[CLIENT] got response: {response}\n")
			return response
		except Exception as e:
			logger.error(f"[PROTOCOL] on send_request: an error occurred: {e}")
			return {"status": "error", "message": str(e)}

	def wait_for_updates(self, update_socket):
		update = decrypt_message(get_message_by_parts(update_socket, self.private_key))
		self.process_update(json.loads(update))

	def process_update(self, update):
		action = update["action"]
		match action:
			case "new_message":
				pass

	def check_for_updates(self, chat_name, biggest_id_used=-1):
		action = "check_for_updates"
		data = {"chat_name": chat_name, "biggest_id": biggest_id_used}
		response = self.send_request(action, data)
		return response["messages"], response["biggest_id"]

	def load_messages(self, chat_name, last_id_usage=False, update=False):
		custom_log(f"[CLIENT] on_load_messages: from chat {chat_name}")
		action = "get_group_messages" if self.chat_mode == "group" else "get_personal_messages"
		data = {
			"group_name" if self.chat_mode == "group" else "user2": chat_name,
			"user1": self.current_user,
			"last_id": self.last_id if last_id_usage else 1e9,
			"first_load": False if last_id_usage else True
		}
		
		response = self.send_request(action, data)
		if not update:
			self.last_id = response["last_id"]
		if not last_id_usage:
			self.biggest_id = response["biggest_id"]
		custom_log(f"[CLIENT] on_load_messages: last_id is {self.last_id}")
		if response["status"] == "success":
			return response["messages"]
		else:
			# messagebox.showerror("Error", response.get("message", "Unknown error."))
			logger.error(f"[CLIENT] error on load_messages: error is {'unknown error'}")
			return None
		# custom_log(f"[CLIENT] loading messages from chat {chat_name} returned {response}")
