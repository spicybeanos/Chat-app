from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Tiger@localhost/chat_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class UserKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    private_key = db.Column(db.Text, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    api_key = db.Column(db.String(36), unique=True, nullable=False)

def create_tables():
    db.create_all()

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    username = request.json.get('username')
    if UserKey.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    api_key = str(uuid.uuid4())
    
    new_user_key = UserKey(username=username, private_key=pem_private_key, public_key=pem_public_key, api_key=api_key)
    db.session.add(new_user_key)
    db.session.commit()

    return jsonify({"public_key": pem_public_key, "api_key": api_key}), 201

@app.route('/get_public_key/<username>', methods=['GET'])
def get_public_key(username):
    user_key = UserKey.query.filter_by(username=username).first()
    if not user_key:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"public_key": user_key.public_key}), 200

def api_key_required(f):
    def decorator(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key or not UserKey.query.filter_by(api_key=api_key).first():
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator

@app.route('/protected', methods=['GET'])
@api_key_required
def protected():
    return jsonify({"msg": "This is a protected route"}), 200

if __name__ == "__main__":
    # Create tables if they don't exist within an application context
    with app.app_context():
        create_tables()
    app.run(host="0.0.0.0", port=5001)
