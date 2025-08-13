"""
Verteil NDC API integration routes.

This module contains routes for interacting with the Verteil NDC API.
"""
import json
import logging
import uuid
import os
from typing import Dict, Any, Optional
from datetime import datetime

from quart import Blueprint, request, jsonify, current_app, make_response
from quart_cors import cors, route_cors
from functools import wraps
import time
from collections import OrderedDict



# Import enhanced air shopping services
from services.flight.air_shopping import process_air_shopping_enhanced, process_air_shopping_basic
from services.flight.search import process_air_shopping  # Legacy compatibility



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
    get_flight_price as get_flight_price_service,
    create_booking,
    process_air_shopping,
    process_order_create,
    process_flight_price
)

# Import Redis flight storage for enhanced caching
from services.redis_flight_storage import redis_flight_storage
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

# CORS is now handled by @route_cors decorator

# Create a Blueprint for Verteil flight routes
bp = Blueprint('verteil_flights', __name__, url_prefix='/api/verteil')

# Allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
    "http://localhost:3001", 
    "http://127.0.0.1:3001",
    "https://flight-pearl.vercel.app"
]

def init_app(app):
    """Initialize the blueprint with the app."""
    # CORS is now handled at the blueprint level with the @route_cors decorator
    return app

# CORS is now handled by the init_app function



def _get_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def _generate_cache_key(search_params: Dict[str, Any], cache_type: str = "search") -> str:
    """Generate a deterministic cache key for flight search parameters."""
    # Create a normalized string from search parameters
    normalized_params = {
        'origin': search_params.get('origin', ''),
        'destination': search_params.get('destination', ''),
        'departDate': search_params.get('departDate', ''),
        'returnDate': search_params.get('returnDate', ''),
        'adults': str(search_params.get('numAdults', search_params.get('num_adults', 1))),
        'children': str(search_params.get('numChildren', search_params.get('num_children', 0))),
        'infants': str(search_params.get('numInfants', search_params.get('num_infants', 0))),
        'cabinClass': search_params.get('cabinPreference', search_params.get('cabin_class', 'ECONOMY')),
        'tripType': search_params.get('tripType', search_params.get('trip_type', 'ONE_WAY')).upper()
    }
    
    # Sort keys for consistent hash
    param_string = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_params.items()) if v)
    cache_key = hashlib.md5(param_string.encode()).hexdigest()
    
    logger.debug(f"Generated {cache_type} cache key: {cache_key} for params: {param_string}")
    return f"flight_{cache_type}:{cache_key}"

def _generate_flight_price_cache_key(offer_id: str, shopping_response_id: str) -> str:
    """Generate a deterministic cache key for flight pricing parameters."""
    normalized_params = {
        'offer_id': str(offer_id),
        'shopping_response_id': str(shopping_response_id)
    }
    
    param_string = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_params.items()) if v)
    cache_key = hashlib.md5(param_string.encode()).hexdigest()
    
    logger.debug(f"Generated flight price cache key: {cache_key} for offer: {offer_id}")
    return f"flight_price:{cache_key}"

def _generate_booking_cache_key(booking_id: str) -> str:
    """Generate a deterministic cache key for booking retrieval."""
    cache_key = hashlib.md5(booking_id.encode()).hexdigest()
    logger.debug(f"Generated booking cache key: {cache_key} for booking: {booking_id}")
    return f"booking:{cache_key}"

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

