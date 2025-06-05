"""
Verteil NDC API integration routes.

This module contains routes for interacting with the Verteil NDC API.
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional

from quart import Blueprint, request, jsonify, current_app, make_response
from quart_cors import cors

# Import from the new modular flight service
from services.flight import (
    FlightServiceError,
    search_flights,
    get_flight_price as get_flight_price_service,
    create_booking,
    process_air_shopping,
    process_order_create,
    process_flight_price
)

# Configure logging
logger = logging.getLogger(__name__)

# Create a Blueprint for Verteil flight routes
bp = Blueprint('verteil_flights', __name__, url_prefix='/api/verteil')

def _add_cors_headers(response):
    """Add CORS headers to the response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@bp.after_request
async def after_request(response):
    """Add CORS headers to all responses."""
    return _add_cors_headers(response)

@bp.before_request
async def handle_preflight():
    """Handle CORS preflight requests."""
    if request.method == "OPTIONS":
        response = await make_response()
        return _add_cors_headers(response)

def _get_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def _create_error_response(
    message: str,
    status_code: int = 400,
    request_id: Optional[str] = None,
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        request_id: Optional request ID for correlation
        details: Additional error details
        
    Returns:
        dict: Standardized error response
    """
    response = {
        'status': 'error',
        'message': message,
        'request_id': request_id or _get_request_id()
    }
    if details:
        response['details'] = details
    return response

@bp.route('/air-shopping', methods=['GET', 'POST', 'OPTIONS'])
async def air_shopping():
    """
    Handle flight search requests with caching and rate limiting.
    
    Accepts both GET and POST requests with different parameter formats:
    
    GET Parameters:
    - origin: Origin airport code (e.g., 'LHR')
    - destination: Destination airport code (e.g., 'BOM')
    - departDate: Departure date in YYYY-MM-DD format
    - [returnDate]: Return date for round trips (optional)
    - adults: Number of adult passengers (1-9)
    - [children]: Number of child passengers (0-8, default: 0)
    - [infants]: Number of infant passengers (0-8, default: 0)
    - [cabinClass]: Cabin class preference (Y, W, C, F)
    - [tripType]: Type of trip ('one-way' or 'round-trip')
    
    POST JSON Body:
    - tripType: Type of trip (ONE_WAY, ROUND_TRIP, MULTI_CITY)
    - odSegments: List of origin-destination segments with:
        - origin: Origin airport code (e.g., 'JFK')
        - destination: Destination airport code (e.g., 'LAX')
        - departureDate: Departure date in YYYY-MM-DD format
        - [returnDate]: Return date for round trips (optional)
    - numAdults: Number of adult passengers (1-9)
    - [numChildren]: Number of child passengers (0-8, default: 0)
    - [numInfants]: Number of infant passengers (0-8, default: 0)
    - [cabinPreference]: Cabin class preference (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
    - [directOnly]: Boolean to show only direct flights (default: false)
    """
    if request.method == 'OPTIONS':
        response = await make_response()
        return _add_cors_headers(response)
        
    request_id = _get_request_id()
    
    try:
        # Parse request data based on method
        if request.method == 'GET':
            args = request.args
            origin = args.get('origin')
            destination = args.get('destination')
            depart_date = args.get('departDate')
            
            if not all([origin, destination, depart_date]):
                error_msg = "Missing required parameters: origin, destination, and departDate are required"
                logger.warning(f"{error_msg} - Request ID: {request_id}")
                return jsonify(_create_error_response(error_msg, 400, request_id))
                
            # Map cabin class codes to full names
            cabin_map = {
                'Y': 'ECONOMY',
                'W': 'PREMIUM_ECONOMY',
                'C': 'BUSINESS',
                'F': 'FIRST'
            }
            
            cabin_class = args.get('cabinClass', 'Y')
            cabin_preference = cabin_map.get(cabin_class.upper(), 'ECONOMY')
            
            # Create odSegments from GET params
            od_segments = [{
                'origin': origin.upper(),
                'destination': destination.upper(),
                'departureDate': depart_date
            }]
            
            # Add return segment if round trip
            if args.get('tripType', '').lower() == 'round-trip' and args.get('returnDate'):
                od_segments.append({
                    'origin': destination.upper(),
                    'destination': origin.upper(),
                    'departureDate': args['returnDate']
                })
            
            search_criteria = {
                'tripType': 'ROUND_TRIP' if args.get('tripType', '').lower() == 'round-trip' else 'ONE_WAY',
                'odSegments': od_segments,
                'numAdults': int(args.get('adults', 1)),
                'numChildren': int(args.get('children', 0)),
                'numInfants': int(args.get('infants', 0)),
                'cabinPreference': cabin_preference,
                'directOnly': False,
                'request_id': request_id
            }
        else:  # POST
            data = await request.get_json()
            logger.info(f"Air shopping request received - Request ID: {request_id}")
            
            # Basic validation for POST
            required_fields = ['tripType', 'odSegments', 'numAdults']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.warning(f"{error_msg} - Request ID: {request_id}")
                return jsonify(_create_error_response(error_msg, 400, request_id))
            
            od_segments = data['odSegments']
            if not isinstance(od_segments, list) or not od_segments:
                error_msg = "odSegments must be a non-empty list"
                logger.warning(f"{error_msg} - Request ID: {request_id}")
                return jsonify(_create_error_response(error_msg, 400, request_id))
            
            num_adults = int(data['numAdults'])
            if num_adults < 1 or num_adults > 9:
                error_msg = "Number of adults must be between 1 and 9"
                logger.warning(f"{error_msg} - Request ID: {request_id}")
                return jsonify(_create_error_response(error_msg, 400, request_id))
            
            search_criteria = {
                'tripType': data['tripType'],
                'odSegments': od_segments,
                'numAdults': num_adults,
                'numChildren': int(data.get('numChildren', 0)),
                'numInfants': int(data.get('numInfants', 0)),
                'cabinPreference': data.get('cabinPreference', 'ECONOMY'),
                'directOnly': bool(data.get('directOnly', False)),
                'request_id': request_id
            }
        result = await process_air_shopping(search_criteria)
        
        logger.info(f"Air shopping request completed - Request ID: {request_id}")
        return jsonify({
            'status': 'success',
            'data': result,
            'request_id': request_id
        })
        
    except json.JSONDecodeError:
        error_msg = "Invalid JSON payload"
        logger.error(f"{error_msg} - Request ID: {request_id}")
        return jsonify(_create_error_response(error_msg, 400, request_id))
    except ValueError as e:
        logger.error(f"Validation error: {str(e)} - Request ID: {request_id}")
        return jsonify(_create_error_response(str(e), 400, request_id))
    except FlightServiceError as e:
        logger.error(f"Flight service error: {str(e)} - Request ID: {request_id}")
        return jsonify(_create_error_response(str(e), 500, request_id, e.details if hasattr(e, 'details') else None))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response("An unexpected error occurred", 500, request_id))

@bp.route('/flight-price', methods=['POST', 'OPTIONS'])
async def flight_price():
    """
    Handle flight price requests.
    
    POST JSON Body:
    - offer_id: The ID of the offer to price
    - shopping_response_id: The ShoppingResponseID from AirShoppingRS
    - air_shopping_rs: The AirShopping response containing offer details
    - [currency]: Currency code (default: USD)
    
    Returns:
    - Pricing details for the selected flight offer
    """
    if request.method == 'OPTIONS':
        response = await make_response()
        return _add_cors_headers(response)
        
    request_id = _get_request_id()
    
    try:
        data = await request.get_json()
        logger.info(f"Flight price request received - Request ID: {request_id}")
        
        # Validate required fields
        required_fields = ['offer_id', 'shopping_response_id', 'air_shopping_rs']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.warning(f"{error_msg} - Request ID: {request_id}")
            return jsonify(_create_error_response(error_msg, 400, request_id))
        
        # Prepare request data
        price_request = {
            'offer_id': data['offer_id'],
            'shopping_response_id': data['shopping_response_id'],
            'air_shopping_response': data['air_shopping_rs'],
            'currency': data.get('currency', 'USD'),
            'request_id': request_id
        }
        
        # Process the flight price request
        result = await process_flight_price(price_request)
        
        logger.info(f"Flight price request completed - Request ID: {request_id}")
        return jsonify({
            'status': 'success',
            'data': result,
            'request_id': request_id
        })
        
    except json.JSONDecodeError:
        error_msg = "Invalid JSON payload"
        logger.error(f"{error_msg} - Request ID: {request_id}")
        return jsonify(_create_error_response(error_msg, 400, request_id))
    except ValueError as e:
        logger.error(f"Validation error: {str(e)} - Request ID: {request_id}")
        return jsonify(_create_error_response(str(e), 400, request_id))
    except FlightServiceError as e:
        logger.error(f"Flight service error: {str(e)} - Request ID: {request_id}")
        return jsonify(_create_error_response(str(e), 500, request_id, e.details if hasattr(e, 'details') else None))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response("An unexpected error occurred", 500, request_id))
