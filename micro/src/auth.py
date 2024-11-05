from flask import Flask, request, jsonify
import sqlite3
import hashlib
import os

app = Flask(__name__)

# Define your API key for authentication
API_KEY = "your_secure_api_key"

# Database setup function
def init_db():
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            passhash TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database if it doesn't exist
if not os.path.exists('auth.db'):
    init_db()

# Helper function to hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register route
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    api_key = data.get('api_key')
    username = data.get('username')
    password = data.get('password')
    
    # Check for API key
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Hash the password
    passhash = hash_password(password)

    # Add the new user to the database
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, passhash) VALUES (?, ?)', (username, passhash))
        conn.commit()
        response = jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        response = jsonify({"error": "Username already exists"}), 409
    finally:
        conn.close()
    
    return response

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    api_key = data.get('api_key')
    username = data.get('username')
    password = data.get('password')
    
    # Check for API key
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Hash the password
    passhash = hash_password(password)
    
    # Check credentials in the database
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND passhash = ?', (username, passhash))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

if __name__ == '__main__':
    app.run(port=6060, debug=True)
