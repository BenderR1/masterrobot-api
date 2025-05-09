# app/utils/logging_config.py
import logging
import sys
import structlog
from structlog.contextvars import merge_contextvars
import os # Needed for checking environment

def setup_logging(log_level="INFO", force_json=False):
    """Configures structlog to wrap standard logging."""

    # Determine renderer based on environment or force_json flag
    # In production (or when forced), use JSON. Otherwise, use ConsoleRenderer for dev.
    is_production = os.environ.get('FLASK_ENV', 'development') == 'production'
    renderer_processor = structlog.processors.JSONRenderer() if (is_production or force_json) else structlog.dev.ConsoleRenderer(colors=True)
    renderer_name = "JSONRenderer" if (is_production or force_json) else "ConsoleRenderer"

    logging.basicConfig(
        format="%(message)s", # structlog handles the final formatting
        stream=sys.stdout,
        level=log_level.upper(),
    )

    structlog.configure(
        processors=[
            merge_contextvars, # Add context variables like request_id
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"), # Add ISO timestamp
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # The processor decides the final output format (JSON or Console)
        processor=renderer_processor,
        foreign_pre_chain=[
            # Optional: Add standard library log record attributes here if needed
            # structlog.stdlib.ExtraAdder(),
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove existing handlers added by basicConfig or Flask's default
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Use standard print here as logging might not be fully flushed initially
    print(f"Logging configured at level {log_level} using {renderer_name}.")

def get_logger(name=None):
    """Gets a structlog logger, optionally named."""
    return structlog.get_logger(name)

# --- Example Usage (in other modules) ---
# from app.utils.logging_config import get_logger
# log = get_logger(__name__) # Get logger named after the module
#
# def some_function(user_id):
#     log.info("Processing request for user", user_id=user_id, extra_data="foo")
#     try:
#         result = 1 / 0
#     except Exception as e:
#         log.error("An error occurred", error=str(e), exc_info=True) # exc_info adds traceback