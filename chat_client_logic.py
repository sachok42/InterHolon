import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
from protocol import *
import logging
import random
from POS_tagger import POS_tagger

class ChatAppLogic:

	def __init__(self):
		self.SERVER_ADDRESS = (input() or "127.0.0.1", 12345)  # Adjust as needed
		logger.info("\n\nClient on")
		self.last_id = 1e9
		self.private_key, self.public_key = generate_key()
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect(self.SERVER_ADDRESS)
		public_pem = self.public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
			)
		self.client_socket.send(public_pem)
		logger.info(f"[CLIENT] sent pem starting {public_pem.hex()[:10]}")
		received_data = self.client_socket.recv(basic_buffer_size)
		logger.info(f"[CLIENT] got pem starting {received_data.hex()[:10]}")
		self.public_key = serialization.load_pem_public_key(received_data)
		# logger.info(f"[CLIENT] my ")

		self.POS_taggers = {}

	def tag_text(self, language, text):
		if language not in self.POS_taggers:
			self.POS_taggers[language] = POS_tagger(language)
		return self.POS_taggers[language].tag_text(text)

	def get_languages(self):
		response = self.send_request("get_languages", {"user1": self.current_user})
		return response["languages"]

	def send_request(self, action, data={}):
		try:
			# self.client_socket.connect(self.SERVER_ADDRESS)
			data["user"] = self.current_user
			request = {"action": action, **data}
			message = encrypt_message(json.dumps(request), self.public_key)
			# custom_log(f"[CLIENT] encrypted_message type is {type(message)}")
			send_message_by_parts(self.client_socket, message, self.private_key)
			# self.client_socket.send(message)
			logger.info(f"[CLIENT] sent request: action is {action} data is {data}")
			encrypted_message = get_message_by_parts(self.client_socket, self.public_key)
			logger.info(f"[CLIENT] on send_request: encrypted_message length is {len(encrypted_message)}")
			response = json.loads(decrypt_message(encrypted_message, self.private_key))
			logger.info(f"[CLIENT] got response: {response}\n")
			return response
		except Exception as e:
			logger.error(f"[PROTOCOL] on send_request: an error occurred: {e}")
			return {"status": "error", "message": str(e)}

	def load_messages(self, chat_name, last_id_usage=False, update=False):
		logger.info(f"[CLIENT] on_load_messages: from chat {chat_name}")
		action = "get_group_messages" if self.chat_mode == "group" else "get_personal_messages"
		data = {
			"group_name" if self.chat_mode == "group" else "user2": chat_name,
			"user1": self.current_user,
			"last_id": self.last_id if last_id_usage else 1e9
		}
		
		response = self.send_request(action, data)
		if not update:
			self.last_id = response["last_id"]
		logger.info(f"[CLIENT] on_load_messages: last_id is {self.last_id}")
		if response["status"] == "success":
			return response["messages"]
		else:
			messagebox.showerror("Error", response.get("message", "Unknown error."))
			return None
		# logger.info(f"[CLIENT] loading messages from chat {chat_name} returned {response}")
