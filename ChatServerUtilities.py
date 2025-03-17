from protocol import *
import numpy as np
import sqlite3
from POS_tagger import POS_tagger
from phunspell import Phunspell
from log_protocol import create_file_logger

create_file_logger("language_logger")
lang_logger = logging.getLogger("language_logger")

class ChatServerUtilities:
	def __init__(self):
		self.POS_taggers = {}
		self.spellcheckers = {}
		for language in languages:
			self.tag_text(language, '')

	def tag_text(self, language, text):
		language = language_names_to_shortnames[language]
		if language not in self.POS_taggers:
			self.POS_taggers[language] = POS_tagger(language)
		return self.POS_taggers[language].tag_text(text)

	def spellcheck_text(self, language, message):
		if language not in self.spellcheckers:
			self.spellcheckers[language] = Phunspell(full_names_to_phunspell_names[language])
		return message.analyze(self.spellcheckers[language])

	def get_user_id(self, conn, user):
		try:
			cursor = conn.cursor()
			logger.info(f"[SERVER] on get_user_id user {user}")
			cursor.execute("""
				SELECT id FROM users WHERE username = ?
				""", (user,))
			user_id = cursor.fetchone()[0]
			# logger.info(f"[SERVER] user {user} id {user_id}")
			return user_id
		except Exception as e:
			logger.error(f"[SERVER] on get_user_id: user {user} not found")
			return None

	def get_username(self, cursor, ID):
		logger.info(f"[SERVER] finds the name of user id {ID}")
		cursor.execute("SELECT username FROM users WHERE id = ?", (ID,))
		username = cursor.fetchone()[0]
		return username

	def get_language_name(self, cursor, ID):
		logger.info(f"[SERVER] finds name of the user id {ID}")
		cursor.execute("SELECT name FROM languages WHERE id = ?", (ID,))
		return cursor.fetchone()[0]

	def get_language_id(self, conn, language):
		cursor = conn.cursor()
		cursor.execute("SELECT id FROM languages WHERE name = ?", (language,))
		return cursor.fetchone()[0]

	def replenish_ids_with_usernames(self, conn, elements):
		cursor = conn.cursor()
		result = [(self.get_username(cursor, element[0]), *element[1:]) for element in elements]
		return result

	def replenish_usernames_with_ids_flat(self, conn, users):
		cursor = conn.cursor()
		result = [self.get_user_id(conn, user) for user in users]
		return result

	def replenish_ids_with_usernames_flat(self, conn, elements):
		cursor = conn.cursor()
		result = [self.get_username(cursor, element) for element in elements]
		return result

	def replenish_ids_with_languages_flat(self, conn, elements):
		cursor = conn.cursor()
		result = [self.get_username(cursor, element) in elements]
		return result

	def get_chat_name(self, conn, ID):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT name FROM chats WHERE id = ?
			""", (ID,))
		return cursor.fetchone()[0]

	def get_chat_id(self, conn, name):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT id FROM chats WHERE name = ?
			""", (name,))
		return cursor.fetchone()[0]
		
	def get_messages(self, conn, group_id, last_id=1e6):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT sender_id, timestamp, content, POS_tags FROM messages WHERE chat_id = ? AND id < ? ORDER BY id DESC LIMIT 10
			""", (group_id, last_id))
		messages = cursor.fetchall()[-1::-1]
		cursor.execute("SELECT id FROM messages WHERE chat_id = ? AND id < ? ORDER BY id DESC LIMIT 10", (group_id, last_id))
		ids = self.flatten_array(cursor.fetchall()) + [1e9]
		messages = self.replenish_ids_with_usernames(conn, messages)
		last_id = min(ids)
		# messages_tagged = [(messages[i][:-1] + [tags[i]]) for i in range(len(messages))]
		return messages, last_id

	def flatten_array(self, array):
		return np.array(array).flatten().tolist()

	def analyze_message_autonomous(self, message, ID):
		lang_logger.info(f"[SERVER] started analysing message {ID}")
		try:
			conn = sqlite3.connect("chat_server.db")
			cursor = conn.cursor()
			mistakes = self.spellcheck_text(message.language, message)
			pre_tags = self.tag_text(message.language, message.content)
			# logger.info(f"[SERVER] on analyze_message_autonomous: tags are {tags}")
			tags = ' '.join([tag[1] for sentence in pre_tags for tag in sentence])
			content = ' '.join([tag[0] for sentence in pre_tags for tag in sentence])
			cursor.executemany("""
				INSERT INTO typos (user_id, language_id, message_id, word_number, corrected_word) VALUES (?, ?, ?, ?, ?)
				""", [(self.get_user_id(conn, message.sender), 1, ID, mistake["word_number"], mistake["corrected_word"]) for mistake in mistakes])
			cursor.execute("""
				UPDATE messages SET POS_tags = ?, content = ? WHERE ID = ?
				""", (tags, content, ID))
			lang_logger.info(f"[SERVER] on analyze_message_autonomous: tags are {tags}")
		except Exception as e:
			lang_logger.error(f"[SERVER]: exception {e}")
		conn.commit()
		return

	def replenish_ids_with_chats_flat(self, conn, elements):
		cursor = conn.cursor()
		result = [self.get_chat_name(conn, element) for element in elements]
		return result
