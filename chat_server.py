import socket
import threading
import sqlite3
import json

# Initialize SQLite database
def initialize_db():
    conn = sqlite3.connect("chat_server.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            sender TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
    """)
    # Add sample chats
    for chat_name in ["Family", "Work", "Friends"]:
        c.execute("INSERT OR IGNORE INTO chats (name) VALUES (?)", (chat_name,))
    conn.commit()
    conn.close()

# Handle client requests
def handle_client(client_socket):
    conn = sqlite3.connect("chat_server.db")
    c = conn.cursor()

    while True:
        try:
            # Receive and decode the request
            request = client_socket.recv(1024).decode()
            if not request:
                break
            request_data = json.loads(request)

            action = request_data["action"]
            response = {"status": "error", "message": "Invalid action"}

            if action == "register":
                username = request_data["username"]
                try:
                    c.execute("INSERT INTO users (username) VALUES (?)", (username,))
                    conn.commit()
                    response = {"status": "success", "message": "User registered successfully"}
                except sqlite3.IntegrityError:
                    response = {"status": "error", "message": "Username already exists"}

            elif action == "login":
                username = request_data["username"]
                c.execute("SELECT id FROM users WHERE username = ?", (username,))
                if c.fetchone():
                    response = {"status": "success", "message": "Login successful"}
                else:
                    response = {"status": "error", "message": "Invalid username"}

            elif action == "send_message":
                chat_name = request_data["chat_name"]
                sender = request_data["sender"]
                content = request_data["content"]

                c.execute("SELECT id FROM chats WHERE name = ?", (chat_name,))
                chat_id = c.fetchone()
                if chat_id:
                    chat_id = chat_id[0]
                    c.execute("INSERT INTO messages (chat_id, sender, content) VALUES (?, ?, ?)",
                              (chat_id, sender, content))
                    conn.commit()
                    response = {"status": "success", "message": "Message sent"}
                else:
                    response = {"status": "error", "message": "Chat does not exist"}

            elif action == "get_messages":
                chat_name = request_data["chat_name"]
                c.execute("SELECT id FROM chats WHERE name = ?", (chat_name,))
                chat_id = c.fetchone()
                if chat_id:
                    chat_id = chat_id[0]
                    c.execute("""
                        SELECT sender, content FROM messages WHERE chat_id = ? ORDER BY timestamp
                    """, (chat_id,))
                    messages = c.fetchall()
                    response = {"status": "success", "messages": messages}
                else:
                    response = {"status": "error", "message": "Chat does not exist"}

            # Send the response back to the client
            client_socket.send(json.dumps(response).encode())
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    conn.close()

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
