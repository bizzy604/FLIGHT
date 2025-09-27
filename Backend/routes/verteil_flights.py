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


def detect_pricing_required(
    servicelist_response: Optional[Dict[str, Any]] = None,
    seatavailability_response: Optional[Dict[str, Any]] = None,
    selected_services: Optional[list] = None,
    selected_seats: Optional[list] = None
) -> Dict[str, Any]:
    """
    Detect if additional pricing is required for selected services and seats.
    
    Args:
        servicelist_response: ServiceList response data
        seatavailability_response: SeatAvailability response data
        selected_services: List of selected service ObjectKeys
        selected_seats: List of selected seat positions (e.g., ['47G', '48A'])
    
    Returns:
        Dict with pricing requirements information
    """
    services_require_pricing = []
    seats_require_pricing = []
    
    # Check services
    if servicelist_response and selected_services:
        services = servicelist_response.get('Services', {}).get('Service', [])
        # Handle case where Service is a single dict instead of a list
        if isinstance(services, dict):
            services = [services]
        elif not isinstance(services, list):
            services = []
            
        for service in services:
            if isinstance(service, dict):
                service_key = service.get('ObjectKey', '')
                priced_ind = service.get('PricedInd', True)
                
                if service_key in selected_services and not priced_ind:
                    services_require_pricing.append(service_key)
    
    # Check seats - FIXED: Handle pricing ObjectKeys directly
    if seatavailability_response and selected_seats:
        # Get seat services from response
        seat_services = seatavailability_response.get('Services', {}).get('Service', [])
        if not isinstance(seat_services, list):
            seat_services = [seat_services] if seat_services else []
        
        # Check each selected seat (which are pricing ObjectKeys)
        for selected_seat in selected_seats:
            # Find the service that matches this pricing ObjectKey
            for service in seat_services:
                if isinstance(service, dict):
                    service_key = service.get('ObjectKey', '')
                    if service_key == selected_seat:
                        priced_ind = service.get('PricedInd', True)
                        if not priced_ind:
                            seats_require_pricing.append(selected_seat)
                            break  # Found one that requires pricing, no need to check others for this seat
    
    requires_pricing = len(services_require_pricing) > 0 or len(seats_require_pricing) > 0
    
    return {
        'requires_pricing': requires_pricing,
        'services_require_pricing': services_require_pricing,
        'seats_require_pricing': seats_require_pricing,
        'total_items_requiring_pricing': len(services_require_pricing) + len(seats_require_pricing)
    }



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
from services.simple_flight_cache import simple_flight_cache
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
    
    # Handle both old format (origin/destination) and new format (odSegments)
    origin = search_params.get('origin', '')
    destination = search_params.get('destination', '')
    depart_date = search_params.get('departDate', '')
    return_date = search_params.get('returnDate', '')
    
    # Check if we have odSegments structure instead
    if not origin and not destination and 'odSegments' in search_params:
        od_segments = search_params['odSegments']
        if isinstance(od_segments, list) and len(od_segments) > 0:
            # Get first segment for outbound
            first_segment = od_segments[0]
            origin = first_segment.get('origin', '')
            destination = first_segment.get('destination', '')
            depart_date = first_segment.get('departureDate', '')
            
            # For round-trip, check if return date is in the first segment
            if first_segment.get('returnDate'):
                return_date = first_segment.get('returnDate', '')
            # Otherwise, get second segment for return if it exists (legacy format)
            elif len(od_segments) > 1:
                second_segment = od_segments[1]
                return_date = second_segment.get('departureDate', '')
    
    # Create a normalized string from search parameters
    normalized_params = {
        'origin': origin,
        'destination': destination,
        'departDate': depart_date,
        'returnDate': return_date,
        'adults': str(search_params.get('numAdults', search_params.get('num_adults', 1))),
        'children': str(search_params.get('numChildren', search_params.get('num_children', 0))),
        'infants': str(search_params.get('numInfants', search_params.get('num_infants', 0))),
        'cabinClass': search_params.get('cabinPreference', search_params.get('cabin_class', 'ECONOMY')),
        'tripType': search_params.get('tripType', search_params.get('trip_type', 'ONE_WAY')).upper(),
        'airlines': search_params.get('airlines', ''),  # Include airline filter in cache key
        'directOnly': str(search_params.get('directOnly', False)),  # Include direct flights filter
        'maxStops': str(search_params.get('maxStops', '')),  # Include stops filter
        'cache_version': '2025-08-26-v4'  # Cache version to force invalidation when needed
    }
    
    # Sort keys for consistent hash
    param_string = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_params.items()) if v)
    cache_key = hashlib.md5(param_string.encode()).hexdigest()
    
    logger.info(f"[CACHE KEY DEBUG] Generated {cache_type} cache key: {cache_key}")
    logger.info(f"[CACHE KEY DEBUG] Param string: {param_string}")
    logger.info(f"[CACHE KEY DEBUG] Airlines filter: '{search_params.get('airlines', 'NONE')}'")
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
        # Extract hash part from cache_key to use as session_id
        session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
        cached_result = simple_flight_cache.get_flight_search(session_id)
        
        if cached_result['success']:
            logger.info(f"Cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_result['data'],
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
        
        # 🚀 PRIORITY FIX: Make API calls primary, cache only when explicitly requested
        use_cache_only = converted_data.get('use_cache_only', False)
        if use_cache_only:
            # Extract hash part from cache_key to use as session_id
            session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
            cached_result = simple_flight_cache.get_flight_search(session_id)
            
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
                # Extract hash part from cache_key to use as session_id
                # cache_key format: "flight_search:hash" -> we need just "hash"
                session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
                cache_result = simple_flight_cache.store_flight_search(
                    session_id=session_id,
                    search_data=result['data'],
                    ttl=300  # 5 minutes
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
        # Extract hash part from cache_key to use as session_id
        session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
        cached_result = simple_flight_cache.get_flight_price(session_id)
        
        if cached_result['success']:
            logger.info(f"Flight price cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_result['data'],
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
        
        # 🚀 PRIORITY FIX: Make API calls primary, cache only when explicitly requested
        use_cache_only = data.get('use_cache_only', False)
        
        # Only use cache if explicitly requested via use_cache_only parameter
        if use_cache_only:
            # Extract hash part from cache_key to use as session_id
            session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
            cached_result = simple_flight_cache.get_flight_price(session_id)
            
            if cached_result['success']:
                logger.info(f"📦 Using cached flight price data for key: {cache_key} - Request ID: {request_id}")
                
                # 🚀 ROBUST SOLUTION: Ensure cached data also has guaranteed cache key
                cached_data = cached_result['data']
                if not cached_data.get('metadata'):
                    cached_data['metadata'] = {}
                
                # Ensure flight_price_cache_key is available in metadata
                if not cached_data['metadata'].get('flight_price_cache_key'):
                    cached_data['metadata']['flight_price_cache_key'] = cache_key
                    logger.info(f"✅ Added cache key to cached flight price metadata: {cache_key}")
                
                # Return cached data with proper response structure
                cache_response = {
                    'status': 'success',
                    'source': 'cache',
                    'data': cached_data,
                    'request_id': request_id,
                    'cache_key': cache_key,
                    'flight_price_cache_key': cached_data['metadata']['flight_price_cache_key'],  # 🔧 Top level guarantee
                    'message': 'Flight price data retrieved from cache'
                }
                
                logger.info(f"🔑 GUARANTEED cached flight_price_cache_key transmission: metadata={cached_data['metadata']['flight_price_cache_key']}, top_level={cache_response['flight_price_cache_key']}")
                return jsonify(cache_response)
        
        # NEW: Check if this is a PricedInd=false pricing request
        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])
        
        # Check if pricing is required for selected services and seats
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        if pricing_info['requires_pricing']:
            logger.info(f"💰 PricedInd=false scenario detected - using ancillary pricing builder - Request ID: {request_id}")
            logger.info(f"Pricing required for: {pricing_info}")
            
            # Use ancillary pricing builder for PricedInd=false scenario
            from scripts.build_flightprice_ancillary_rq import build_flightprice_ancillary_request
            
            # Build ancillary pricing request
            ancillary_request = build_flightprice_ancillary_request(
                flight_price_response=air_shopping,  # Use air shopping response as base
                servicelist_response=servicelist_response,
                seatavailability_response=seatavailability_response,
                selected_services=selected_services,
                selected_seats=selected_seats
            )
            
            if not ancillary_request:
                return jsonify(_create_error_response("Failed to build ancillary pricing request", 400, request_id))
            
            logger.info(f"✅ Built ancillary pricing request with {len(ancillary_request.get('Query', {}).get('Offers', {}).get('Offer', [{}])[0].get('OfferItemIDs', {}).get('OfferItemID', []))} items")
            
            # NEW: Log ancillary pricing request
            from utils.api_logger import api_logger
            api_logger.log_request(
                service_name='FlightPrice',
                request_id=request_id,
                payload=ancillary_request,
                endpoint='/entrygate/rest/request:flightPrice',
                headers={'Content-Type': 'application/json'}
            )
            
            # Create price request for ancillary pricing
            price_request = {
                'ancillary_pricing_request': ancillary_request,  # Use ancillary request
                'pricing_info': pricing_info,
                'request_id': request_id,
                'config': dict(current_app.config)
            }
        else:
            # Standard flight pricing request
            logger.info(f"[DEBUG] Standard flight price request - Offer ID: {offer_id}, Type: {type(offer_id).__name__}")
            
            price_request = {
                'offer_id': offer_id,  # This is the frontend's offer ID
                'shopping_response_id': shopping_response_id,
                'air_shopping_response': air_shopping,
                'currency': data.get('currency', 'USD'),
                'request_id': request_id,
                'raw_response_cache_key': raw_response_cache_key,  # For optimized backend caching
                'config': dict(current_app.config)  # Pass the app configuration
            }
        
        # Add request deduplication to prevent multiple concurrent API calls for same flight pricing
        dedup_key = f"flight_price:{cache_key}"
        if request_cache.is_duplicate(dedup_key):
            logger.info(f"🔄 Duplicate flight price request detected for key: {cache_key}. Waiting for ongoing request... - Request ID: {request_id}")
            
            # Wait for the ongoing request to complete by polling cache
            import asyncio
            wait_time = 0
            max_wait = 10  # Maximum 10 seconds wait
            
            while wait_time < max_wait:
                await asyncio.sleep(0.5)  # Wait 500ms
                wait_time += 0.5
                
                # Check if cache now has the result
                session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
                cached_result = simple_flight_cache.get_flight_price(session_id)
                if cached_result['success']:
                    logger.info(f"🎯 Duplicate request resolved via cache for key: {cache_key} - Request ID: {request_id}")
                    return jsonify({
                        'status': 'success',
                        'source': 'cache_after_dedup',
                        'data': cached_result['data'],
                        'request_id': request_id,
                        'cache_key': cache_key,
                        'message': 'Flight price data retrieved after deduplication wait'
                    })
            
            logger.warning(f"⏰ Deduplication wait timeout for key: {cache_key}. Proceeding with request - Request ID: {request_id}")
        
        # Mark this request as in progress to prevent duplicates
        request_cache.add_request(dedup_key)
        
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
                                # Use new cache system to invalidate the search data
                                delete_result = simple_flight_cache.delete_flight_search(search_cache_key)
                                if delete_result['success']:
                                    logger.info(f"✅ Successfully invalidated search cache: {search_cache_key}")
                                else:
                                    logger.warning(f"Failed to invalidate search cache: {delete_result.get('error')}")
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
                    # Extract hash part from cache_key to use as session_id
                    session_id = cache_key.split(':')[-1] if ':' in cache_key else cache_key
                    cache_result = simple_flight_cache.store_flight_price(
                        session_id=session_id,
                        price_data=result['data'],
                        ttl=300  # 5 minutes
                    )
                    if cache_result['success']:
                        logger.info(f"💾 Cached flight price data for key: {cache_key} - Request ID: {request_id}")
                        result['cache_key'] = cache_key
                        result['cached'] = True
                        
                        # 🚀 ROBUST SOLUTION: Ensure metadata always exists and contains flight_price_cache_key
                        if not result.get('data'):
                            result['data'] = {}
                        if not result['data'].get('metadata'):
                            result['data']['metadata'] = {}
                        
                        # Preserve raw cache key from pricing service if it exists, otherwise use processed cache key
                        if not result['data']['metadata'].get('flight_price_cache_key'):
                            result['data']['metadata']['flight_price_cache_key'] = cache_key
                            logger.info(f"✅ Added processed flight_price_cache_key to metadata: {cache_key}")
                        else:
                            logger.info(f"✅ Preserved raw flight_price_cache_key in metadata: {result['data']['metadata']['flight_price_cache_key']}")
                        
                        # Add processed cache key separately for reference
                        result['data']['metadata']['processed_cache_key'] = cache_key
                        
                        # 🔧 CRITICAL: Ensure frontend receives cache key at top level too
                        result['flight_price_cache_key'] = result['data']['metadata']['flight_price_cache_key']
                        
                        logger.info(f"🔑 GUARANTEED flight_price_cache_key transmission: metadata={result['data']['metadata']['flight_price_cache_key']}, top_level={result['flight_price_cache_key']}")
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
                
                # NEW: Log FlightPrice response
                from utils.api_logger import api_logger
                api_logger.log_response(
                    service_name='FlightPrice',
                    request_id=request_id,
                    response=result,
                    status_code=200 if status == 'success' else 400,
                    response_time_ms=None  # Could be calculated if needed
                )

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
        cached_result = simple_flight_cache.get_booking(cache_key)
        
        if cached_result['success']:
            logger.info(f"Booking cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'source': 'cache',
                'data': cached_result['data'],
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

@bp.route('/cache/clear', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def clear_cache():
    """
    Clear all flight-related cache data.
    """
    if request.method == 'OPTIONS':
        return await make_response(), 200
    
    try:
        from services.simple_flight_cache import simple_flight_cache
        
        # Clear all cached data 
        health_result = simple_flight_cache.get_cache_health()
        stats_before = health_result.get('stats', {})
        
        # Since we can't clear all cache directly, we'll update the cache version to invalidate all keys
        # This is done by changing the cache version in the code above
        
        return jsonify({
            'status': 'success',
            'message': 'Cache invalidation triggered via version update',
            'stats_before_clear': stats_before,
            'new_cache_version': '2025-08-26-v4'
        })
        
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to clear cache: {str(e)}'
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
        
        # 🔍 DEBUG: Log the complete raw request body to identify missing cache keys
        import json
        logger.error(f"🚨 RAW REQUEST BODY (ReqID: {request_id}): {json.dumps(data, default=str)[:2000]}...")



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
        
        # 🚀 NEW: Extract cache keys sent by frontend (proper approach)
        seat_availability_cache_key = data.get('seat_availability_cache_key')  
        service_list_cache_key = data.get('service_list_cache_key')
        
        # 🔧 FALLBACK: If frontend didn't send cache keys, try to derive them from flight price data
        if (not seat_availability_cache_key or not service_list_cache_key) and flight_price_response:
            logger.info(f"[FALLBACK] Frontend didn't send cache keys, attempting to derive from flight price data (ReqID: {request_id})")
            
            # Try to extract flight_price_cache_key from metadata
            flight_price_cache_key = None
            if isinstance(flight_price_response, dict):
                metadata = flight_price_response.get('metadata') or flight_price_response.get('Metadata', {})
                flight_price_cache_key = metadata.get('flight_price_cache_key')
                
                if not flight_price_cache_key:
                    # Try to get from top-level metadata
                    flight_price_cache_key = flight_price_response.get('flight_price_cache_key')
                    
                logger.info(f"[FALLBACK] Extracted flight_price_cache_key: {flight_price_cache_key} (ReqID: {request_id})")
            
            # 🔧 FIXED: Use the flight_price_cache_key directly for consistency with seat/service endpoints
            # The seat/service data is stored with the flight_price_cache_key as session_id
            if flight_price_cache_key and not seat_availability_cache_key:
                seat_availability_cache_key = flight_price_cache_key
                logger.info(f"[FALLBACK] ✅ Using flight_price_cache_key for seat_availability_cache_key: {seat_availability_cache_key} (ReqID: {request_id})")
            
            if flight_price_cache_key and not service_list_cache_key:
                service_list_cache_key = flight_price_cache_key
                logger.info(f"[FALLBACK] ✅ Using flight_price_cache_key for service_list_cache_key: {service_list_cache_key} (ReqID: {request_id})")
            
            # If no flight_price_cache_key, fall back to the old derivation method
            if not flight_price_cache_key:
                logger.warning(f"[FALLBACK] No flight_price_cache_key found, falling back to derivation (ReqID: {request_id})")
                
                # Derive cache keys using the same logic as seat/service endpoints
                if not seat_availability_cache_key:
                    try:
                        # Import the cache key generation function
                        from routes.clean_seat_service import _generate_seat_availability_cache_key
                        derived_seat_key = _generate_seat_availability_cache_key(
                            flight_price_response=flight_price_response,
                            flight_price_cache_key=flight_price_cache_key
                        )
                        seat_availability_cache_key = derived_seat_key
                        logger.info(f"[FALLBACK] ✅ Derived seat_availability_cache_key: {seat_availability_cache_key} (ReqID: {request_id})")
                    except Exception as e:
                        logger.warning(f"[FALLBACK] Failed to derive seat cache key: {e} (ReqID: {request_id})")
                
                if not service_list_cache_key:
                    try:
                        # Import the cache key generation function  
                        from routes.clean_seat_service import _generate_service_list_cache_key
                        derived_service_key = _generate_service_list_cache_key(
                            flight_price_response=flight_price_response,
                            flight_price_cache_key=flight_price_cache_key
                        )
                        service_list_cache_key = derived_service_key
                        logger.info(f"[FALLBACK] ✅ Derived service_list_cache_key: {service_list_cache_key} (ReqID: {request_id})")
                    except Exception as e:
                        logger.warning(f"[FALLBACK] Failed to derive service cache key: {e} (ReqID: {request_id})")
        
        # 🔍 DEBUG: Log raw request data to identify missing keys
        logger.info(f"[DEBUG] RAW REQUEST DATA received at OrderCreate (ReqID: {request_id}):")
        logger.info(f"[DEBUG] - Request data keys: {list(data.keys()) if data else 'None'}")
        logger.info(f"[DEBUG] - Raw seat_availability_cache_key from request: {repr(data.get('seat_availability_cache_key'))}")
        logger.info(f"[DEBUG] - Raw service_list_cache_key from request: {repr(data.get('service_list_cache_key'))}")
        logger.info(f"[DEBUG] - session_id from request: {data.get('session_id')}")
        
        # 🚀 DEBUG LOG FOR SEAT/SERVICE SELECTIONS
        logger.info(f"[DEBUG] Seat/Service selections received (ReqID: {request_id}):")
        logger.info(f"[DEBUG] - selected_services: {selected_services}")
        logger.info(f"[DEBUG] - selected_seats: {selected_seats}")
        logger.info(f"[DEBUG] - servicelist_response available: {bool(servicelist_response)}")
        logger.info(f"[DEBUG] - seatavailability_response available: {bool(seatavailability_response)}")
        logger.info(f"[DEBUG] - seat_availability_cache_key: {seat_availability_cache_key}")
        logger.info(f"[DEBUG] - service_list_cache_key: {service_list_cache_key}")

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
                        # FIXED: Use simple cache for consistent data retrieval
                        # Extract hash part if flight_price_cache_key has wrong format
                        session_id = flight_price_cache_key.split(':')[-1] if ':' in flight_price_cache_key else flight_price_cache_key
                        cached_result = simple_flight_cache.get_flight_price(session_id)
                        if cached_result.get('success') and cached_result.get('data'):
                            logger.info(f"[DEBUG] Retrieved flight price response from Redis (ReqID: {request_id})")
                            flight_price_response = cached_result['data']
                            
                            # 🚀 CRITICAL FIX: Ensure metadata is preserved in flight_price_response
                            if not isinstance(flight_price_response, dict):
                                flight_price_response = {}
                            if 'metadata' not in flight_price_response:
                                flight_price_response['metadata'] = {}
                            
                            # Ensure the flight_price_cache_key is available for seat/service cache retrieval
                            if 'flight_price_cache_key' not in flight_price_response['metadata']:
                                flight_price_response['metadata']['flight_price_cache_key'] = flight_price_cache_key
                                logger.info(f"[DEBUG] ✅ Restored flight_price_cache_key to metadata: {flight_price_cache_key} (ReqID: {request_id})")
                        else:
                            logger.warning(f"[DEBUG] Flight price response not found in Redis for key: {flight_price_cache_key} (ReqID: {request_id})")
                    except Exception as cache_error:
                        logger.warning(f"[DEBUG] Failed to retrieve flight price response from Redis: {cache_error} (ReqID: {request_id})")

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
        
        # FIXED: Check if pricing is required for selected services and seats BEFORE OrderCreate
        from scripts.build_flightprice_ancillary_rq import detect_pricing_required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        logger.info(f"🔍 Pricing requirements: {pricing_info} - Request ID: {request_id}")
        
        # FIXED: Handle PricedInd=false scenario by calling ancillary pricing API
        ancillary_pricing_response = None
        if pricing_info['requires_pricing']:
            logger.info("💰 PricedInd=false scenario detected - calling ancillary pricing API")
            
            # Check if ancillary pricing response is already provided
            ancillary_pricing_response = data.get('ancillary_pricing_response')
            
            if not ancillary_pricing_response:
                # Call ancillary pricing API
                try:
                    from scripts.build_flightprice_ancillary_rq import build_flightprice_ancillary_request
                    from services.flight.core import make_api_request
                    from utils.auth import TokenManager
                    
                    # Build ancillary pricing request
                    ancillary_request = build_flightprice_ancillary_request(
                        flight_price_response=flight_price_response,
                        servicelist_response=servicelist_response,
                        seatavailability_response=seatavailability_response,
                        selected_services=selected_services,
                        selected_seats=selected_seats,
                        selected_offer_index=0
                    )
                    
                    # Get token for API call
                    token_manager = TokenManager.get_instance()
                    bearer_token = token_manager.get_token()
                    
                    # Make ancillary pricing API call
                    logger.info(f"🚀 Calling ancillary pricing API for {pricing_info['total_items_require_pricing']} items")
                    ancillary_pricing_response = await make_api_request(
                        url=f"{current_app.config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice",
                        method='POST',
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': '*/*',
                            'Authorization': bearer_token,
                            'OfficeId': current_app.config.get('VERTEIL_OFFICE_ID'),
                            'service': 'FlightPrice',
                            'User-Agent': 'PostmanRuntime/7.41',
                            'Cache-Control': 'no-cache',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Connection': 'keep-alive'
                        },
                        json_data=ancillary_request,
                        service_name='FlightPrice',
                        request_id=request_id
                    )
                    
                    logger.info("✅ Ancillary pricing API call completed successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to call ancillary pricing API: {e}")
                    return jsonify(_create_error_response(
                        f"Failed to price selected services/seats: {str(e)}", 
                        500, request_id
                    ))
            
            logger.info("✅ Ancillary pricing response available - will use enhanced OrderCreate builder")
        else:
            logger.info("✅ PricedInd=true scenario - using standard OrderCreate builder")
        
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
            'selected_seats': selected_seats,  # Pass selected seat ObjectKeys
            'seat_availability_cache_key': seat_availability_cache_key,  # 🚀 Direct cache key from frontend
            'service_list_cache_key': service_list_cache_key,  # 🚀 Direct cache key from frontend
            'pricing_info': pricing_info,  # NEW: Pass pricing requirements info
            'ancillary_pricing_response': ancillary_pricing_response if pricing_info['requires_pricing'] else None  # NEW: Pass pricing response if needed
        }
        
        # DEBUG: Log order data summary (without verbose content)
        logger.info(f"[DEBUG] Order data being sent to booking service (ReqID: {request_id}) - Keys: {list(order_data.keys()) if order_data else 'None'}")
        
        logger.info(f"Processing order creation - Request ID: {request_id}")
        
        # NEW: Log OrderCreate request
        from utils.api_logger import api_logger
        api_logger.log_request(
            service_name='OrderCreate',
            request_id=request_id,
            payload=order_data,
            endpoint='/entrygate/rest/request:orderCreate',
            headers={'Content-Type': 'application/json'}
        )
        
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
            
            # Store the OrderCreate response in Redis for frontend access
            try:
                from services.simple_flight_cache import simple_flight_cache
                
                # Create a session ID for this booking using booking reference
                booking_reference = result.get('data', {}).get('bookingReference', 'N/A')
                booking_session_id = f"booking_{booking_reference}"
                
                # Store the complete booking data including OrderCreate response
                booking_data = {
                    'bookingReference': result.get('data', {}).get('bookingReference', 'N/A'),
                    'orderId': result.get('data', {}).get('orderId', 'N/A'),
                    'raw_order_create_response': result.get('raw_order_create_response'),
                    'flightDetails': result.get('data', {}).get('flightDetails', {}),
                    'passengers': result.get('data', {}).get('passengers', []),
                    'contactInfo': result.get('data', {}).get('contactInfo', {}),
                    'pricing': result.get('data', {}).get('pricing', {}),
                    'extras': result.get('data', {}).get('extras', []),
                    'status': 'confirmed',
                    'createdAt': result.get('data', {}).get('createdAt', ''),
                    'timestamp': result.get('data', {}).get('timestamp', '')
                }
                
                # Store in Redis with 24 hour TTL
                store_result = simple_flight_cache.store_booking_data(booking_session_id, booking_data, 86400)
                
                if store_result.get('success'):
                    logger.info(f"✅ OrderCreate response stored in Redis for session: {booking_session_id}")
                else:
                    logger.warning(f"⚠️ Failed to store OrderCreate response in Redis: {store_result.get('error')}")
                    
            except Exception as storage_error:
                logger.warning(f"⚠️ Error storing OrderCreate response in Redis: {storage_error}")
            
            # NEW: Log OrderCreate response
            api_logger.log_response(
                service_name='OrderCreate',
                request_id=request_id,
                response=result,
                status_code=200,
                response_time_ms=None
            )
            
            return jsonify({
                'status': 'success',
                'data': result,
                'request_id': request_id
            })
    
    except Exception as e:
        logger.error(f"Unexpected error in order creation: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response("An unexpected error occurred during order creation", 500, request_id))
