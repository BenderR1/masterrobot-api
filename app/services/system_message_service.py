# app/services/system_message_service.py
from .db_service import query_db, insert_db
from app.utils.logging_config import get_logger

log = get_logger(__name__)

def create_system_message(user_id, name, content):
    """Creates a new system message for a user."""
    try:
        # Optional: Check for duplicate name for this user
        existing = query_db("SELECT id FROM system_messages WHERE user_id = ? AND name = ?", (user_id, name), one=True)
        if existing:
            log.warning("Attempt to create system message with duplicate name", user_id=user_id, name=name)
            return None, "A system message with this name already exists for this user."

        message_id = insert_db(
            "INSERT INTO system_messages (user_id, name, content) VALUES (?, ?, ?)",
            (user_id, name, content)
        )
        if message_id:
            log.info("System message created", user_id=user_id, name=name, message_id=message_id)
            return message_id, "System message created successfully."
        else:
            log.error("System message creation failed during insert", user_id=user_id, name=name)
            return None, "Failed to create system message."
    except Exception as e:
        log.error("Exception creating system message", user_id=user_id, name=name, error=str(e), exc_info=True)
        return None, "An internal error occurred."

def get_system_messages_for_user(user_id):
    """Retrieves all system messages for a specific user."""
    try:
        messages = query_db(
            "SELECT id, name, content, created_at FROM system_messages WHERE user_id = ? ORDER BY name ASC",
            (user_id,)
        )
        log.debug("Retrieved system messages for user", user_id=user_id, count=len(messages))
        # Convert Row objects to dictionaries
        return [dict(msg) for msg in messages]
    except Exception as e:
        log.error("Exception retrieving system messages", user_id=user_id, error=str(e), exc_info=True)
        return [] # Return empty list on error

def get_system_message_by_id(user_id, message_id):
    """Retrieves a specific system message by ID, ensuring it belongs to the user."""
    try:
        message = query_db(
            "SELECT id, name, content, created_at FROM system_messages WHERE id = ? AND user_id = ?",
            (message_id, user_id),
            one=True
        )
        if message:
            log.debug("Retrieved system message by ID", user_id=user_id, message_id=message_id)
            return dict(message)
        else:
            log.warning("System message not found or access denied", user_id=user_id, message_id=message_id)
            return None
    except Exception as e:
        log.error("Exception retrieving system message by ID", user_id=user_id, message_id=message_id, error=str(e), exc_info=True)
        return None

def update_system_message(user_id, message_id, name, content):
    """Updates a system message, ensuring ownership."""
    try:
        # Optional: Check for name conflict (excluding the current message being updated)
        existing = query_db(
            "SELECT id FROM system_messages WHERE user_id = ? AND name = ? AND id != ?",
            (user_id, name, message_id), one=True
        )
        if existing:
            log.warning("Attempt to update system message resulting in duplicate name", user_id=user_id, name=name, message_id=message_id)
            return False, "Another system message with this name already exists."

        # Use query_db helper which handles commit/rollback
        result = query_db(
            "UPDATE system_messages SET name = ?, content = ? WHERE id = ? AND user_id = ?",
            (name, content, message_id, user_id)
        )
        # Check if the update affected any row (query_db doesn't directly return row count)
        # We can re-fetch to confirm or modify query_db to return rowcount
        updated_message = get_system_message_by_id(user_id, message_id)
        if updated_message and updated_message['name'] == name and updated_message['content'] == content:
             log.info("System message updated successfully", user_id=user_id, message_id=message_id)
             return True, "System message updated successfully."
        else:
             # Could be that the message_id didn't exist or didn't belong to user
             log.warning("System message update failed (not found or no change)", user_id=user_id, message_id=message_id)
             # Check if it exists at all for this user to give a better error
             if get_system_message_by_id(user_id, message_id) is None:
                 return False, "System message not found or access denied."
             else:
                 return False, "Failed to update system message (no changes detected or other error)."

    except Exception as e:
        log.error("Exception updating system message", user_id=user_id, message_id=message_id, error=str(e), exc_info=True)
        return False, "An internal error occurred."


def delete_system_message(user_id, message_id):
    """Deletes a system message, ensuring ownership."""
    try:
        # Check if it exists first (optional, DELETE won't error if not found)
        message = get_system_message_by_id(user_id, message_id)
        if not message:
            log.warning("Attempt to delete non-existent or unauthorized system message", user_id=user_id, message_id=message_id)
            return False, "System message not found or access denied."

        # Use query_db helper
        query_db(
            "DELETE FROM system_messages WHERE id = ? AND user_id = ?",
            (message_id, user_id)
        )
        # Verify deletion
        if get_system_message_by_id(user_id, message_id) is None:
            log.info("System message deleted successfully", user_id=user_id, message_id=message_id)
            return True, "System message deleted successfully."
        else:
            # This shouldn't happen if the DELETE worked and get_system_message_by_id is correct
            log.error("System message deletion failed verification", user_id=user_id, message_id=message_id)
            return False, "Failed to delete system message."
    except Exception as e:
        log.error("Exception deleting system message", user_id=user_id, message_id=message_id, error=str(e), exc_info=True)
        return False, "An internal error occurred."