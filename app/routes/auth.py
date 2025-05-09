# app/routes/auth.py
from flask import Blueprint, request, jsonify, g, current_app
from functools import wraps
from app.services import auth_service
from app.utils.logging_config import get_logger

log = get_logger(__name__)

bp = Blueprint('auth', __name__)

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                 log.warning("Invalid Authorization header format")
                 return jsonify({"error": "Invalid Authorization header format"}), 401

        if not token:
            log.warning("Authorization token is missing")
            return jsonify({"error": "Authorization token is missing"}), 401

        user_id = auth_service.verify_access_token(token)
        if user_id is None:
            log.warning("Invalid or expired token provided")
            return jsonify({"error": "Invalid or expired token"}), 401

        # Token is valid, find the user and attach to Flask's g for this request
        user = auth_service.find_user_by_id(user_id)
        if not user:
             log.error("User ID from valid token not found in DB", user_id=user_id)
             # This shouldn't happen if DB is consistent, but handle defensively
             return jsonify({"error": "User not found for token"}), 401

        g.user = user # Store user dict (id, username, created_at) in g
        log.debug("User authenticated via token", user_id=g.user['id'])

        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        log.warning("Registration attempt with missing fields", data_keys=list(data.keys()) if data else None)
        return jsonify({"error": "Username and password are required"}), 400

    username = data['username']
    password = data['password']

    user_id, message = auth_service.register_user(username, password)

    if user_id:
        return jsonify({"message": message, "user_id": user_id}), 201 # 201 Created
    else:
        # Determine status code based on message (e.g., conflict vs. internal error)
        status_code = 409 if "already exists" in message else 500
        return jsonify({"error": message}), status_code

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        log.warning("Login attempt with missing fields", data_keys=list(data.keys()) if data else None)
        return jsonify({"error": "Username and password are required"}), 400

    username = data['username']
    password = data['password']

    user = auth_service.authenticate_user(username, password)

    if user:
        access_token = auth_service.generate_access_token(user['id'])
        if access_token:
            log.info("Login successful, token generated", username=username, user_id=user['id'])
            return jsonify({"access_token": access_token, "user": user}), 200
        else:
            log.error("Login successful but token generation failed", username=username, user_id=user['id'])
            return jsonify({"error": "Could not generate access token"}), 500
    else:
        log.warning("Login failed", username=username)
        return jsonify({"error": "Invalid username or password"}), 401

@bp.route('/profile', methods=['GET'])
@login_required # Protect this route
def profile():
    # g.user is populated by the @login_required decorator
    log.info("Profile accessed", user_id=g.user['id'])
    # Return user info stored in g (already excludes password hash)
    return jsonify(g.user), 200

# Add /logout route if needed (e.g., for JWT blocklisting)