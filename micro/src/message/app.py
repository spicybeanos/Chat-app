from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64
import uuid
from datetime import datetime  # Import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Tiger@localhost/chat_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(50), nullable=False)
    recipient = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add timestamp field

@app.route('/store_message', methods=['POST'])
def store_message():
    data = request.json
    content = data.get('content')
    sender = data.get('sender')
    recipient = data.get('recipient')
    
    # Store message with the current timestamp
    new_message = Message(content=content, sender=sender, recipient=recipient)
    db.session.add(new_message)
    db.session.commit()
    
    return jsonify({"status": "Message stored", "message_id": new_message.id}), 201

@app.route('/get_messages/<recipient>', methods=['GET'])
def get_messages(recipient):
    # Retrieve messages for the recipient and order them by timestamp
    messages = Message.query.filter_by(recipient=recipient).order_by(Message.timestamp.asc()).all()
    
    # Return the messages in the correct order
    return jsonify([{"sender": msg.sender, "content": msg.content, "id": msg.id, "timestamp": msg.timestamp.isoformat()} for msg in messages])


if __name__ == "__main__":
    # Create tables within application context
    with app.app_context():
        db.create_all()
    
    app.run(host="0.0.0.0", port=5002)
