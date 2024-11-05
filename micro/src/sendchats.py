from flask import Flask, request, jsonify, abort
import sqlite3
import os
import uuid

app = Flask(__name__)

# Placeholder for API key
API_KEY = "add_msgs_key_123409876"

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

# Function to add a message to the database
def add_message(username, receiver, message):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    message_id = str(uuid.uuid4())  # Generate a new UUID for the message
    cursor.execute("""
        INSERT INTO messages (UUID, sender, receiver, content) 
        VALUES (?, ?, ?, ?)
    """, (message_id, username, receiver, message))
    conn.commit()
    conn.close()
    return message_id

# Route to handle POST request
@app.route('/add_message', methods=['POST'])
def add_message_route():
    # Extract JSON data from the request
    data = request.get_json()

    # Validate input
    username = data.get('username')
    receiver = data.get('receiver')
    message = data.get('message')
    api_key = data.get('api_key')

    # Validate API key
    if api_key != API_KEY:
        abort(403, description="Invalid API key")

    # Check required parameters
    if not username or not receiver or not message:
        abort(400, description="Missing required parameters")

    # Add the message to the database
    message_id = add_message(username, receiver, message)

    # Return success response with message ID
    return jsonify({"message": "Message added successfully", "UUID": message_id}), 201

if __name__ == '__main__':
    # Run the app on port 6070
    app.run(debug=True, port=6070)
