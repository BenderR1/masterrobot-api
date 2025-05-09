# app/wsgi.py
from app import create_app
import os

# Create app instance using config based on FLASK_ENV or default
# This ensures Gunicorn uses the correct config (e.g., production)
# You might need to adjust Config class selection based on your deployment strategy
app = create_app()

if __name__ == "__main__":
    # For local development using 'python app/wsgi.py'
    # Gunicorn should be used for production/staging
    print("Running Flask development server...")
    app.run(host='0.0.0.0', port=5000) # Debug is controlled by FLASK_ENV in Config