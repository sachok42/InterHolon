import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import random
import os
import json
import datetime

logger = logging.getLogger(__name__)
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
logger = logging.getLogger('chatting_log')
error_logger = logging.getLogger('error_log')

languages = ["English", "German", "Spanish", "Russian", "Hebrew", "Ukranian"]
basic_buffer_size = 1024
# Function to validate language structure (optional utility)
def validate_language_tree(language_tree):
	"""
	Validates the structure of the LANGUAGE_TREE.
	Ensures every branch is a dictionary and leaves are lists.
	"""
	if not isinstance(language_tree, dict):
		raise TypeError("LANGUAGE_TREE must be a dictionary at the root level.")
	for family, subfamilies in language_tree.items():
		if not isinstance(subfamilies, dict):
			raise TypeError(f"Subfamilies under '{family}' must be dictionaries.")
		for subfamily, languages in subfamilies.items():
			if not isinstance(languages, list):
				raise TypeError(f"Languages under '{subfamily}' in '{family}' must be lists.")

# Base group categories for organizing languages
base_groups = ["Collective", "Indo-European", "Semitic", "Uralic"] # Placeholder for broader linguistic categories or roles

# Language families and subfamilies with examples
LANGUAGE_TREE = {
	"Indo-European": {
		"Germanic": ["English", "German", "Dutch"],
		"Romance": ["Spanish", "French", "Italian"],
		"Slavic": ["Russian", "Polish", "Czech"]
	},
	"Semitic": {
		"Arabic": [],  # Future extensions can populate dialects or variations
		"Hebrew": []
	},
	"Uralic": {
		"Finnic": ["Finnish", "Estonian"],
		"Ugric": ["Hungarian"]
	}
}

def custom_log(text, usedloger=logger):
	message = f"{text} {datetime.datetime.now()}"
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

POS_painting = {
	"CC": "#7f7f7f",
	"CD": "#d62738",
	"DT": "#9467bd",
	"EX": "#ff9896",
	"FW": "#555555",
	"IN": "#17becf",
	"JJ": "#ff7f0e",
	"JJR": "#ffbb78",
	"JJS": "#d62728",
	"LS": "#17becf",
	"MD": "#1f77b4",
	"NN": "#1f77b4",
	"NNS": "#aec7e8",
	"NNP": "#2ca02c",
	"NNPS": "#98df8a",
	"PDT": "#c5b0d5",
	"POS": "#e7ba52",
	"PRP": "#e377c2",
	"PRP$": "#f7b6d2",
	"RB": "#ffbb78",
	"RBR": "#ffcc00",
	"RBS": "#ffeb3b",
	"RP": "#8c564b",
	"SYM": "#000000",
	"TO": "#bcbd22",
	"UH": "#c49c94",
	"VB": "#2ca02c",
	"VBD": "#98df8a",
	"VBG": "#d62728",
	"VBN": "#ff9896",
	"VBP": "#9467bd",
	"VBZ": "#c5b0d5",
	"WDT": "#8c564b",
	"WP": "#8c564b",
	"WP$": "#c49c94",
	"WRB": "#8c564b",
	"PNC": "black"
}

def encrypt_message(message, public_key):
	# logger.info(f"[PROTOCOL] started encrypting message")
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
	# logger.info(f"[PROTOCOL] finished encrypting message")
	return res.encode()


def decrypt_message(data, private_key):
	# logger.info(f"[PROTOCOL] started decrypting message")
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
	# logger.info(f"[PROTOCOL] finished decrypting message")
	return decrypted_message.decode()

# Run validation on script load (optional)
# validate_language_tree(LANGUAGE_TREE)

def send_message_by_parts(used_socket, encoded_message, private_key):
	logger.info(f"[PROTOCOL] started sending message, size of the message is {len(encoded_message)}")
	index = 0
	while index + basic_buffer_size - 8 < len(encoded_message):
		data = b"0" + encoded_message[index: index + basic_buffer_size - 8]
		logger.info(f"[PROTOCOL] on send_message_by_parts: sent chunk starting {data[0]}")
		used_socket.send(data)
		index += basic_buffer_size - 8
		logger.info(f"[PROTOCOL] on send_message_by_parts: sent chunk number {index / (basic_buffer_size - 8)}")
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