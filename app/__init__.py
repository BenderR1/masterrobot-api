# app/__init__.py
import os
from flask import Flask, g, request
import uuid
from structlog.contextvars import bind_contextvars, clear_contextvars

from .config import Config
from .utils.logging_config import setup_logging, get_logger
from .services import db_service # Import db_service

# Initialize logger early, but setup happens in create_app
log = get_logger(__name__) # Get logger named 'app'

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True) # instance_relative_config=True is often useful
    app.config.from_object(config_class)

    # Ensure instance folder exists (needed for SQLite if path is relative to instance)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        # Also ensure data directory exists if using default path
        data_dir = os.path.join(os.path.dirname(app.instance_path), 'data')
        os.makedirs(data_dir, exist_ok=True)
        # Ensure upload folder exists if defined
        if app.config.get('UPLOAD_FOLDER'):
             os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        log.error("Could not create instance or data folder", path=app.instance_path)
        pass # Or raise an error

    # --- Setup Logging ---
    # Pass force_json=True if you want JSON logs even in development for testing
    setup_logging(app.config['LOG_LEVEL'])
    log.info("Flask app created", config=config_class.__name__, env=app.config['FLASK_ENV'])

    # --- Initialize Database ---
    db_service.init_app(app)
    log.info("Database service initialized.")

    # --- Request ID Logging Middleware ---
    @app.before_request
    def before_request():
        # Clear context variables at the start of each request
        clear_contextvars()
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        # Bind it to the context for all logs within this request
        bind_contextvars(request_id=request_id)
        # Store it on g for potential access in the request handler if needed
        g.request_id = request_id
        log.debug("Request started", method=request.method, path=request.path, remote_addr=request.remote_addr)

    @app.after_request
    def after_request(response):
        log.debug("Request finished", status_code=response.status_code)
        # Clear context variables after the request is done
        # clear_contextvars() # Usually done by before_request of the *next* request
        return response

    # --- Register Blueprints (API routes) ---
    from .routes import auth, system_message # Add system_message
    app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
    app.register_blueprint(system_message.bp, url_prefix='/api/v1/system_message')
    # Add others later: chat, history, image
    # app.register_blueprint(history.bp, url_prefix='/api/v1/history')
    # app.register_blueprint(image.bp, url_prefix='/api/v1/image')
    # app.register_blueprint(system_message.bp, url_prefix='/api/v1/system_message')
    log.info("Blueprints registered.")

    # --- Basic root route for health check/info ---
    @app.route('/')
    def index():
        log.debug("Root endpoint accessed")
        return {"message": "MasterRobot API is running!", "environment": app.config['FLASK_ENV']}

    log.info("App initialization complete.")
    return app