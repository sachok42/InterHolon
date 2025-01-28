from protocol import *
import numpy as np


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

	def flatten_array(self, array):
		return np.array(array).flatten().tolist()