# app/routes/system_message.py
from flask import Blueprint, request, jsonify, g
from app.services import system_message_service
from app.routes.auth import login_required # Import the decorator
from app.utils.logging_config import get_logger

log = get_logger(__name__)
bp = Blueprint('system_message', __name__)

@bp.route('/', methods=['POST'])
@login_required
def create():
    """Creates a new system message for the logged-in user."""
    user_id = g.user['id']
    data = request.get_json()
    if not data or not data.get('name') or not data.get('content'):
        log.warning("Create system message attempt with missing fields", user_id=user_id)
        return jsonify({"error": "Name and content are required"}), 400

    name = data['name']
    content = data['content']

    message_id, message = system_message_service.create_system_message(user_id, name, content)

    if message_id:
        # Fetch the created message to return it
        new_message = system_message_service.get_system_message_by_id(user_id, message_id)
        return jsonify(new_message), 201
    else:
        status_code = 409 if "already exists" in message else 500
        return jsonify({"error": message}), status_code

@bp.route('/', methods=['GET'])
@login_required
def list_messages():
    """Lists all system messages for the logged-in user."""
    user_id = g.user['id']
    messages = system_message_service.get_system_messages_for_user(user_id)
    return jsonify(messages), 200

@bp.route('/<int:message_id>', methods=['GET'])
@login_required
def get_message(message_id):
    """Gets a specific system message by ID for the logged-in user."""
    user_id = g.user['id']
    message = system_message_service.get_system_message_by_id(user_id, message_id)
    if message:
        return jsonify(message), 200
    else:
        log.warning("System message get request failed: not found or access denied", user_id=user_id, message_id=message_id)
        return jsonify({"error": "System message not found or access denied"}), 404

@bp.route('/<int:message_id>', methods=['PUT'])
@login_required
def update(message_id):
    """Updates a specific system message by ID for the logged-in user."""
    user_id = g.user['id']
    data = request.get_json()
    if not data or not data.get('name') or not data.get('content'):
        log.warning("Update system message attempt with missing fields", user_id=user_id, message_id=message_id)
        return jsonify({"error": "Name and content are required"}), 400

    name = data['name']
    content = data['content']

    success, message = system_message_service.update_system_message(user_id, message_id, name, content)

    if success:
        updated_message = system_message_service.get_system_message_by_id(user_id, message_id)
        return jsonify(updated_message), 200
    else:
        status_code = 404 if "not found" in message else (409 if "already exists" in message else 500)
        return jsonify({"error": message}), status_code

@bp.route('/<int:message_id>', methods=['DELETE'])
@login_required
def delete(message_id):
    """Deletes a specific system message by ID for the logged-in user."""
    user_id = g.user['id']
    success, message = system_message_service.delete_system_message(user_id, message_id)

    if success:
        return jsonify({"message": message}), 200 # Or 204 No Content
    else:
        status_code = 404 if "not found" in message else 500
        return jsonify({"error": message}), status_code