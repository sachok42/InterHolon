import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
from protocol import *
import logging


class ChatAppLogic:
	SERVER_ADDRESS = ("127.0.0.1", 12345)  # Adjust as needed

	def __init__(self):
		self.last_id = 1e9

	def populate_language_list(self, lang_list):
		for language in languages:
			lang_list.insert(tk.END, language)

	def send_request(self, action, data={}):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
				logger.info(f"[USER] sent request: action is {action} data is {data}")
				client_socket.connect(self.SERVER_ADDRESS)
				request = {"action": action, **data}
				client_socket.send(json.dumps(request).encode())
				response = json.loads(client_socket.recv(1024).decode())
				logger.info(f"[USER] got response: {response}\n")
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
