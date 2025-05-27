"""
Flight Booking Portal Backend

This module initializes the Flask application and sets up the API routes.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

def create_app(test_config=None):
    """Create and configure the Flask application."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure the app
    app.config.from_mapping(
        # Flask settings
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production'),
        DEBUG=os.environ.get('FLASK_ENV') == 'development',
        TESTING=False,
        
        # API settings
        API_PREFIX='/api',
        
        # Verteil NDC API settings
        VERTEIL_API_BASE_URL=os.environ.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com'),
        VERTEIL_USERNAME=os.environ.get('VERTEIL_USERNAME'),
        VERTEIL_PASSWORD=os.environ.get('VERTEIL_PASSWORD'),
        VERTEIL_TOKEN_ENDPOINT=os.environ.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
        VERTEIL_OFFICE_ID=os.environ.get('VERTEIL_OFFICE_ID', 'OFF3748'),
        VERTEIL_THIRD_PARTY_ID=os.environ.get('VERTEIL_THIRD_PARTY_ID', 'WY'),
        
        # Request timeout in seconds
        REQUEST_TIMEOUT=30,
        
        # OAuth2 Settings
        OAUTH2_TOKEN_EXPIRY_BUFFER=60,
        
        # Logging
        LOG_LEVEL=os.environ.get('LOG_LEVEL', 'INFO'),
        LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Register blueprints
    from .routes import verteil_flights
    app.register_blueprint(verteil_flights.bp)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy"}), 200
    
    return app

# Create the application
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

# Import routes at the bottom to avoid circular imports
from . import routes
