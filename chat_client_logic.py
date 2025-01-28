import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
from protocol import *
import logging


class ChatAppLogic:
	SERVER_ADDRESS = ("127.0.0.1", 12345)  # Adjust as needed

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
