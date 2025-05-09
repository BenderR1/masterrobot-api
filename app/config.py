# app/config.py
import os
from dotenv import load_dotenv

# Load .env file from the parent directory of the 'app' package
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Config:
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Database
    # Construct absolute path for SQLite relative to project root
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data", "master_robot.db")}')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-dev-jwt-secret')
    # Add other JWT settings like expiration time if needed
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # LLM API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Add other application-specific config
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads') # Example

class TestConfig(Config):
    TESTING = True
    # Use an in-memory SQLite database for tests or a separate file
    DATABASE_URL = 'sqlite:///:memory:'
    # DATABASE_URL = f'sqlite:///{os.path.join(Config.BASE_DIR, "data", "test_master_robot.db")}'
    SECRET_KEY = 'test-secret'
    JWT_SECRET_KEY = 'test-jwt-secret'
    LOG_LEVEL = 'DEBUG' # Often useful to see debug logs during tests