@bp.route('/air-shopping-test-postman', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)
async def air_shopping_test_postman():
    """Test endpoint using exact Postman request body structure"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Use exact Postman request body structure
        postman_payload = {
            "Preference": {
                "CabinPreferences": {
                    "CabinType": [
                        {"Code": "C", "OriginDestinationReferences": ["OD1"]},
                        {"Code": "C", "OriginDestinationReferences": ["OD2"]}
                    ]
                },
                "FarePreferences": {
                    "Types": {"Type": [{"Code": "PUBL"}]}
                },
                "PricingMethodPreference": {"BestPricingOption": "Y"}
            },
            "ResponseParameters": {
                "SortOrder": [
                    {"Order": "ASCENDING", "Parameter": "PRICE"},
                    {"Order": "ASCENDING", "Parameter": "STOP"},
                    {"Order": "ASCENDING", "Parameter": "DEPARTURE_TIME"}
                ],
                "ShopResultPreference": "FULL"
            },
            "Travelers": {
                "Traveler": [{"AnonymousTraveler": [{"PTC": {"value": "ADT"}}]}]
            },
            "CoreQuery": {
                "OriginDestinations": {
                    "OriginDestination": [
                        {
                            "OriginDestinationKey": "OD1",
                            "Departure": {"AirportCode": {"value": "NBO"}, "Date": "2025-07-20"},
                            "Arrival": {"AirportCode": {"value": "CDG"}}
                        },
                        {
                            "OriginDestinationKey": "OD2",
                            "Departure": {"AirportCode": {"value": "CDG"}, "Date": "2025-07-29"},
                            "Arrival": {"AirportCode": {"value": "NBO"}}
                        }
                    ]
                }
            }
        }

        logger.info(f"[TEST] Using exact Postman request body structure")
        logger.info(f"[TEST] Round-trip: NBO->CDG->NBO, Business class, 2025-07-20/29")

        # Use the core flight service directly
        from services.flight.core import FlightService

        # Initialize the service with current app config
        service = FlightService(current_app.config)

        # Make the request directly with the exact Postman payload
        response = await service._make_request(
            endpoint='/entrygate/rest/request:airShopping',
            payload=postman_payload,
            service_name='AirShopping',
            method='POST'
        )

        logger.info(f"[TEST] ✅ SUCCESS! Postman payload test returned flight data!")
        logger.info(f"[TEST] Response contains {len(str(response))} characters of data")

        return jsonify({
            'success': True,
            'message': '✅ SUCCESS! Postman payload test returned real flight data!',
            'response_size': len(str(response)),
            'has_flight_data': 'VDC-PR-' in str(response)  # Check for flight pricing data
        }), 200

    except Exception as e:
        logger.error(f"[TEST] Postman payload test failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/air-shopping-test-regular', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)
async def air_shopping_test_regular():
    """Test endpoint using regular air-shopping with updated payload structure"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Use the same search criteria as the working Postman test
        test_request = {
            "tripType": "ROUND_TRIP",
            "odSegments": [
                {"origin": "NBO", "destination": "CDG", "departureDate": "2025-07-20"},
                {"origin": "CDG", "destination": "NBO", "departureDate": "2025-07-29"}
            ],
            "numAdults": 1,
            "numChildren": 0,
            "numInfants": 0,
            "cabinClass": "BUSINESS"  # Business class like Postman
        }

        logger.info(f"[TEST] Testing regular air-shopping with updated payload structure")
        logger.info(f"[TEST] Round-trip: NBO->CDG->NBO, Business class, 2025-07-20/29")

        # Process through the enhanced air-shopping flow
        # Add configuration to the request data
        test_request['config'] = dict(current_app.config)
        test_request['enhanced'] = True  # Use enhanced mode for testing
        result = await process_air_shopping_enhanced(test_request)

        logger.info(f"[TEST] Regular air-shopping test result: {result.get('status', 'unknown')}")

        if result.get('status') == 'success':
            data = result.get('data', {})
            offers = data.get('offers', [])
            logger.info(f"[TEST] ✅ SUCCESS! Regular air-shopping returned {len(offers)} flight offers!")

            return jsonify({
                'success': True,
                'message': f'✅ SUCCESS! Regular air-shopping returned {len(offers)} flight offers!',
                'offers_count': len(offers),
                'has_offers': len(offers) > 0
            }), 200
        else:
            logger.error(f"[TEST] ❌ FAILED! Regular air-shopping returned error: {result.get('error', 'unknown')}")
            return jsonify({
                'success': False,
                'message': f'❌ FAILED! Regular air-shopping returned error',
                'error': result.get('error', 'unknown')
            }), 500

    except Exception as e:
        logger.error(f"[TEST] Error in regular air-shopping test: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Regular air-shopping test failed'
        }), 500


@bp.route('/air-shopping/cache-check', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_flight_search_cache():
    """
    Check if flight search data exists in cache and return it if valid.
    
    POST JSON Body:
    - Same parameters as air-shopping endpoint
    
    Returns:
    - Cached flight data if available and valid
    - Cache miss response if no valid cache exists
    """
    if request.method == 'OPTIONS':
        return await make_response(), 200
        
    request_id = _get_request_id()
    logger.info(f"Cache check request received - Request ID: {request_id}")
    
    try:
        # Get request data
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            data = await request.get_json() or {}
        
        # Generate cache key from search parameters
        cache_key = _generate_cache_key(data)
        
        # Try to retrieve cached data from Redis
        cached_result = redis_flight_storage.get_flight_search(cache_key)
        
        if cached_result['success']:
            logger.info(f"Cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_result['data'],
                'cached_at': cached_result['stored_at'],
                'expires_at': cached_result['expires_at'],
                'request_id': request_id,
                'cache_key': cache_key
            })
        else:
            logger.info(f"Cache miss for key: {cache_key} - Request ID: {request_id}")
            
            # Return cache miss response
            return jsonify({
                'status': 'cache_miss',
                'message': 'No valid cached data found',
                'request_id': request_id,
                'cache_key': cache_key
            })
            
    except Exception as e:
        logger.error(f"Cache check error: {str(e)} - Request ID: {request_id}")
        return jsonify({
            'status': 'cache_miss',
            'message': 'Cache check failed',
            'error': str(e),
            'request_id': request_id
        })

