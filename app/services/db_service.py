# app/services/db_service.py
import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext
import os # Needed for schema path

# Import logger setup correctly
from app.utils.logging_config import get_logger

log = get_logger(__name__)

def get_db():
    """Connects to the application's configured database. Caches connection per request."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_URL'].replace('sqlite:///', '')
        # Ensure the directory exists if the path is not :memory:
        if db_path != ':memory:':
             os.makedirs(os.path.dirname(db_path), exist_ok=True)

        try:
            g.db = sqlite3.connect(
                db_path,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row # Access columns by name
            log.debug("Database connection established", path=db_path)
        except sqlite3.Error as e:
            log.error("Database connection failed", path=db_path, error=str(e))
            raise # Re-raise the exception
    return g.db

def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
            log.debug("Database connection closed.")
        except sqlite3.Error as e:
            log.error("Error closing database connection", error=str(e))


def init_db():
    """Initializes the database schema from schema.sql."""
    try:
        db = get_db()
        # Correct path relative to the project root where schema.sql is located
        schema_path = os.path.join(current_app.config['BASE_DIR'], 'data', 'schema.sql')
        log.info("Initializing database schema", path=schema_path)

        if not os.path.exists(schema_path):
             log.error("Database schema file not found", path=schema_path)
             raise FileNotFoundError(f"Schema file not found at {schema_path}")

        with open(schema_path, 'r') as f:
            db.executescript(f.read())
        db.commit() # Commit schema changes
        log.info("Database schema initialized successfully.")
    except sqlite3.Error as e:
        log.error("Error initializing database schema", error=str(e))
        if 'db' in locals() and db:
            db.rollback() # Rollback on error
        raise
    except Exception as e:
        log.error("Unexpected error during DB initialization", error=str(e))
        raise


# Command to initialize the database from Flask CLI
@click.command('init-db')
@with_appcontext # Ensures app context is available
def init_db_command():
    """Clear existing data and create new tables based on schema.sql."""
    try:
        init_db()
        click.echo('Initialized the database.')
    except Exception as e:
        log.error("Failed to initialize database via CLI", error=str(e), exc_info=True)
        click.echo(f'Error initializing database: {e}', err=True)


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db) # Call close_db when request context ends
    app.cli.add_command(init_db_command) # Add 'flask init-db' command
    log.debug("Database service functions registered with app.")

# --- Query Execution Helper (Optional but Recommended) ---
# You can add helper functions here or place query logic directly in services

def query_db(query, args=(), one=False):
    """Helper function to execute queries."""
    db = get_db()
    try:
        cur = db.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        db.commit() # Commit changes after successful execution (for INSERT/UPDATE/DELETE)
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        log.error("Database query failed", query=query, error=str(e))
        db.rollback() # Rollback on error
        # Depending on your error handling strategy, you might return None,
        # an empty list, or re-raise a custom exception
        return None # Example: return None on error

def insert_db(query, args=()):
    """Helper function for INSERT queries, returns last row ID."""
    db = get_db()
    try:
        cur = db.execute(query, args)
        last_id = cur.lastrowid
        cur.close()
        db.commit()
        return last_id
    except sqlite3.Error as e:
        log.error("Database insert failed", query=query, error=str(e))
        db.rollback()
        return None