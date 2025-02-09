from flask import jsonify, request, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import random
import string
from functools import wraps
from app.models.user_model import users_collection
from app.models.token_model import tokens_collection
from app import app
from app import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
from email.mime.text import MIMEText
import smtplib

# JWT configuration
JWT_SECRET_KEY = app.config.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_2fa_token():
    """Generate a 6-digit 2FA token"""
    return ''.join(random.choices(string.digits, k=6))

def send_2fa_email(email, token):
    """Send 2FA token via email"""
    msg = MIMEText(f'Your verification code is: {token}')
    msg['Subject'] = '2FA Verification Code'
    msg['From'] = SMTP_USERNAME
    msg['To'] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = users_collection.find_one({'email': data['email']})
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            print(f"Error decoding token: {e}")
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

def signup():
    """Handle user signup"""
    data = request.json

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if user already exists
    if users_collection.find_one({'email': data['email']}):
        return jsonify({'message': 'User already exists'}), 409

    # Hash password and create user
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = {
        'email': data['email'],
        'password': hashed_password,
        'is_verified': False,
        'created_at': datetime.datetime.utcnow()
    }

    users_collection.insert_one(new_user)

    # Generate and send 2FA token
    token = generate_2fa_token()
    tokens_collection.insert_one({
        'email': data['email'],
        'token': token,
        'created_at': datetime.datetime.utcnow()
    })

    if send_2fa_email(data['email'], token):
        return jsonify({'message': 'User created. Please verify your email'}), 201
    else:
        return jsonify({'message': 'Error sending verification email'}), 500

def verify_2fa():
    """Handle 2FA verification"""
    data = request.json

    if not data or not data.get('email') or not data.get('token'):
        return jsonify({'message': 'Missing required fields'}), 400

    stored_token = tokens_collection.find_one({
        'email': data['email'],
        'token': data['token'],
        'created_at': {'$gt': datetime.datetime.utcnow() - datetime.timedelta(minutes=10)}
    })

    if not stored_token:
        return jsonify({'message': 'Invalid or expired token'}), 401

    # Update user verification status
    users_collection.update_one(
        {'email': data['email']},
        {'$set': {'is_verified': True}}
    )

    # Clean up used token
    tokens_collection.delete_one({'_id': stored_token['_id']})

    return jsonify({'message': 'Email verified successfully'}), 200

def login():
    """Handle user login"""
    data = request.json

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    user = users_collection.find_one({'email': data['email']})

    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    if not user['is_verified']:
        return jsonify({'message': 'Please verify your email first'}), 403

    # Generate and send 2FA token for login
    token = generate_2fa_token()
    tokens_collection.insert_one({
        'email': data['email'],
        'token': token,
        'created_at': datetime.datetime.utcnow()
    })

    if send_2fa_email(data['email'], token):
        return jsonify({'message': 'Please check your email for 2FA code'}), 200
    else:
        return jsonify({'message': 'Error sending 2FA code'}), 500

def login_verify():
    """Handle 2FA login verification"""
    data = request.json

    if not data or not data.get('email') or not data.get('token'):
        return jsonify({'message': 'Missing required fields'}), 400

    stored_token = tokens_collection.find_one({
        'email': data['email'],
        'token': data['token'],
        'created_at': {'$gt': datetime.datetime.utcnow() - datetime.timedelta(minutes=10)}
    })

    if not stored_token:
        return jsonify({'message': 'Invalid or expired token'}), 401

    # Generate JWT token
    token = jwt.encode({
        'email': data['email'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, JWT_SECRET_KEY)

    # Clean up used token
    tokens_collection.delete_one({'_id': stored_token['_id']})

    # Create response with httpOnly cookie
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie(
        'token',
        token,
        httponly=True,
        secure=True,  # Enable in production with HTTPS
        samesite='Strict',
        max_age=7 * 24 * 60 * 60  # 7 days
    )

    return response

def logout():
    """Handle user logout"""
    response = make_response(jsonify({'message': 'Logout successful'}))
    response.delete_cookie('token')
    return response

@token_required
def protected_route(current_user):
    """Example protected route"""
    return jsonify({'message': f'Hello {current_user["email"]}!'})