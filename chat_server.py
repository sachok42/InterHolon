import socket
import threading
import sqlite3
import json
from protocol import *

# Initialize SQLite database
def initialize_db():
    db_connect = sqlite3.connect("chat_server.db")
    cursor = db_connect.cursor()

    # Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """)

    # Group chats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Messages (group and personal)
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

    # Pre-populate group chats
    for group_name in base_groups:
        cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (group_name,))

    db_connect.commit()
    db_connect.close()

# Handle client requests
def handle_client(client_socket):
    db_connect = sqlite3.connect("chat_server.db")
    cursor = db_connect.cursor()

    while True:
        try:
            # Receive request
            request = client_socket.recv(1024).decode()
            if not request:
                break
            request_data = json.loads(request)

            action = request_data["action"]
            response = {"status": "error", "message": "Invalid action"}

            # Register user
            if action == "register":
                username = request_data["username"]
                try:
                    cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
                    db_connect.commit()
                    response = {"status": "success", "message": "User registered successfully"}
                except sqlite3.IntegrityError:
                    response = {"status": "error", "message": "Username already exists"}

            # Login user
            elif action == "login":
                username = request_data["username"]
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    response = {"status": "success", "message": "Login successful"}
                else:
                    response = {"status": "error", "message": "Invalid username"}

            # Send group message
            elif action == "send_group_message":
                group_name = request_data["group_name"]
                sender = request_data["sender"]
                content = request_data["content"]

                cursor.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
                group_id = cursor.fetchone()
                if group_id:
                    group_id = group_id[0]
                    cursor.execute("""
                        INSERT INTO messages (chat_type, chat_id, sender, content) 
                        VALUES ('group', ?, ?, ?)
                    """, (group_id, sender, content))
                    db_connect.commit()
                    response = {"status": "success", "message": "Message sent"}
                else:
                    response = {"status": "error", "message": "Group does not exist"}

            # Send personal message
            elif action == "send_personal_message":
                sender = request_data["sender"]
                receiver = request_data["receiver"]
                content = request_data["content"]

                cursor.execute("SELECT id FROM users WHERE username = ?", (receiver,))
                if cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO messages (chat_type, sender, receiver, content) 
                        VALUES ('personal', ?, ?, ?)
                    """, (sender, receiver, content))
                    db_connect.commit()
                    response = {"status": "success", "message": "Message sent"}
                else:
                    response = {"status": "error", "message": "Receiver does not exist"}

            # Fetch group messages
            elif action == "get_group_messages":
                group_name = request_data["group_name"]
                cursor.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
                group_id = cursor.fetchone()
                if group_id:
                    group_id = group_id[0]
                    cursor.execute("""
                        SELECT sender, content FROM messages 
                        WHERE chat_type = 'group' AND chat_id = ? 
                        ORDER BY timestamp
                    """, (group_id,))
                    messages = cursor.fetchall()
                    response = {"status": "success", "messages": messages}
                else:
                    response = {"status": "error", "message": "Group does not exist"}

            # Fetch personal messages
            elif action == "get_personal_messages":
                user1 = request_data["user1"]
                user2 = request_data["user2"]
                cursor.execute("""
                    SELECT sender, content FROM messages 
                    WHERE chat_type = 'personal' AND 
                    ((sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)) 
                    ORDER BY timestamp
                """, (user1, user2, user2, user1))
                messages = cursor.fetchall()
                response = {"status": "success", "messages": messages}

            # Get list of users (new action for personal chat mode)
            elif action == "get_users":
                cursor.execute("SELECT username FROM users")
                users = [row[0] for row in cursor.fetchall()]
                response = {"status": "success", "users": users}

            # Send response
            client_socket.send(json.dumps(response).encode())
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    db_connect.close()

# Start the server
def start_server():
    initialize_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen(5)
    print("Server is listening on port 12345...")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection established with {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
