from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
import base64

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    sender = data['sender']
    recipient = data['recipient']
    message = data['message']

    # Fetch recipient's public key
    public_key_response = requests.get(f'http://authentication:5001/get_public_key/{recipient}',timeout=2.5)
    if public_key_response.status_code != 200:
        emit('error', {'error': 'Recipient not found'})
        return

    public_key = public_key_response.json()['public_key']
    encrypted_message = base64.b64encode(message.encode()).decode()

    # Store encrypted message
    requests.post('http://message:5002/store_message', json={
        'content': encrypted_message,
        'sender': sender,
        'recipient': recipient
    },timeout=2.5)

    emit('message', {'sender': sender, 'message': encrypted_message}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5003)