@bp.route('/air-shopping', methods=['GET', 'POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Timestamp"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
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



        # Convert frontend parameter names to backend equivalents
        parameter_mapping = {
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
            'infants': 'num_infants',
            'tripType': 'trip_type'
        }
        
        # Apply parameter mapping
        converted_data = {}
        for key, value in data.items():
            # Use mapped key if it exists, otherwise use original key
            mapped_key = parameter_mapping.get(key, key)
            converted_data[mapped_key] = value

        # Handle tripType parameter specifically
        if 'tripType' in data and 'trip_type' not in converted_data:
            converted_data['trip_type'] = data['tripType']

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
            logger.info(f"[DEBUG] Trip type for return segment check: '{trip_type}', returnDate: {converted_data.get('returnDate')}")
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
        
        # Convert cabin class names to preference names (frontend sends names like 'BUSINESS')
        cabin_code_mapping = {
            'ECONOMY': 'ECONOMY',
            'PREMIUM_ECONOMY': 'PREMIUM_ECONOMY',
            'BUSINESS': 'BUSINESS',
            'FIRST': 'FIRST',
            # Legacy support for codes (in case any old code still sends codes)
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
            # Handle single cabin class for one-way trips (from URL parameter cabinClass)
            cabin_code = converted_data['cabin_class']
            converted_data['cabinPreference'] = cabin_code_mapping.get(cabin_code, 'ECONOMY')
            logger.info(f"[DEBUG] Mapped cabin class {cabin_code} to {converted_data['cabinPreference']}")
        elif 'cabinPreference' in converted_data:
            # Handle cabin preference for one-way trips (from POST body cabinPreference)
            cabin_preference = converted_data['cabinPreference']
            # Ensure the cabin preference is properly mapped using the same mapping
            converted_data['cabinPreference'] = cabin_code_mapping.get(cabin_preference, 'ECONOMY')
            logger.info(f"[DEBUG] Mapped cabin preference {cabin_preference} to {converted_data['cabinPreference']}")
        else:
            # Debug: Log what keys are available if cabin mapping fails
            logger.info(f"[DEBUG] No cabin class mapping applied. Available keys: {list(converted_data.keys())}")
            if 'cabin_class' in converted_data:
                logger.info(f"[DEBUG] cabin_class value: {converted_data['cabin_class']}")
            if 'cabinClass' in converted_data:
                logger.info(f"[DEBUG] cabinClass value: {converted_data['cabinClass']}")
            if 'cabinPreference' in converted_data:
                logger.info(f"[DEBUG] cabinPreference value: {converted_data['cabinPreference']}")
            if 'outbound_cabin_class' in converted_data:
                logger.info(f"[DEBUG] outbound_cabin_class value: {converted_data['outbound_cabin_class']}")
            if 'return_cabin_class' in converted_data:
                logger.info(f"[DEBUG] return_cabin_class value: {converted_data['return_cabin_class']}")
            
        # Log the incoming request for debugging
        logger.info(f"Original request data: {data}")
        logger.info(f"Converted request data: {converted_data}")



        # Generate cache key for this search
        cache_key = _generate_cache_key(converted_data)
        
        # Check if we have cached data first (only for GET and POST without force_refresh)
        force_refresh = converted_data.get('force_refresh', False)
        if not force_refresh:
            cached_result = redis_flight_storage.get_flight_search(cache_key)
            
            if cached_result['success']:
                logger.info(f"🚀 Cache hit! Returning cached data for key: {cache_key} - Request ID: {request_id}")
                
                # Ensure the raw response cache key is updated with current request_id
                cached_data = cached_result['data']
                if cached_data and cached_data.get('metadata'):
                    # Check if we have a stored raw_response_cache_key
                    original_raw_key = cached_data['metadata'].get('raw_response_cache_key')
                    if original_raw_key:
                        # Extract the original request_id from the cached key
                        # Format: "air_shopping_raw_{original_request_id}"
                        if original_raw_key.startswith('air_shopping_raw_'):
                            original_request_id = original_raw_key.replace('air_shopping_raw_', '')
                            # Verify the raw response cache is still valid
                            try:
                                from utils.cache_manager import cache_manager
                                raw_response = cache_manager.get(original_raw_key)
                                if raw_response:
                                    logger.info(f"✅ Raw response cache still valid for key: {original_raw_key}")
                                else:
                                    logger.warning(f"⚠️ Raw response cache expired for key: {original_raw_key}")
                                    # Clear the key since it's no longer valid
                                    cached_data['metadata']['raw_response_cache_key'] = None
                            except Exception as e:
                                logger.warning(f"⚠️ Error checking raw response cache: {e}")
                                cached_data['metadata']['raw_response_cache_key'] = None
                    
                    # Add flight search cache key for future pricing calls
                    cached_data['metadata']['flight_search_cache_key'] = cache_key
                    logger.info(f"✅ Added flight_search_cache_key to cached metadata: {cache_key}")
                
                # Return cached data with proper response structure
                return jsonify({
                    'status': 'success',
                    'source': 'cache',
                    'data': cached_data,
                    'cached_at': cached_result['stored_at'],
                    'expires_at': cached_result['expires_at'],
                    'request_id': request_id,
                    'cache_key': cache_key,
                    'message': 'Flight search results retrieved from cache'
                })
        
        # Process the request with the enhanced flight service
        # Check if enhanced mode is requested (default: enhanced for multi-airline support)
        use_enhanced = converted_data.get('enhanced', True)  # Default to enhanced mode

        # Add configuration to the request data
        converted_data['config'] = dict(current_app.config)

        if use_enhanced:
            # Use enhanced air shopping with multi-airline support
            logger.info(f"🔍 Using enhanced air shopping service (cache miss) - Request ID: {request_id}")
            result = await process_air_shopping_enhanced(converted_data)
        else:
            # Use basic air shopping for legacy compatibility
            logger.info(f"🔍 Using basic air shopping service (cache miss) - Request ID: {request_id}")
            result = await process_air_shopping_basic(converted_data)

        # Cache the successful result for future requests
        if result.get('status') == 'success' and result.get('data'):
            try:
                cache_result = redis_flight_storage.store_flight_search(
                    search_data=result['data'],
                    session_id=cache_key,
                    ttl=300  # 5 minutes (reduced to match typical offer expiration times)
                )
                if cache_result['success']:
                    logger.info(f"💾 Cached search results for key: {cache_key} - Request ID: {request_id}")
                    # Add cache info to response
                    result['cache_key'] = cache_key
                    result['cached'] = True
                    
                    # Add flight search cache key to metadata for pricing API access
                    if result.get('data') and result['data'].get('metadata'):
                        result['data']['metadata']['flight_search_cache_key'] = cache_key
                        logger.info(f"Added flight_search_cache_key to metadata: {cache_key}")
                else:
                    logger.warning(f"Failed to cache search results: {cache_result.get('message')} - Request ID: {request_id}")
                    result['cached'] = False
            except Exception as cache_error:
                logger.error(f"Error caching search results: {str(cache_error)} - Request ID: {request_id}")
                result['cached'] = False

        # Log success
        service_type = "enhanced" if use_enhanced else "basic"
        logger.info(f"Successfully processed {service_type} air shopping request - Request ID: {request_id}")

        # Return the result (enhanced service already includes status and request_id)
        if result.get('status') == 'success':
            response = jsonify(result)
        else:
            # Handle error response
            response = jsonify(result)
            response.status_code = 500

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

@bp.route('/flight-price/cache-check', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_flight_price_cache():
    """
    Check if flight price data exists in cache and return it if valid.
    
    POST JSON Body:
    - offer_id: The ID of the offer to price
    - shopping_response_id: The ShoppingResponseID from AirShoppingRS
    
    Returns:
    - Cached flight price data if available and valid
    - Cache miss response if no valid cache exists
    """
    if request.method == 'OPTIONS':
        return await make_response(), 200
        
    request_id = _get_request_id()
    logger.info(f"Flight price cache check request received - Request ID: {request_id}")
    
    try:
        data = await request.get_json() or {}
        
        if not data.get('offer_id') or not data.get('shopping_response_id'):
            return jsonify({
                'status': 'cache_miss',
                'message': 'Missing required parameters for cache check',
                'request_id': request_id
            })
        
        # Generate cache key from pricing parameters
        cache_key = _generate_flight_price_cache_key(data['offer_id'], data['shopping_response_id'])
        
        # Try to retrieve cached data from Redis
        cached_result = redis_flight_storage.get_flight_price(cache_key)
        
        if cached_result['success']:
            logger.info(f"Flight price cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_result['data'],
                'cached_at': cached_result['stored_at'],
                'expires_at': cached_result['expires_at'],
                'request_id': request_id,
                'cache_key': cache_key
            })
        else:
            logger.info(f"Flight price cache miss for key: {cache_key} - Request ID: {request_id}")
            
            # Return cache miss response
            return jsonify({
                'status': 'cache_miss',
                'message': 'No valid cached price data found',
                'request_id': request_id,
                'cache_key': cache_key
            })
            
    except Exception as e:
        logger.error(f"Flight price cache check error: {str(e)} - Request ID: {request_id}")
        return jsonify({
            'status': 'cache_miss',
            'message': 'Cache check failed',
            'error': str(e),
            'request_id': request_id
        })

@bp.route('/flight-price', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Timestamp"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def flight_price():
    """
    Handle flight price requests.
    
    POST JSON Body:
    - offer_id: The ID of the offer to price
    - shopping_response_id: The ShoppingResponseID from AirShoppingRS
    - air_shopping_response: The full AirShopping response containing offer details
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
        required_fields = ['offer_id', 'shopping_response_id', 'air_shopping_response']
        missing_fields = [f for f in required_fields if f not in data and f != 'air_shopping_response' and f'{f}_id' not in data]
        
        # Backward compatibility: Check for air_shopping_rs as well
        if 'air_shopping_response' not in data and 'air_shopping_rs' in data:
            data['air_shopping_response'] = data.pop('air_shopping_rs')
            
        if not data.get('air_shopping_response'):
            missing_fields.append('air_shopping_response')
            
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.warning(f"{error_msg} - Request ID: {request_id}")
            return jsonify(_create_error_response(error_msg, 400, request_id))
        
        # Log the shopping response ID and offer ID for debugging
        logger.info(f"Processing flight price request - Offer ID: {data['offer_id']}, "
                   f"Shopping Response ID: {data['shopping_response_id']} - Request ID: {request_id}")
        
        # Log basic info about the air shopping response
        air_shopping = data.get('air_shopping_response', {})
        logger.debug(f"Air shopping response type: {type(air_shopping)}, "
                    f"keys: {list(air_shopping.keys()) if isinstance(air_shopping, dict) else 'N/A'}")

        # Extract cache key if available (for optimized backend caching)
        raw_response_cache_key = None
        if isinstance(air_shopping, dict):
            # Check if cache key is provided in metadata
            metadata = air_shopping.get('metadata', {})
            if isinstance(metadata, dict):
                raw_response_cache_key = metadata.get('raw_response_cache_key')
                if raw_response_cache_key:
                    logger.info(f"Found raw response cache key: {raw_response_cache_key}")

        # Generate cache key for this pricing request
        offer_id = data['offer_id']
        shopping_response_id = data['shopping_response_id']
        cache_key = _generate_flight_price_cache_key(offer_id, shopping_response_id)
        
        # Check if we have cached pricing data first
        force_refresh = data.get('force_refresh', False)
        if not force_refresh:
            cached_result = redis_flight_storage.get_flight_price(cache_key)
            
            if cached_result['success']:
                logger.info(f"🚀 Flight price cache hit! Returning cached data for key: {cache_key} - Request ID: {request_id}")
                
                # Return cached data with proper response structure
                return jsonify({
                    'status': 'success',
                    'source': 'cache',
                    'data': cached_result['data'],
                    'cached_at': cached_result['stored_at'],
                    'expires_at': cached_result['expires_at'],
                    'request_id': request_id,
                    'cache_key': cache_key,
                    'message': 'Flight price data retrieved from cache'
                })
        
        # Log the offer details for debugging
        logger.info(f"[DEBUG] Flight price request (cache miss) - Offer ID: {offer_id}, Type: {type(offer_id).__name__}")
        
        price_request = {
            'offer_id': offer_id,  # This is the frontend's offer ID
            'shopping_response_id': shopping_response_id,
            'air_shopping_response': air_shopping,
            'currency': data.get('currency', 'USD'),
            'request_id': request_id,
            'raw_response_cache_key': raw_response_cache_key,  # For optimized backend caching
            'config': dict(current_app.config)  # Pass the app configuration
        }
        
        try:
            # Process the flight price request
            logger.info(f"🔍 Processing flight price request (cache miss) - Request ID: {request_id}")
            result = await process_flight_price(price_request)
            
            # Check if the result is an error due to expired offers
            is_expired_offer_error = False
            if result and isinstance(result, dict) and result.get('status') == 'error':
                error_msg = result.get('error', '').lower()
                # Check for common expired offer error codes and messages
                expired_offer_indicators = [
                    'ndc-4191',
                    'shop offer not found',
                    'does not exist, expired, or consumed',
                    'offer expired',
                    'offer not found'
                ]
                is_expired_offer_error = any(indicator in error_msg for indicator in expired_offer_indicators)
                
                if is_expired_offer_error:
                    logger.warning(f"🕐 Detected expired offer error - Request ID: {request_id}")
                    
                    # Try to invalidate cached search data and retry once
                    try:
                        # Extract search parameters from the air shopping response for cache invalidation
                        air_shopping = data.get('air_shopping_response', {})
                        metadata = air_shopping.get('metadata', {})
                        
                        if metadata.get('flight_search_cache_key'):
                            # Invalidate the cached search data
                            search_cache_key = metadata['flight_search_cache_key']
                            logger.info(f"🗑️ Invalidating expired search cache: {search_cache_key} - Request ID: {request_id}")
                            
                            # Try to delete the cached search data
                            try:
                                redis_connection = redis_flight_storage.redis_client
                                if redis_connection and redis_flight_storage.redis_available:
                                    redis_connection.delete(search_cache_key)
                                    logger.info(f"✅ Successfully invalidated search cache: {search_cache_key}")
                            except Exception as invalidate_error:
                                logger.warning(f"Failed to invalidate search cache: {invalidate_error}")
                        
                        # Return a specific error response that the frontend can handle
                        logger.info(f"💫 Returning expired offer error for frontend handling - Request ID: {request_id}")
                        return jsonify({
                            'status': 'expired_offer_error',
                            'error': 'Flight offers have expired. Please search again for fresh results.',
                            'error_code': 'EXPIRED_OFFERS',
                            'message': 'The selected flight offers are no longer available. This happens when offers expire after being cached. Please perform a new search to get current offers.',
                            'request_id': request_id,
                            'should_retry_search': True,
                            'original_error': result.get('error', '')
                        })
                        
                    except Exception as retry_error:
                        logger.error(f"Error during expired offer retry handling: {str(retry_error)} - Request ID: {request_id}")
                        # Fall through to return the original error
            
            # Cache the successful result for future requests
            if result and isinstance(result, dict) and result.get('status') == 'success' and result.get('data'):
                try:
                    cache_result = redis_flight_storage.store_flight_price(
                        price_data=result['data'],
                        session_id=cache_key,
                        ttl=300  # 5 minutes - same as flight search to ensure consistency
                    )
                    if cache_result['success']:
                        logger.info(f"💾 Cached flight price data for key: {cache_key} - Request ID: {request_id}")
                        result['cache_key'] = cache_key
                        result['cached'] = True
                        
                        # Add cache key to metadata for booking service access
                        if result.get('data') and result['data'].get('metadata'):
                            result['data']['metadata']['flight_price_cache_key'] = cache_key
                            logger.info(f"Added flight_price_cache_key to metadata: {cache_key}")
                    else:
                        logger.warning(f"Failed to cache flight price data: {cache_result.get('message')} - Request ID: {request_id}")
                        result['cached'] = False
                except Exception as cache_error:
                    logger.error(f"Error caching flight price data: {str(cache_error)} - Request ID: {request_id}")
                    result['cached'] = False
            
            # Log the result status
            if result and isinstance(result, dict):
                status = result.get('status', 'unknown')
                logger.info(f"Flight price request completed with status: {status} - Request ID: {request_id}")
                if status == 'error' and not is_expired_offer_error:
                    logger.error(f"Error in flight price request: {result.get('error', 'No error details')} - Request ID: {request_id}")

            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Unhandled exception in flight price endpoint: {str(e)} - Request ID: {request_id}", exc_info=True)
            return jsonify(_create_error_response("An internal server error occurred", 500, request_id))
        
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


@bp.route('/booking/cache-check', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_booking_cache():
    """
    Check if booking data exists in cache and return it if valid.
    
    POST JSON Body:
    - booking_id: The ID of the booking to retrieve
    
    Returns:
    - Cached booking data if available and valid
    - Cache miss response if no valid cache exists
    """
    if request.method == 'OPTIONS':
        return await make_response(), 200
        
    request_id = _get_request_id()
    logger.info(f"Booking cache check request received - Request ID: {request_id}")
    
    try:
        data = await request.get_json() or {}
        
        if not data.get('booking_id'):
            return jsonify({
                'status': 'cache_miss',
                'message': 'Missing required booking_id parameter for cache check',
                'request_id': request_id
            })
        
        # Generate cache key from booking ID
        cache_key = _generate_booking_cache_key(data['booking_id'])
        
        # Try to retrieve cached data from Redis
        cached_result = redis_flight_storage.get_booking_data(cache_key)
        
        if cached_result['success']:
            logger.info(f"Booking cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_result['data'],
                'cached_at': cached_result['stored_at'],
                'expires_at': cached_result['expires_at'],
                'request_id': request_id,
                'cache_key': cache_key
            })
        else:
            logger.info(f"Booking cache miss for key: {cache_key} - Request ID: {request_id}")
            
            # Return cache miss response
            return jsonify({
                'status': 'cache_miss',
                'message': 'No valid cached booking data found',
                'request_id': request_id,
                'cache_key': cache_key
            })
            
    except Exception as e:
        logger.error(f"Booking cache check error: {str(e)} - Request ID: {request_id}")
        return jsonify({
            'status': 'cache_miss',
            'message': 'Cache check failed',
            'error': str(e),
            'request_id': request_id
        })

@bp.route('/debug/token', methods=['GET', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def debug_token():
    """
    Debug endpoint to check token status and metrics.
    """
    try:
        from utils.auth import TokenManager
        import os

        token_manager = TokenManager.get_instance()
        token_info = token_manager.get_token_info()

        # Try to get a token to see if it triggers generation
        try:
            token = token_manager.get_token()
            token_available = True
        except Exception as e:
            token_available = False
            token_info['error'] = str(e)

        # Add config debugging to this working endpoint
        config_debug = {
            'app_config': {
                'VERTEIL_USERNAME': 'SET' if current_app.config.get('VERTEIL_USERNAME') else 'NOT SET',
                'VERTEIL_PASSWORD': 'SET' if current_app.config.get('VERTEIL_PASSWORD') else 'NOT SET', 
                'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
                'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
                'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
            },
            'env_vars': {
                'VERTEIL_USERNAME': 'SET' if os.getenv('VERTEIL_USERNAME') else 'NOT SET',
                'VERTEIL_PASSWORD': 'SET' if os.getenv('VERTEIL_PASSWORD') else 'NOT SET', 
                'VERTEIL_API_BASE_URL': os.getenv('VERTEIL_API_BASE_URL'),
                'VERTEIL_OFFICE_ID': os.getenv('VERTEIL_OFFICE_ID'),
                'VERTEIL_THIRD_PARTY_ID': os.getenv('VERTEIL_THIRD_PARTY_ID'),
            }
        }

        return jsonify({
            'status': 'success',
            'token_available': token_available,
            'token_info': token_info,
            'config_set': bool(token_manager._config),
            'persistence_enabled': token_manager._enable_persistence,
            'token_file_path': token_manager._get_token_file_path() if token_manager._enable_persistence else None,
            'config_debug': config_debug
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@bp.route('/debug/config', methods=['GET', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def debug_config():
    """Debug endpoint to check configuration values."""
    try:
        if request.method == 'OPTIONS':
            return '', 200
            
        # Import os to check env vars directly
        import os
        
        config_debug = {
            'app_config': {
                'VERTEIL_USERNAME': 'SET' if current_app.config.get('VERTEIL_USERNAME') else 'NOT SET',
                'VERTEIL_PASSWORD': 'SET' if current_app.config.get('VERTEIL_PASSWORD') else 'NOT SET', 
                'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
                'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
                'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
            },
            'env_vars': {
                'VERTEIL_USERNAME': 'SET' if os.getenv('VERTEIL_USERNAME') else 'NOT SET',
                'VERTEIL_PASSWORD': 'SET' if os.getenv('VERTEIL_PASSWORD') else 'NOT SET', 
                'VERTEIL_API_BASE_URL': os.getenv('VERTEIL_API_BASE_URL'),
                'VERTEIL_OFFICE_ID': os.getenv('VERTEIL_OFFICE_ID'),
                'VERTEIL_THIRD_PARTY_ID': os.getenv('VERTEIL_THIRD_PARTY_ID'),
            },
            'config_keys_count': len(current_app.config.keys())
        }
        
        return jsonify({
            'status': 'success',
            'config': config_debug
        })
    except Exception as e:
        logger.error(f"Debug config endpoint failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/order-create', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-Timestamp"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def create_order():
    """
    Create a new flight booking order.
    
    Expected JSON payload:
    {
        "flight_price_response": {...},  # Direct flight price response from frontend
        "passengers": [...],    # Passenger details from frontend
        "payment": {...},       # Payment information
        "contact_info": {...},  # Contact information
        "servicelist_response": {...},  # Optional ServiceListRS response data
        "seatavailability_response": {...},  # Optional SeatAvailabilityRS response data
        "selected_services": [...],  # Optional list of selected service ObjectKeys
        "selected_seats": [...]  # Optional list of selected seat ObjectKeys
    }
    """
    request_id = _get_request_id()
    
    try:
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("Request body is required", 400, request_id))



        # DEBUG: Log frontend data summary
        logger.info(f"[DEBUG] Raw frontend data received (ReqID: {request_id}) - Keys: {list(data.keys()) if data else 'None'}")
        
        # Extract data from frontend request
        flight_price_response = data.get('flight_price_response')  # Direct flight price response from frontend
        frontend_passengers = data.get('passengers', [])
        payment_info = data.get('payment', {})
        contact_info = data.get('contact_info', {})
        frontend_offer_id = data.get('OfferID')  # Extract OfferID sent from frontend (might be index)
        shopping_response_id = data.get('ShoppingResponseID')  # Extract ShoppingResponseID sent from frontend
        
        # Extract service and seat data from frontend request
        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])

        # Extract the REAL OfferID from the raw flight price response instead of using the index
        offer_id = None
        logger.info(f"[DEBUG] flight_price_response available: {bool(flight_price_response)} (ReqID: {request_id})")
        logger.info(f"[DEBUG] frontend_offer_id received: {frontend_offer_id} (ReqID: {request_id})")

        if flight_price_response:
            logger.info(f"[DEBUG] flight_price_response keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'} (ReqID: {request_id})")
            logger.info(f"[DEBUG] flight_price_response type: {type(flight_price_response)} (ReqID: {request_id})")

            # Try multiple possible structures for OfferID extraction
            extracted_offer_id = None

            # Log the complete structure for debugging
            logger.info(f"[DEBUG] Complete flight_price_response structure (first 2000 chars): {str(flight_price_response)[:2000]}... (ReqID: {request_id})")

            # Method 1: Direct PricedFlightOffers at top level
            priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                offer_id_node = priced_offers[0].get('OfferID', {})
                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                    extracted_offer_id = offer_id_node['value']
                    logger.info(f"[DEBUG] Method 1 - Extracted OfferID from top-level PricedFlightOffers: {extracted_offer_id} (ReqID: {request_id})")
                elif offer_id_node:
                    extracted_offer_id = offer_id_node
                    logger.info(f"[DEBUG] Method 1 - Extracted OfferID (simple): {extracted_offer_id} (ReqID: {request_id})")

            # Method 2: Try nested data.raw_response structure
            if not extracted_offer_id and 'data' in flight_price_response:
                data_section = flight_price_response['data']
                logger.info(f"[DEBUG] Found data section, keys: {list(data_section.keys()) if isinstance(data_section, dict) else 'Not a dict'} (ReqID: {request_id})")

                if 'raw_response' in data_section:
                    raw_response = data_section['raw_response']
                    logger.info(f"[DEBUG] Found raw_response in data, keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'Not a dict'} (ReqID: {request_id})")

                    priced_offers = raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
                    if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                        offer_id_node = priced_offers[0].get('OfferID', {})
                        if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                            extracted_offer_id = offer_id_node['value']
                            logger.info(f"[DEBUG] Method 2 - Extracted OfferID from data.raw_response: {extracted_offer_id} (ReqID: {request_id})")

            # Method 3: Try FlightPriceRS structure
            if not extracted_offer_id:
                flight_price_rs = flight_price_response.get('FlightPriceRS', {})
                if flight_price_rs:
                    logger.info(f"[DEBUG] Found FlightPriceRS, keys: {list(flight_price_rs.keys()) if isinstance(flight_price_rs, dict) else 'Not a dict'} (ReqID: {request_id})")
                    priced_offers = flight_price_rs.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
                    if priced_offers and isinstance(priced_offers, list) and len(priced_offers) > 0:
                        offer_id_node = priced_offers[0].get('OfferID', {})
                        if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                            extracted_offer_id = offer_id_node['value']
                            logger.info(f"[DEBUG] Method 3 - Extracted OfferID from FlightPriceRS: {extracted_offer_id} (ReqID: {request_id})")

            # Method 4: Try to find any OfferID anywhere in the structure (recursive search)
            if not extracted_offer_id:
                def find_offer_id_recursive(obj, path=""):
                    if isinstance(obj, dict):
                        if 'OfferID' in obj:
                            offer_id_node = obj['OfferID']
                            if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                                return offer_id_node['value'], f"{path}.OfferID.value"
                            elif offer_id_node:
                                return offer_id_node, f"{path}.OfferID"

                        for key, value in obj.items():
                            result, result_path = find_offer_id_recursive(value, f"{path}.{key}" if path else key)
                            if result:
                                return result, result_path
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            result, result_path = find_offer_id_recursive(item, f"{path}[{i}]")
                            if result:
                                return result, result_path

                    return None, ""

                extracted_offer_id, found_path = find_offer_id_recursive(flight_price_response)
                if extracted_offer_id:
                    logger.info(f"[DEBUG] Method 4 - Found OfferID recursively at path: {found_path}, value: {extracted_offer_id} (ReqID: {request_id})")

            offer_id = extracted_offer_id

            # Fallback to frontend OfferID if extraction failed
            if not offer_id:
                offer_id = frontend_offer_id
                logger.warning(f"[DEBUG] Could not extract OfferID from raw response, using frontend value: {offer_id} (ReqID: {request_id})")
        else:
            offer_id = frontend_offer_id
            logger.warning(f"[DEBUG] No flight_price_response available, using frontend OfferID: {offer_id} (ReqID: {request_id})")
        
        # Try to retrieve flight price response from new Redis flight storage system
        flight_price_cache_key = None
        if isinstance(flight_price_response, dict):
            metadata = flight_price_response.get('metadata', {})
            if isinstance(metadata, dict):
                flight_price_cache_key = metadata.get('flight_price_cache_key')
                if flight_price_cache_key:
                    logger.info(f"[DEBUG] Found flight price cache key: {flight_price_cache_key} (ReqID: {request_id})")
                    try:
                        from services.redis_flight_storage import RedisFlightStorage
                        redis_flight_storage = RedisFlightStorage()
                        cached_result = redis_flight_storage.get_flight_price(flight_price_cache_key)
                        if cached_result['success']:
                            logger.info(f"[DEBUG] Retrieved flight price response from Redis cache (ReqID: {request_id})")
                            flight_price_response = cached_result['data']
                        else:
                            logger.warning(f"[DEBUG] Flight price response not found in Redis cache for key: {flight_price_cache_key} (ReqID: {request_id})")
                    except Exception as cache_error:
                        logger.warning(f"[DEBUG] Failed to retrieve flight price response from Redis cache: {cache_error} (ReqID: {request_id})")

        # DEBUG: Log extracted data components
        logger.info(f"[DEBUG] Extracted flight_price_response present (ReqID: {request_id}): {bool(flight_price_response)}")
        if flight_price_response:
            logger.info(f"[DEBUG] Flight price response keys (ReqID: {request_id}): {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
        logger.info(f"[DEBUG] Extracted passengers count (ReqID: {request_id}): {len(frontend_passengers) if frontend_passengers else 0}")
        logger.info(f"[DEBUG] Extracted payment method (ReqID: {request_id}): {payment_info.get('payment_method') if payment_info else 'None'}")
        logger.info(f"[DEBUG] Complete payment_info structure (ReqID: {request_id}): {payment_info}")
        logger.info(f"[DEBUG] Extracted contact info present (ReqID: {request_id}): {bool(contact_info)}")
        logger.info(f"[DEBUG] Extracted OfferID (ReqID: {request_id}): {offer_id}")
        logger.info(f"[DEBUG] Extracted ShoppingResponseID (ReqID: {request_id}): {shopping_response_id}")
        logger.info(f"[DEBUG] Using cached flight price response (ReqID: {request_id}): {bool(flight_price_cache_key)}")
        
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
            'shopping_response_id': shopping_response_id,  # Pass the extracted ShoppingResponseID
            'servicelist_response': servicelist_response,  # Pass ServiceListRS response
            'seatavailability_response': seatavailability_response,  # Pass SeatAvailabilityRS response
            'selected_services': selected_services,  # Pass selected service ObjectKeys
            'selected_seats': selected_seats  # Pass selected seat ObjectKeys
        }
        
        # DEBUG: Log order data summary (without verbose content)
        logger.info(f"[DEBUG] Order data being sent to booking service (ReqID: {request_id}) - Keys: {list(order_data.keys()) if order_data else 'None'}")
        
        logger.info(f"Processing order creation - Request ID: {request_id}")
        
        # Call the booking service
        result = await process_order_create(order_data)

        # Check if result contains an error
        if 'error' in result:
            error_info = result['error']
            # Handle both string and dict error formats
            if isinstance(error_info, str):
                error_message = error_info
                error_code = 'BOOKING_ERROR'
            else:
                error_message = error_info.get('message', 'Failed to create order')
                error_code = error_info.get('code', 'BOOKING_ERROR')
            logger.error(f"Order creation failed - Request ID: {request_id}, Error Code: {error_code}, Error: {error_message}")
            return jsonify(_create_error_response(
                error_message,
                500,
                request_id
            ))
        else:
            # Success case - result contains booking data directly
            logger.info(f"Order created successfully - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': result,
                'request_id': request_id
            })
    
    except Exception as e:
        logger.error(f"Unexpected error in order creation: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response("An unexpected error occurred during order creation", 500, request_id))
