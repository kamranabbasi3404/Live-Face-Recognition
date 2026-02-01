"""
Flask API Backend for Face Recognition with JWT Authentication
Run with: python api.py
"""
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import cv2
import numpy as np
import base64
import os
import sys
import jwt
import bcrypt
from datetime import datetime, timedelta

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.face_detector import FaceDetector
from modules.embeddings import EmbeddingGenerator
from modules.verifier import Verifier
from database.db_manager import DatabaseManager
from config import DUPLICATE_THRESHOLD, VERIFICATION_THRESHOLD

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-key-change-in-production')
JWT_EXPIRATION_HOURS = 24

# Initialize models (lazy loading)
detector = None
embedding_gen = None
verifier = None
db = None


def init_models():
    """Initialize AI models and database"""
    global detector, embedding_gen, verifier, db
    if detector is None:
        print("Loading AI models...")
        detector = FaceDetector()
        embedding_gen = EmbeddingGenerator()
        verifier = Verifier()
        db = DatabaseManager()
        print("Models loaded!")


def decode_base64_image(base64_string):
    """Decode base64 image to OpenCV format"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None


def to_python_type(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_python_type(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_python_type(x) for x in obj]
    return obj


def generate_token(account_id, email, name):
    """Generate JWT token for authenticated user"""
    payload = {
        'account_id': account_id,
        'email': email,
        'name': name,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            g.account_id = payload['account_id']
            g.email = payload['email']
            g.name = payload['name']
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated


# ==================== AUTH ENDPOINTS ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new account"""
    init_models()
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    
    if not email or not password or not name:
        return jsonify({'success': False, 'error': 'Email, password, and name are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    # Check if email already exists
    existing = db.get_account_by_email(email)
    if existing:
        return jsonify({'success': False, 'error': 'Email already registered'}), 409
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create account
    account_id = db.create_account(email, password_hash, name)
    if not account_id:
        return jsonify({'success': False, 'error': 'Failed to create account'}), 500
    
    # Generate token
    token = generate_token(account_id, email, name)
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully',
        'token': token,
        'user': {
            'id': account_id,
            'email': email,
            'name': name
        }
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login to existing account"""
    init_models()
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400
    
    # Get account
    account = db.get_account_by_email(email)
    if not account:
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    
    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), account['password_hash'].encode('utf-8')):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    
    # Generate token
    token = generate_token(account['id'], account['email'], account['name'])
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': account['id'],
            'email': account['email'],
            'name': account['name']
        }
    })


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current authenticated user"""
    init_models()
    
    account = db.get_account_by_id(g.account_id)
    if not account:
        return jsonify({'success': False, 'error': 'Account not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': account['id'],
            'email': account['email'],
            'name': account['name']
        }
    })


# ==================== PROTECTED ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Face Recognition API is running'})


@app.route('/api/enroll', methods=['POST'])
@token_required
def enroll_user():
    """Enroll a new user with face image (protected)"""
    init_models()
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    user_id = data.get('user_id', '').strip()
    name = data.get('name', '').strip()
    image_base64 = data.get('image', '')
    
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    if not image_base64:
        return jsonify({'success': False, 'error': 'Image is required'}), 400
    
    # Decode image
    img = decode_base64_image(image_base64)
    if img is None:
        return jsonify({'success': False, 'error': 'Invalid image data'}), 400
    
    # Detect face
    faces = detector.detect_faces(img)
    if not faces:
        return jsonify({'success': False, 'error': 'No face detected in image'}), 400
    
    face = detector.get_largest_face(faces)
    
    # Generate embedding
    embedding = embedding_gen.generate_embedding(face['face_img'])
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate face embedding'}), 500
    
    # Check for duplicate face (only within this account's users)
    result = verifier.verify_with_database(embedding, db, owner_id=g.account_id)
    if result['distance'] < DUPLICATE_THRESHOLD:
        return jsonify({
            'success': False,
            'error': 'Face already registered',
            'existing_user': result['user_name'],
            'distance': result['distance']
        }), 409
    
    # Generate user ID if not provided
    if not user_id:
        user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Check if user ID exists
    if db.user_exists(user_id):
        return jsonify({'success': False, 'error': 'User ID already exists'}), 409
    
    # Save user and embedding (with owner_id)
    if not db.add_user(user_id, name, owner_id=g.account_id):
        return jsonify({'success': False, 'error': 'Failed to save user'}), 500
    
    db.add_embedding(user_id, embedding)
    
    return jsonify({
        'success': True,
        'message': f'User {name} enrolled successfully',
        'user_id': user_id,
        'name': name
    })


@app.route('/api/verify', methods=['POST'])
@token_required
def verify_face():
    """Verify a face against enrolled users (protected, owner-filtered)"""
    init_models()
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    image_base64 = data.get('image', '')
    if not image_base64:
        return jsonify({'success': False, 'error': 'Image is required'}), 400
    
    # Decode image
    img = decode_base64_image(image_base64)
    if img is None:
        return jsonify({'success': False, 'error': 'Invalid image data'}), 400
    
    # Detect face
    faces = detector.detect_faces(img)
    if not faces:
        return jsonify({
            'success': False,
            'verified': False,
            'error': 'No face detected in image'
        }), 400
    
    face = detector.get_largest_face(faces)
    
    # Generate embedding
    embedding = embedding_gen.generate_embedding(face['face_img'])
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate face embedding'}), 500
    
    # Verify against database (only this account's users)
    result = verifier.verify_with_database(embedding, db, owner_id=g.account_id)
    
    # Convert ALL values to Python native types for JSON
    response = {
        'success': True,
        'verified': bool(result['verified']),
        'user_name': result['user_name'],
        'user_id': result['user_id'],
        'confidence': float(result['confidence']) if result['confidence'] else 0.0,
        'distance': float(result['distance']) if result['distance'] else 1.0,
        'face_box': [int(x) for x in face['box']]
    }
    
    return jsonify(response)


@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    """Get all enrolled users for current account (protected)"""
    init_models()
    
    users = db.get_all_users(owner_id=g.account_id)
    
    return jsonify({
        'success': True,
        'users': users,
        'total': len(users)
    })


@app.route('/api/users/<user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    """Delete a user (protected, owner-verified)"""
    init_models()
    
    if db.delete_user(user_id, owner_id=g.account_id):
        return jsonify({
            'success': True,
            'message': f'User {user_id} deleted successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'User not found or you do not have permission to delete'
        }), 404


@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    """Get system statistics for current account (protected)"""
    init_models()
    
    stats = db.get_statistics(owner_id=g.account_id)
    return jsonify({
        'success': True,
        'stats': stats
    })


if __name__ == '__main__':
    print("Starting Face Recognition API with Authentication...")
    init_models()
    app.run(host='0.0.0.0', port=5000, debug=True)
