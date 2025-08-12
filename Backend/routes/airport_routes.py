"""
Airport API Routes

This module contains routes for airport-related functionalities,
including autocomplete search.
"""
import logging
import hashlib
from quart import Blueprint, request, jsonify
from quart_cors import cors, route_cors  # Import cors and route_cors

# Adjust import path if necessary, assuming services is a package in Backend
from services.flight.airport_service import AirportService
from services.redis_flight_storage import redis_flight_storage

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

def _generate_airport_cache_key(query: str, search_by: str) -> str:
    """Generate a deterministic cache key for airport search parameters."""
    normalized_params = {
        'query': query.lower().strip(),
        'search_by': search_by.lower().strip()
    }
    
    param_string = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_params.items()) if v)
    cache_key = hashlib.md5(param_string.encode()).hexdigest()
    
    logger.debug(f"Generated airport cache key: {cache_key} for query: {query}")
    return f"airport_search:{cache_key}"

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
        # Generate cache key for this airport search
        cache_key = _generate_airport_cache_key(query, search_by)
        
        # Check if we have cached results first
        cached_result = redis_flight_storage.get_flight_search(cache_key)
        
        if cached_result['success']:
            logger.info(f"🚀 Airport search cache hit for query '{query}' - returning cached results")
            
            # Return cached data with proper response structure
            cached_data = cached_result['data']
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_data.get('results', []),
                'cached_at': cached_result['stored_at'],
                'expires_at': cached_result['expires_at']
            }), 200
        
        # Cache miss - search airports using the service
        logger.info(f"🔍 Airport search cache miss for query '{query}' - searching airports")
        results = airport_service.search_airports(query=query, search_by=search_by)
        
        # Cache the successful results for future requests
        if results:
            try:
                search_data = {
                    'results': results,
                    'query': query,
                    'search_by': search_by,
                    'total_results': len(results)
                }
                
                cache_result = redis_flight_storage.store_flight_search(
                    search_data=search_data,
                    session_id=cache_key,
                    ttl=3600  # 1 hour for airport data (static data, can cache longer)
                )
                
                if cache_result['success']:
                    logger.info(f"💾 Cached airport search results for query '{query}' - {len(results)} results")
                else:
                    logger.warning(f"Failed to cache airport search results: {cache_result.get('message')}")
                    
            except Exception as cache_error:
                logger.error(f"Error caching airport search results: {str(cache_error)}")
        
        logger.info(f"Found {len(results)} airports for query '{query}' by '{search_by}'.")
        return jsonify({
            'status': 'success',
            'data': results,
            'cached': True if results else False
        }), 200
    except Exception as e:
        logger.error(f"Error during airport autocomplete search: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred while searching for airports.'
        }), 500