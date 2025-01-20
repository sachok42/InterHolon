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
		CREATE TABLE IF NOT EXISTS groups (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT UNIQUE NOT NULL
		)
	""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS messages (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			chat_type TEXT CHECK(chat_type IN ('group', 'personal')),
			chat_id INTEGER,
			sender TEXT,
			receiver TEXT,
			content TEXT,
			timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (chat_id) REFERENCES groups (id),
			FOREIGN KEY (receiver) REFERENCES users (username)
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
			-- PRIMARY KEY (user_id, language),
			FOREIGN KEY (message_id) REFERENCES messages(id),
			FOREIGN KEY (language_id) REFERENCES languages(id),
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
	""")
	