from protocol import *

def sql_db_init(cursor):
	cursor.execute("""
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT UNIQUE NOT NULL,
					hashed_password TEXT NOT NULL,
					salt TEXT NOT NULL
				)
			""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS languages (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT UNIQUE NOT NULL
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS chats (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT UNIQUE NOT NULL,
			type TEXT CHECK(type in ('group', 'personal')) DEFAULT 'group'
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS messages (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			chat_type TEXT CHECK(chat_type IN ('group', 'personal')),
			chat_id INTEGER,
			sender_id INTEGER,
			content TEXT,
			timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (chat_id) REFERENCES groups (id),
			FOREIGN KEY (chat_type) REFERENCES groups (type),
			FOREIGN KEY (sender_id) REFERENCES users (id)
			-- PRIMARY KEY (group_id, id)
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS user_languages (
			user_id INTEGER,
			language_id INTEGER,
			-- PRIMARY KEY (user_id, language),
			FOREIGN KEY (language_id) REFERENCES languages (id),					
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS typos (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER,
			language_id INTEGER,
			message_id INTEGER,
			word_number INTEGER,
			corrected_word TEXT,
			FOREIGN KEY (message_id) REFERENCES messages(id),
			FOREIGN KEY (language_id) REFERENCES languages(id),
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS contacts (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			id1 INTEGER,
			id2 INTEGER,
			chat_id INTEGER UNIQUE,
			FOREIGN KEY (chat_id) REFERENCES chats(id),
			FOREIGN KEY (id1) REFERENCES users(id),
			FOREIGN KEY (id2) REFERENCES users(id)
			)
		""")

	cursor.execute("""
		CREATE TABLE IF NOT EXISTS requests (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			sender_id INTEGER,
			receiver_id INTEGER,
			FOREIGN KEY (sender_id) REFERENCES users(id),
			FOREIGN KEY (receiver_id) REFERENCES users(id)
			)
		""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS group_participants (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			group_id INTEGER,
			user_id INTEGER,
			FOREIGN KEY (group_id) REFERENCES chats(id),
			FOREIGN KEY (user_id) REFERENCES users(id)
			)
		""")
	# cursor.execute("""
	# 	CREATE INDEX OR IGNORE message_index ON messages (chat_id, id)
	# 	""")

	for language_name in languages:
		cursor.execute("INSERT OR IGNORE INTO languages (name) VALUES (?)", (language_name,))

