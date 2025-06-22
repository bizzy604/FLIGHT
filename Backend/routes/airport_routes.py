"""
Airport API Routes

This module contains routes for airport-related functionalities,
including autocomplete search.
"""
import logging
from quart import Blueprint, request, jsonify
from quart_cors import cors, route_cors  # Import cors and route_cors

# Adjust import path if necessary, assuming services is a package in Backend
from services.flight.airport_service import AirportService

logger = logging.getLogger(__name__)

# Create a Blueprint for airport routes
airport_bp = Blueprint('airport_routes', __name__, url_prefix='/api/airports')

# Initialize AirportService
airport_service = AirportService()

# CORS configuration
cors_config = {
    "allow_origin": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    "allow_headers": ["Content-Type", "Authorization", "X-Request-Timestamp"],
    "allow_methods": ["GET", "OPTIONS"],
    "allow_credentials": True,
    "expose_headers": ["Content-Type", "Authorization", "X-Request-Timestamp"]
}

# Apply CORS to all routes in this blueprint
airport_bp = cors(airport_bp, **cors_config)

@airport_bp.route('/autocomplete', methods=['GET', 'OPTIONS'])
async def airport_autocomplete():
    """
    Provides airport autocomplete suggestions based on a query.

    Query Parameters:
        query (str): The search term (e.g., city name or partial airport name).
        search_by (str, optional): Field to search by ('city' or 'airport_name'). 
                                   Defaults to 'city'.
    Returns:
        JSON response with a list of matching airports or an error message.
    """
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS preflight request for /autocomplete")
        return jsonify({}), 200 # Respond to OPTIONS preflight

    query = request.args.get('query', type=str)
    search_by = request.args.get('search_by', default='city', type=str)

    logger.info(f"Airport autocomplete request received. Query: '{query}', Search by: '{search_by}'")

    if not query or len(query.strip()) < 2: # Require at least 2 characters for a meaningful search
        logger.warning("Autocomplete query too short or missing.")
        return jsonify({
            'status': 'error',
            'message': 'Query parameter is required and must be at least 2 characters long.'
        }), 400

    if search_by not in ['city', 'airport_name']:
        logger.warning(f"Invalid search_by parameter: {search_by}. Defaulting to 'city'.")
        search_by = 'city' # Default to city if invalid parameter is provided

    try:
        results = airport_service.search_airports(query=query, search_by=search_by)
        logger.info(f"Found {len(results)} airports for query '{query}' by '{search_by}'.")
        return jsonify({
            'status': 'success',
            'data': results
        }), 200
    except Exception as e:
        logger.error(f"Error during airport autocomplete search: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred while searching for airports.'
        }), 500