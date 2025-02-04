import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
from protocol import *
import logging
import random


class ChatAppLogic:
	SERVER_ADDRESS = ("127.0.0.1", 12345)  # Adjust as needed

	def __init__(self):
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

	def populate_language_list(self, lang_list):
		for language in languages:
			lang_list.insert(tk.END, language)

	def send_request(self, action, data={}):
		try:
			# self.client_socket.connect(self.SERVER_ADDRESS)
			request = {"action": action, **data}
			message = encrypt_message(json.dumps(request), self.public_key)
			custom_log(f"[CLIENT] encrypted_message type is {type(message)}")
			self.client_socket.send(message)
			logger.info(f"[CLIENT] sent request: action is {action} data is {data}")
			encrypted_message = self.client_socket.recv(basic_buffer_size)
			logger.info(f"[CLIENT] on send_request: encrypted_message length is {len(encrypted_message)}")
			response = json.loads(decrypt_message(encrypted_message, self.private_key))
			logger.info(f"[CLIENT] got response: {response}\n")
			return response
		except Exception as e:
			messagebox.showerror("Connection Error", f"An error occurred: {e}")
			return {"status": "error", "message": str(e)}

	def load_messages(self, chat_name, last_id_usage=False):
		logger.info(f"[CLIENT] on_load_messages: from chat {chat_name}")
		action = "get_group_messages" if self.chat_mode == "group" else "get_personal_messages"
		data = {
			"group_name" if self.chat_mode == "group" else "user2": chat_name,
			"user1": self.current_user,
			"last_id": self.last_id if last_id_usage else 1e9
		}
		
		response = self.send_request(action, data)
		self.last_id = response["last_id"]
		logger.info(f"[CLIENT] on_load_messages: last_id is {self.last_id}")
		if response["status"] == "success":
			return response["messages"]
		else:
			messagebox.showerror("Error", response.get("message", "Unknown error."))
			return None
		# logger.info(f"[CLIENT] loading messages from chat {chat_name} returned {response}")
