"""
Verteil NDC API integration routes.

This module contains routes for interacting with the Verteil NDC API.
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from quart import Blueprint, request, jsonify, current_app, make_response
from quart_cors import cors, route_cors
from functools import wraps
import time
from collections import OrderedDict

# Simple in-memory request deduplication cache
class RequestDeduplicationCache:
    def __init__(self, max_size=100, ttl=5):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl  # seconds
    
    def _cleanup(self):
        current_time = time.time()
        # Remove expired entries
        expired_keys = [k for k, (_, timestamp) in self.cache.items() 
                      if current_time - timestamp > self.ttl]
        for k in expired_keys:
            self.cache.pop(k, None)
        
        # Trim to max size if needed
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def add_request(self, key):
        self._cleanup()
        current_time = time.time()
        self.cache[key] = (current_time, current_time)
    
    def is_duplicate(self, key):
        self._cleanup()
        return key in self.cache

# Initialize request deduplication cache
request_cache = RequestDeduplicationCache(max_size=1000, ttl=2)  # 2 second TTL - reduced from 5 to improve UX

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

def handle_cors(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = await make_response()
            response.headers.add('Access-Control-Allow-Origin', ', '.join(current_app.config['CORS_ORIGINS']))
            response.headers.add('Access-Control-Allow-Headers', ', '.join(current_app.config['CORS_ALLOW_HEADERS']))
            response.headers.add('Access-Control-Allow-Methods', ', '.join(current_app.config['CORS_METHODS']))
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
        return await f(*args, **kwargs)
    return decorated_function

# Create a Blueprint for Verteil flight routes
bp = Blueprint('verteil_flights', __name__, url_prefix='/api/verteil')

# Apply CORS to all routes in this blueprint
bp = cors(
    bp,
    allow_origin=current_app.config['CORS_ORIGINS'] if 'CORS_ORIGINS' in current_app.config else ["*"],
    allow_headers=current_app.config.get('CORS_ALLOW_HEADERS', ["Content-Type", "Authorization"]),
    allow_methods=current_app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
    expose_headers=current_app.config.get('CORS_EXPOSE_HEADERS', ["Content-Type"]),
    allow_credentials=current_app.config.get('CORS_SUPPORTS_CREDENTIALS', True)
)

# For debugging, allow all origins temporarily
ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]

# Enable CORS for all routes in this blueprint with specific options
bp = cors(
    bp,
    allow_origin=ALLOWED_ORIGINS,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    allow_methods=["GET", "POST"],
    expose_headers=["Content-Type"],
    max_age=600,
    allow_credentials=True
)

# Add request logging
@bp.before_request
async def log_request():
    logger.info(f"Incoming request: {request.method} {request.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Origin: {request.headers.get('Origin')}")
    logger.info(f"Access-Control-Request-Method: {request.headers.get('Access-Control-Request-Method')}")

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
@handle_cors
@route_cors(allow_origin=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"], 
           allow_headers=["Content-Type", "Authorization", "X-Requested-With"], 
           allow_methods=["GET", "POST", "OPTIONS"],
           allow_credentials=True)
async def air_shopping():
    """
    Handle flight search requests with caching and advanced filtering capabilities.
    
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
    - [minPrice]: Minimum price filter (optional)
    - [maxPrice]: Maximum price filter (optional)
    - [airlines]: Comma-separated airline codes to filter by (optional)
    - [maxStops]: Maximum number of stops (0, 1, 2+) (optional)
    - [departTimeMin]: Minimum departure time in HH:MM format (optional)
    - [departTimeMax]: Maximum departure time in HH:MM format (optional)
    - [enableRoundtrip]: Boolean to enable round trip transformation (default: false)
    
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
    - [filters]: Advanced filtering options (optional)
    - [sortBy]: Sorting preference ('price', 'duration', 'departure', 'arrival', 'stops')
    - [sortOrder]: Sort order ('asc' or 'desc') (default: 'asc')
    - [enableRoundtrip]: Boolean to enable round trip transformation (default: false)
    
    Returns:
    - Flight search results with enhanced filtering and sorting
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        logger.info("Handling OPTIONS preflight request")
        return await make_response(), 200
        
    request_id = _get_request_id()
    logger.info(f"Air shopping request received - Request ID: {request_id}")
    
    # Create a fingerprint of the request to detect duplicates
    request_data = await request.get_data()
    request_fingerprint = f"{request.remote_addr}:{request.path}:{request_data.decode()}"
    
    # Check for duplicate request (skip for OPTIONS)
    if request.method != 'OPTIONS' and request_cache.is_duplicate(request_fingerprint):
        logger.warning(f"Duplicate request detected - Request ID: {request_id}")
        return jsonify({
            'status': 'error',
            'message': 'Duplicate request detected. Please wait a moment and try again.',
            'request_id': request_id
        }), 429  # Too Many Requests
    
    # Add to cache (skip for OPTIONS)
    if request.method != 'OPTIONS':
        request_cache.add_request(request_fingerprint)
    
    try:
        # Get request data based on method
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            data = await request.get_json() or {}
            
        # Early logging to debug the issue
        logger.info(f"[DEBUG] Request method: {request.method}")
        logger.info(f"[DEBUG] Raw request data: {data}")
            
        # Convert frontend parameter names to backend equivalents
        parameter_mapping = {
            'tripType': 'trip_type',
            'numAdults': 'num_adults',
            'numChildren': 'num_children',
            'numInfants': 'num_infants',
            'cabinClass': 'cabin_class',
            'outboundCabinClass': 'outbound_cabin_class',
            'returnCabinClass': 'return_cabin_class',
            'departDate': 'departure_date',
            'returnDate': 'return_date',
            'originCode': 'origin_code',
            'destinationCode': 'destination_code',
            'adults': 'num_adults',
            'children': 'num_children',
            'infants': 'num_infants'
        }
        
        # Apply parameter mapping
        converted_data = {}
        for key, value in data.items():
            # Use mapped key if it exists, otherwise use original key
            mapped_key = parameter_mapping.get(key, key)
            converted_data[mapped_key] = value
            
        # Build odSegments from individual parameters if not already present
        if 'odSegments' not in converted_data and 'origin' in converted_data and 'destination' in converted_data:
            od_segments = []
            
            # Add outbound segment
            departure_date = converted_data.get('departure_date') or converted_data.get('departDate')
            if converted_data.get('origin') and converted_data.get('destination') and departure_date:
                od_segments.append({
                    'origin': converted_data['origin'],
                    'destination': converted_data['destination'],
                    'departureDate': departure_date
                })
            
            # Add return segment for round-trip
            trip_type = converted_data.get('trip_type', '').lower()
            if (trip_type in ['round-trip', 'round_trip', 'roundtrip'] and 
                converted_data.get('returnDate')):
                od_segments.append({
                    'origin': converted_data['destination'],
                    'destination': converted_data['origin'],
                    'departureDate': converted_data['returnDate']
                })
            
            # Add odSegments to converted_data
            if od_segments:
                converted_data['odSegments'] = od_segments
        
        # Handle case where odSegments are already present but need processing for round trips
        elif 'odSegments' in converted_data:
            trip_type = converted_data.get('trip_type', '').upper()
            if trip_type == 'ROUND_TRIP' and len(converted_data['odSegments']) == 1:
                # Check if the single segment has a returnDate (frontend format)
                segment = converted_data['odSegments'][0]
                if 'returnDate' in segment:
                    # Split into two segments
                    outbound_segment = {
                        'origin': segment['origin'],
                        'destination': segment['destination'],
                        'departureDate': segment['departureDate']
                    }
                    return_segment = {
                        'origin': segment['destination'],
                        'destination': segment['origin'],
                        'departureDate': segment['returnDate']
                    }
                    converted_data['odSegments'] = [outbound_segment, return_segment]
                    logger.info(f"[DEBUG] Split round trip segment into two: {converted_data['odSegments']}")
        
        # Convert cabin class codes to preference names
        cabin_code_mapping = {
            'Y': 'ECONOMY',
            'W': 'PREMIUM_ECONOMY', 
            'C': 'BUSINESS',
            'F': 'FIRST'
        }
        
        # Handle separate cabin classes for round trips
        if converted_data.get('trip_type') == 'ROUND_TRIP' and 'outbound_cabin_class' in converted_data and 'return_cabin_class' in converted_data:
            outbound_cabin = converted_data['outbound_cabin_class']
            return_cabin = converted_data['return_cabin_class']
            
            # Set cabin preferences for each segment
            if 'odSegments' in converted_data and len(converted_data['odSegments']) == 2:
                converted_data['odSegments'][0]['cabinPreference'] = cabin_code_mapping.get(outbound_cabin, 'ECONOMY')
                converted_data['odSegments'][1]['cabinPreference'] = cabin_code_mapping.get(return_cabin, 'ECONOMY')
                logger.info(f"[DEBUG] Mapped outbound cabin {outbound_cabin} to {converted_data['odSegments'][0]['cabinPreference']}")
                logger.info(f"[DEBUG] Mapped return cabin {return_cabin} to {converted_data['odSegments'][1]['cabinPreference']}")
                # Remove global cabin preference to avoid conflicts
                converted_data.pop('cabinPreference', None)
        elif 'cabin_class' in converted_data:
            # Handle single cabin class for one-way trips
            cabin_code = converted_data['cabin_class']
            converted_data['cabinPreference'] = cabin_code_mapping.get(cabin_code, 'ECONOMY')
            logger.info(f"[DEBUG] Mapped cabin class {cabin_code} to {converted_data['cabinPreference']}")
            
        # Log the incoming request for debugging
        logger.info(f"Original request data: {data}")
        logger.info(f"Converted request data: {converted_data}")
        
        # Process the request with the flight service
        # Add configuration to the request data
        converted_data['config'] = dict(current_app.config)
        result = await process_air_shopping(converted_data)
        
        # Log success
        logger.info(f"Successfully processed air shopping request - Request ID: {request_id}")
        
        # Return the result
        response = jsonify({
            'status': 'success',
            'data': result,
            'request_id': request_id
        })
        
        return response
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in request: {str(e)}"
        logger.error(f"{error_msg} - Request ID: {request_id}")
        return jsonify(_create_error_response(
            message="Invalid JSON in request body",
            status_code=400,
            request_id=request_id,
            details={"error": str(e)}
        )), 400
        
    except FlightServiceError as e:
        error_msg = f"Flight service error: {str(e)}"
        logger.error(f"{error_msg} - Request ID: {request_id}")
        return jsonify(_create_error_response(
            message=str(e),
            status_code=getattr(e, 'status_code', 500),
            request_id=request_id,
            details=getattr(e, 'details', None)
        )), getattr(e, 'status_code', 500)
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"{error_msg} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(
            message="An unexpected error occurred",
            status_code=500,
            request_id=request_id,
            details={"error": str(e) if str(e) else "Unknown error"}
        )), 500

