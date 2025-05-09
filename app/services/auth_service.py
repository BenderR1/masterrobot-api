# app/services/auth_service.py
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta, timezone # Use timezone-aware datetimes
from flask import current_app

# Use the db helper functions or direct cursor execution
from .db_service import get_db, query_db, insert_db
from app.utils.logging_config import get_logger

log = get_logger(__name__)

def register_user(username, password):
    """Registers a new user if the username doesn't exist."""
    db = get_db()
    try:
        # Check if user already exists
        existing_user = query_db("SELECT id FROM users WHERE username = ?", (username,), one=True)
        if existing_user:
            log.warning("Registration attempt for existing username", username=username)
            return None, "Username already exists"

        # Hash the password
        password_hash = generate_password_hash(password)

        # Insert new user
        user_id = insert_db(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )

        if user_id:
            log.info("User registered successfully", username=username, user_id=user_id)
            return user_id, "User registered successfully"
        else:
            log.error("User registration failed during insert", username=username)
            return None, "Registration failed"

    except Exception as e: # Catch broader exceptions during DB interaction
        log.error("Exception during user registration", username=username, error=str(e), exc_info=True)
        return None, "An internal error occurred during registration"


def authenticate_user(username, password):
    """Authenticates a user and returns user info or None."""
    try:
        user = query_db("SELECT id, username, password_hash FROM users WHERE username = ?", (username,), one=True)

        if user and check_password_hash(user['password_hash'], password):
            log.info("User authenticated successfully", username=username, user_id=user['id'])
            # Return user info (excluding password hash)
            return {"id": user['id'], "username": user['username']}
        else:
            log.warning("Authentication failed", username=username, reason="User not found or invalid password")
            return None
    except Exception as e:
        log.error("Exception during user authentication", username=username, error=str(e), exc_info=True)
        return None

def generate_access_token(user_id):
    """Generates a JWT access token for the user."""
    try:
        payload = {
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'sub': str(user_id),  # <<< --- CHANGE THIS: Convert user_id to string
        }
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        log.debug("Generated JWT access token", user_id=user_id)
        return token
    except Exception as e:
        log.error("Failed to generate JWT token", user_id=user_id, error=str(e), exc_info=True)
        return None

def verify_access_token(token):
    """Verifies a JWT access token and returns the user ID (subject) as an integer or None."""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=["HS256"]
        )
        user_id_str = payload.get('sub')
        if user_id_str is None:
             log.warning("JWT verification failed: 'sub' claim missing", token_prefix=token[:10])
             return None
        try:
            user_id = int(user_id_str) # <<< --- CHANGE THIS: Convert 'sub' back to int
        except ValueError:
            log.warning("JWT verification failed: 'sub' claim is not a valid integer", sub_claim=user_id_str, token_prefix=token[:10])
            return None

        log.debug("JWT verified successfully", user_id=user_id)
        return user_id
    except jwt.ExpiredSignatureError:
        log.info("JWT verification failed: Expired signature", token_prefix=token[:10])
        return None
    except jwt.InvalidTokenError as e:
        log.warning("JWT verification failed: Invalid token", error=str(e), token_prefix=token[:10])
        return None
    except Exception as e:
        log.error("Unexpected error during JWT verification", error=str(e), exc_info=True)
        return None

def find_user_by_id(user_id):
    """Finds user details by ID (excluding password hash)."""
    try:
        user = query_db("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,), one=True)
        if user:
            return dict(user) # Convert Row to dict
        else:
            return None
    except Exception as e:
        log.error("Exception finding user by ID", user_id=user_id, error=str(e), exc_info=True)
        return None