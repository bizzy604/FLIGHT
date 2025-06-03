"""
Flight Booking Portal Backend

This module initializes the Quart application and sets up the API routes.
"""
import os
import sys
from quart import Quart, jsonify, request, make_response, current_app
from quart_cors import cors
from dotenv import load_dotenv
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_app(test_config=None):
    """Create and configure the Quart application."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Create and configure the app
    app = Quart(__name__, instance_relative_config=True)
    
    # Configure CORS to allow requests from the frontend
    app.config['CORS_ORIGINS'] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.config['CORS_ALLOW_HEADERS'] = ["Content-Type", "Authorization"]
    app.config['CORS_METHODS'] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    app.config['CORS_EXPOSE_HEADERS'] = ["Content-Type"]
    
    # Enable CORS for all routes
    app = cors(app, allow_origin=app.config['CORS_ORIGINS'], 
              allow_headers=app.config['CORS_ALLOW_HEADERS'],
              allow_methods=app.config['CORS_METHODS'],
              expose_headers=app.config['CORS_EXPOSE_HEADERS'])
    
    # Load configuration from config.py
    from Backend.config import Config
    app.config.from_object(Config)
    
    # Load the instance config, if it exists, when not testing
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Set additional configuration
    app.config.update(
        REQUEST_TIMEOUT=30,
        OAUTH2_TOKEN_EXPIRY_BUFFER=60,  # seconds before actual expiry to consider token expired
        LOG_LEVEL=os.environ.get('LOG_LEVEL', 'INFO'),
        LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Import and register blueprints
    from routes import verteil_flights, debug
    
    # Register the blueprints with their respective URL prefixes
    app.register_blueprint(verteil_flights.bp)  # Uses the URL prefix defined in the blueprint
    app.register_blueprint(debug.debug_bp, url_prefix='/')
    
    # Log registered routes for debugging
    @app.before_serving
    async def log_routes():
        # Log all registered routes
        for rule in app.url_map.iter_rules():
            app.logger.info(f"Route: {rule.endpoint} -> {rule.rule}")
    
    # Add error handler for 404
    @app.errorhandler(404)
    async def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'The requested resource was not found.',
            'error': str(error)
        }), 404
        
    # Add error handler for 500
    @app.errorhandler(500)
    async def server_error(error):
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred.',
            'error': str(error) if app.debug else 'Internal Server Error'
        }), 500
    
    # Health check endpoint
    @app.route('/api/health')
    async def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy"}), 200
        
    # Debug endpoint to list all routes
    @app.route('/api/debug/routes')
    async def list_routes():
        """List all registered routes."""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': sorted(rule.methods),
                'path': str(rule)
            })
        return jsonify(routes)
    
    return app

# Create the application
app = create_app()

if __name__ == '__main__':
    # Run with Hypercorn server for async support
    app.run(host='0.0.0.0', port=5000, debug=True)

# Import routes at the bottom to avoid circular imports
# from . import routes