@bp.route('/flight-price', methods=['POST', 'OPTIONS'])
@handle_cors
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
        
    request_id = _get_request_id()
    
    try:
        data = await request.get_json()
        logger.info(f"Flight price request received - Request ID: {request_id}")
        
        # Check if data is None (invalid JSON or missing content-type)
        if data is None:
            error_msg = "Invalid request: No JSON data received. Please check Content-Type header and request body."
            logger.error(f"{error_msg} - Request ID: {request_id}")
            return jsonify(_create_error_response(error_msg, 400, request_id))
        
        logger.info(f"Request data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'} - Request ID: {request_id}")
        
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
            'request_id': request_id,
            'config': dict(current_app.config)  # Pass the app configuration
        }
        
        # Process the flight price request
        result = await process_flight_price(price_request)
        
        logger.info(f"Flight price request completed - Request ID: {request_id}")
        return jsonify(result)
        
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


@bp.route('/order-create', methods=['POST', 'OPTIONS'])
@handle_cors
async def create_order():
    """
    Create a new flight booking order.
    
    Expected JSON payload:
    {
        "flight_price_response": {...},  # Direct flight price response from frontend
        "passengers": [...],    # Passenger details from frontend
        "payment": {...},       # Payment information
        "contact_info": {...}   # Contact information
    }
    """
    request_id = _get_request_id()
    
    try:
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("Request body is required", 400, request_id))
        
        # DEBUG: Log raw frontend data
        logger.info(f"[DEBUG] Raw frontend data received (ReqID: {request_id}):")
        logger.info(f"[DEBUG] Full request payload: {json.dumps(data, indent=2, default=str)}")
        
        # Extract data from frontend request
        flight_price_response = data.get('flight_price_response')  # Direct flight price response from frontend
        frontend_passengers = data.get('passengers', [])
        payment_info = data.get('payment', {})
        contact_info = data.get('contact_info', {})
        offer_id = data.get('OfferID')  # Extract OfferID sent from frontend
        shopping_response_id = data.get('ShoppingResponseID')  # Extract ShoppingResponseID sent from frontend
        
        # DEBUG: Log extracted data components
        logger.info(f"[DEBUG] Extracted flight_price_response present (ReqID: {request_id}): {bool(flight_price_response)}")
        if flight_price_response:
            logger.info(f"[DEBUG] Flight price response keys (ReqID: {request_id}): {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
        logger.info(f"[DEBUG] Extracted passengers (ReqID: {request_id}): {json.dumps(frontend_passengers, indent=2, default=str)}")
        logger.info(f"[DEBUG] Extracted payment (ReqID: {request_id}): {json.dumps(payment_info, indent=2, default=str)}")
        logger.info(f"[DEBUG] Extracted contact_info (ReqID: {request_id}): {json.dumps(contact_info, indent=2, default=str)}")
        logger.info(f"[DEBUG] Extracted OfferID (ReqID: {request_id}): {offer_id}")
        logger.info(f"[DEBUG] Extracted ShoppingResponseID (ReqID: {request_id}): {shopping_response_id}")
        
        # Validate required data
        if not flight_price_response:
            error_msg = "Flight price response is required. Please ensure the flight price response is included in the request."
            return jsonify(_create_error_response(error_msg, 400, request_id))
        
        if not frontend_passengers:
            return jsonify(_create_error_response("At least one passenger is required", 400, request_id))
        
        if not payment_info:
            return jsonify(_create_error_response("Payment information is required", 400, request_id))
        
        if not contact_info or not contact_info.get('email'):
            return jsonify(_create_error_response("Contact information with email is required", 400, request_id))
        
        # Prepare order data for the booking service (pass raw frontend data)
        order_data = {
            'flight_price_response': flight_price_response,  # Consistent naming throughout backend
            'passengers': frontend_passengers,  # Pass raw frontend passenger data
            'payment_info': payment_info,
            'contact_info': contact_info,
            'request_id': request_id,
            'config': dict(current_app.config),  # Pass the app configuration
            'offer_id': offer_id,  # Pass the extracted OfferID
            'shopping_response_id': shopping_response_id  # Pass the extracted ShoppingResponseID
        }
        
        # DEBUG: Log order data being sent to booking service
        logger.info(f"[DEBUG] Order data being sent to booking service (ReqID: {request_id}): {json.dumps(order_data, indent=2, default=str)}")
        
        logger.info(f"Processing order creation - Request ID: {request_id}")
        
        # Call the booking service
        result = await process_order_create(order_data)
        
        if result.get('status') == 'success':
            logger.info(f"Order created successfully - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': result.get('data', {}),
                'request_id': request_id
            })
        else:
            logger.error(f"Order creation failed - Request ID: {request_id}, Error: {result.get('error')}")
            return jsonify(_create_error_response(
                result.get('error', 'Failed to create order'), 
                500, 
                request_id
            ))
    
    except Exception as e:
        logger.error(f"Unexpected error in order creation: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response("An unexpected error occurred during order creation", 500, request_id))
