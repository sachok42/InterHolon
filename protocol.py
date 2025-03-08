import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import random
import os
import json
import datetime
from language_protocol import *

# logger = logging.getLogger(__name__)
logging.basicConfig(filename='chatting_log.log', encoding='utf-8', level=logging.DEBUG)
logging.basicConfig(filename='error_log.log', encoding='utf-8', level=logging.DEBUG)

standard_font = ("Arial", 14)

def setup_logger(logger_name, log_file, level=logging.DEBUG):
	l = logging.getLogger(logger_name)
	formatter = logging.Formatter('%(asctime)s : %(message)s')
	fileHandler = logging.FileHandler(log_file, mode='w')
	fileHandler.setFormatter(formatter)
	streamHandler = logging.StreamHandler()
	streamHandler.setFormatter(formatter)

	l.setLevel(level)
	l.addHandler(fileHandler)
	# l.addHandler(streamHandler)    

# setup_logger('chatting_log', 'chatting_log.log')
# setup_logger('error_log', 'error_log.log')
logger = logging.getLogger('chatting_log.log')
error_logger = logging.getLogger('error_log.log')
formatter = logging.Formatter('%(asctime)s : %(message)s')
fileHandler = logging.FileHandler('chatting_log.log', mode='w')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
basic_buffer_size = 1024

def custom_log(text, used_logger=None):
	if used_logger is None:
		used_logger = logger
	message = f"{datetime.datetime.now()} {text}"
	logger.info(message)
	print(message)

standard_key_size = 2048
def generate_key():
	private_key = rsa.generate_private_key(
		public_exponent=65537,
		key_size=standard_key_size
		)
	public_key = private_key.public_key()
	return private_key, public_key

def encrypt_message(message, public_key):
	logger.info(f"[PROTOCOL] started encrypting message")
	aes_key = os.urandom(32)
	iv = os.urandom(12)

	aes_cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
	encryptor = aes_cipher.encryptor()
	ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
	encrypted_key = public_key.encrypt(
		aes_key,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA256()),
			algorithm=hashes.SHA256(),
			label=None
		)
	)
	res = json.dumps({
		"aes_key": encrypted_key.hex(),
		"iv": iv.hex(),
		"ciphertext": ciphertext.hex(),
		"tag": encryptor.tag.hex()
		})
	logger.info(f"[PROTOCOL] finished encrypting message")
	return res.encode()


def decrypt_message(data, private_key):
	logger.info(f"[PROTOCOL] started decrypting message")
	data = json.loads(data)
	encrypted_aes_key = bytes.fromhex(data["aes_key"])
	iv = bytes.fromhex(data["iv"])
	ciphertext = bytes.fromhex(data["ciphertext"])
	tag = bytes.fromhex(data["tag"])

	aes_key = private_key.decrypt(
		encrypted_aes_key,
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA256()),
			algorithm=hashes.SHA256(),
			label=None
		)
	)
	aes_cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag))
	decryptor = aes_cipher.decryptor()
	decrypted_message = decryptor.update(ciphertext) + decryptor.finalize()
	logger.info(f"[PROTOCOL] finished decrypting message")
	return decrypted_message.decode()

# Run validation on script load (optional)
# validate_language_tree(LANGUAGE_TREE)

def send_message_by_parts(used_socket, encoded_message, private_key):
	logger.info(f"[PROTOCOL] started sending message, size of the message is {len(encoded_message)}")
	index = 0
	while index + basic_buffer_size - 1 < len(encoded_message):
		data = b"0" + encoded_message[index: index + basic_buffer_size - 1]
		logger.info(f"[PROTOCOL] on send_message_by_parts: sent chunk starting {data[0]}")
		used_socket.send(data)
		index += basic_buffer_size - 1
		logger.info(f"[PROTOCOL] on send_message_by_parts: sent chunk number {index // (basic_buffer_size - 1)}")
	data = b"1" + encoded_message[index:]
	logger.info(f"[PROTOCOL] on send_message_by_parts: final chunk starting {data[0]}")
	used_socket.send(data)

def get_message_by_parts(used_socket, public_key):
	logger.info(f"[PROTOCOL] started receiving message")
	result = b""

	while True:
		data = used_socket.recv(basic_buffer_size)
		logger.info(f"[PROTOCOL] on get_message_by_parts got a chunk, first char is {data[0]}")
		result = result + data[1:]
		if data[0] == 49:
			break

	logger.info(f"[PROTOCOL] on get_message_by_parts: final size of the message is {len(result)}")
	return result

def get_message(used_socket, public_key):
	pass