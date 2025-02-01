from protocol import *
import numpy as np
import sqlite3


class ChatServerUtilities:
	def get_user_id(self, conn, user):
		try:
			cursor = conn.cursor()
			logger.info(f"[SERVER] on get_user_id user {user}")
			cursor.execute("""
				SELECT id FROM users WHERE username = ?
				""", (user,))
			user_id = cursor.fetchone()[0]
			logger.info(f"[SERVER] user {user} id {user_id}")
			return user_id
		except Exception as e:
			logger.error(f"[SERVER] on get_user_id: user {user} not found")
			return None

	def get_username(self, cursor, ID):
		logger.info(f"[SERVER] find the name of user id {ID}")
		cursor.execute("SELECT username FROM users WHERE id = ?", (ID,))
		username = cursor.fetchone()[0]
		return username

	def replenish_ids_with_usernames(self, conn, elements):
		cursor = conn.cursor()
		result = [(self.get_username(cursor, element[0]), *element[1:]) for element in elements]
		return result

	def replenish_ids_with_usernames_flat(self, conn, elements):
		cursor = conn.cursor()
		result = [self.get_username(cursor, element) for element in elements]
		return result

	def get_chat_name(self, conn, ID):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT name FROM chats WHERE id = ?
			""", (ID,))
		return cursor.fetchone()[0]
		
	def get_messages(self, conn, group_id, last_id=1e6):
		cursor = conn.cursor()
		cursor.execute("SELECT sender_id, content, timestamp FROM messages WHERE chat_id = ? AND id < ? ORDER BY id DESC LIMIT 10", (group_id, last_id))
		messages = cursor.fetchall()[-1::-1]
		cursor.execute("SELECT id FROM messages WHERE chat_id = ? AND id < ? ORDER BY id DESC LIMIT 10", (group_id, last_id))
		ids = self.flatten_array(cursor.fetchall())
		messages = self.replenish_ids_with_usernames(conn, messages)
		last_id = min(ids)
		return messages, last_id

	def flatten_array(self, array):
		return np.array(array).flatten().tolist()

	def analyze_message_autonomous(self, message, ID):
		logger.info(f"[SERVER] started analysing message {ID}")
		conn = sqlite3.connect("chat_server.db")
		cursor = conn.cursor()
		mistakes = message.analyze(self.my_spellchecker)
		cursor.executemany("""
			INSERT INTO typos (user_id, language_id, message_id, word_number, corrected_word) VALUES (?, ?, ?, ?, ?)
			""", [(self.get_user_id(conn, message.sender), 1, ID, mistake["word_number"], mistake["corrected_word"]) for mistake in mistakes])
		conn.commit()
		return

