from flask import Flask, request, jsonify, abort
import sqlite3
import os

app = Flask(__name__)

# Placeholder for API key
API_KEY = "abcd1234"

# Database file path
DB_FILE = 'messages.db'

# Function to initialize the database if it doesn't exist
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE messages (
                UUID TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print("Database created and initialized.")

# Call init_db() to ensure the database is ready
init_db()

# Function to fetch messages between two users
def get_messages_between_users(me, receiver):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT UUID, sender, receiver, content 
        FROM messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
    """, (me, receiver, receiver, me))
    messages = cursor.fetchall()
    conn.close()
    return [{"UUID": row[0], "sender": row[1], "receiver": row[2], "content": row[3]} for row in messages]

# Route to handle GET request
@app.route('/get_messages', methods=['GET'])
def get_messages():
    # Extract query parameters
    me = request.args.get('me')
    receiver = request.args.get('receiver')
    api_key = request.args.get('api_key')

    # Validate API key
    if api_key != API_KEY:
        abort(403, description="Invalid API key")

    # Check required parameters
    if not me or not receiver:
        abort(400, description="Missing required parameters")

    # Fetch messages
    messages = get_messages_between_users(me, receiver)

    # Return messages as JSON
    return jsonify(messages)

if __name__ == '__main__':
    # Run the app on port 6080
    app.run(debug=True, port=6080)
