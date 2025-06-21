"""
WSGI config for the Flight Booking Backend.

This module contains the WSGI application used by the production server.
"""
import os
import sys

# Add the project directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the application factory function
from Backend.app import create_app

# Create the application instance
app = create_app()

# Ensure the app can be imported by Gunicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # This is used when running locally
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
