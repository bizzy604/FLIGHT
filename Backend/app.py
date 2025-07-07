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
import logging # Added for explicit logger configuration

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_app(test_config=None):
    """Create and configure the Quart application."""
    app = Quart(__name__)

    # Increase maximum request size for large flight data (100MB)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

    # Load environment variables from .env file
    load_dotenv()
    
    # Load configuration
    from Backend.config import get_config
    env = os.environ.get('QUART_ENV', 'development')
    config = get_config(env)
    app.config.from_object(config)
    app.config.from_envvar('QUART_CONFIG', silent=True)
    
    # Initialize config if it has an init_app method
    if hasattr(config, 'init_app'):
        config.init_app(app)
    
    # Configure CORS - Let the route-level CORS handle it
    # The @route_cors decorator on individual routes will handle CORS
    
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
        OAUTH2_TOKEN_EXPIRY_BUFFER=60,  # seconds before actual expiry to consider token expired (1 minute buffer for 11-hour tokens)
        LOG_LEVEL=os.environ.get('LOG_LEVEL', 'INFO'),
        LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure specific logger for FlightService
    service_logger = logging.getLogger('services.flight.core')
    service_logger.setLevel(app.config.get('LOG_LEVEL', 'INFO'))
    # If Quart's default handler isn't picked up, add one:
    if not service_logger.hasHandlers() and app.logger.hasHandlers():
        for handler in app.logger.handlers:
            service_logger.addHandler(handler)
    # Configure specific logger for FlightSearchService (search.py)
    search_service_logger = logging.getLogger('services.flight.search')
    search_service_logger.setLevel(app.config.get('LOG_LEVEL', 'INFO'))
    if not search_service_logger.hasHandlers() and app.logger.hasHandlers():
        for handler in app.logger.handlers:
            search_service_logger.addHandler(handler)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Import and register blueprints
    from routes import verteil_flights, debug
    from routes.airport_routes import airport_bp # Import the new airport blueprint
    from routes.itinerary_routes import itinerary_bp # Import the new itinerary blueprint
    from routes.flight_storage import flight_storage_bp # Import the flight storage blueprint

    # Initialize routes with app
    verteil_flights.init_app(app)

    # Register blueprints
    app.register_blueprint(verteil_flights.bp)
    app.register_blueprint(debug.bp)
    app.register_blueprint(airport_bp)  # Register the airport blueprint (prefix is in blueprint definition)
    app.register_blueprint(itinerary_bp)  # Register the itinerary blueprint
    app.register_blueprint(flight_storage_bp)  # Register the flight storage blueprint

    # Initialize centralized authentication
    @app.before_serving
    async def initialize_auth():
        """Initialize the centralized TokenManager with app configuration."""
        from utils.auth import TokenManager

        # Get the singleton TokenManager instance
        token_manager = TokenManager.get_instance()

        # Configure it once with the app configuration
        auth_config = {
            'VERTEIL_API_BASE_URL': app.config.get('VERTEIL_API_BASE_URL'),
            'VERTEIL_TOKEN_ENDPOINT': app.config.get('VERTEIL_TOKEN_ENDPOINT') or app.config.get('VERTEIL_TOKEN_ENDPOINT_PATH', '/oauth2/token'),
            'VERTEIL_USERNAME': app.config.get('VERTEIL_USERNAME'),
            'VERTEIL_PASSWORD': app.config.get('VERTEIL_PASSWORD'),
            'VERTEIL_THIRD_PARTY_ID': app.config.get('VERTEIL_THIRD_PARTY_ID'),
            'VERTEIL_OFFICE_ID': app.config.get('VERTEIL_OFFICE_ID'),
            'OAUTH2_TOKEN_EXPIRY_BUFFER': app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 60)
        }

        token_manager.set_config(auth_config)
        app.logger.info("Centralized TokenManager initialized with app configuration")

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
    # Configure logging to reduce verbosity
    import logging
    import os
    
    # Set environment variable to disable asyncio debug mode
    os.environ['PYTHONASYNCIODEBUG'] = '0'
    
    # Configure root logger to reduce noise
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Suppress specific loggers that cause repetitive output
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('quart.serving').setLevel(logging.INFO)
    logging.getLogger('quart.utils').setLevel(logging.ERROR)
    
    # Run with Hypercorn server for async support
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

# Import routes at the bottom to avoid circular imports
# from . import routes
