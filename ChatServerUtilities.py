from protocol import *
import numpy as np
import sqlite3
from POS_tagger import POS_tagger
from phunspell import Phunspell
import phunspell
from log_protocol import create_file_logger
import spellchecker as sp
from language_protocol import good_spellchecking_supporting
from Spellchecker import Spellchecker
from decomplex_numbers import decomplex_numbers


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
		custom_log(f"[ChatServerUtilities] on spellcheck_text: message is {message}")
		if language not in self.spellcheckers:
			if language_names_to_shortnames[language] in good_spellchecking_supporting:
				self.spellcheckers[language] = Spellchecker(sp.SpellChecker(language=language_names_to_shortnames[language]))
			else:
				self.spellcheckers[language] = Spellchecker(Phunspell(full_names_to_phunspell_names[language]))
			custom_log(f"[ChatServerUtilities] on spellcheck_text: created spellchecker for language {language}")
		else:
			custom_log(f"[ChatServerUtilities] on spellcheck_text: no new spellchecker needed")
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

	def get_language(self, cursor, ID):
		cursor.execute("""SELECT name FROM languages WHERE id = ?""", (ID,))
		return cursor.fetchone()[0]

	def replenish_ids_with_languages_flat(self, conn, elements):
		cursor = conn.cursor()
		result = [self.get_language(cursor, element) for element in elements]
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
		
	def create_group_by_ids(self, conn, group_name, participants_ids):
		self.add_chat(conn, group_name)
		group_id = self.get_chat_id(conn, group_name)
		cursor = conn.cursor()
		cursor.executemany("""
			INSERT INTO group_participants (group_id, user_id) VALUES (?, ?)
			""", [(group_id, user_id) for user_id in participants_ids])
		conn.commit()
		return {"status": "success", "message": f"group {group_name} created"}

	def get_messages(self, conn, group_id, last_id=1e9):
		cursor = conn.cursor()
		cursor.execute("""
			SELECT sender_id, id, timestamp, content, POS_tags FROM messages
			 WHERE chat_id = ? AND id < ? ORDER BY id DESC LIMIT ?
			""", (group_id, last_id, MESSAGES_PER_LOAD))
		messages = cursor.fetchall()[-1::-1]
		cursor.execute("SELECT id FROM messages WHERE chat_id = ? AND id < ? ORDER BY id DESC LIMIT ?", \
			(group_id, last_id, MESSAGES_PER_LOAD))
		ids = self.flatten_array(cursor.fetchall())
		if len(messages) == 0:
			last_id = 1e9
			biggest_id = -1
		else:
			last_id = min(ids)
			biggest_id = max(ids)

		messages = self.replenish_ids_with_usernames(conn, messages)
		# messages_tagged = [(messages[i][:-1] + [tags[i]]) for i in range(len(messages))]
		return messages, last_id, biggest_id

	def flatten_array(self, array):
		return np.array(array).flatten().tolist()

	def analyze_message_autonomous(self, message, ID):
		lang_logger.info(f"[SERVER] started analysing message {ID}")
		try:
			conn = sqlite3.connect("chat_server.db")
			cursor = conn.cursor()
			content = decomplex_numbers(message.content)
			pre_tags = self.tag_text(message.language, content)

			tags = ' '.join([tag[1] for sentence in pre_tags for tag in sentence])
			content = ' '.join([tag[0] for sentence in pre_tags for tag in sentence])
			new_words = []
			if len(tags.split()) != len(content.split()):
				custom_log(f"[SERVER] on analyze_message_autonomous: CODE RED: something was tagged badly on message {ID}")

			cursor.execute("""
				UPDATE messages SET POS_tags = ?, content = ? WHERE ID = ?
				""", (tags, content, ID))
			lang_logger.info(f"[SERVER] on analyze_message_autonomous: tags are {tags}")

			mistakes = self.spellcheck_text(message.language, message)
			# logger.info(f"[SERVER] on analyze_message_autonomous: tags are {tags}")
			cursor.executemany("""
				INSERT INTO typos (user_id, language_id, message_id, word_number, corrected_word, wrong_word) 
				VALUES (?, ?, ?, ?, ?, ?)
				""", [(self.get_user_id(conn, message.sender), 1, ID, \
				 mistake["word_number"], mistake["corrected_word"], mistake["original"]) for mistake in mistakes])
		except Exception as e:
			lang_logger.error(f"[SERVER]: exception {e}")
		conn.commit()
		return

	def replenish_ids_with_chats_flat(self, conn, elements):
		cursor = conn.cursor()
		result = [self.get_chat_name(conn, element) for element in elements]
		return result
