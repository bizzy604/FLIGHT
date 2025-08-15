"""
Clean seat availability and service list routes - completely new implementation.
"""
import json
import logging
import uuid
import hashlib
from quart import Blueprint, request, jsonify, current_app
from quart_cors import route_cors
from utils.auth import TokenManager
from scripts.build_seatavailability_rq import build_seatavailability_request
from scripts.build_servicelist_rq import build_servicelist_request
from services.redis_flight_storage import RedisFlightStorage
from services.flight.core import FlightService
from utils.service_list_transformer import transform_service_list_lean_frontend
from utils.seat_availability_transformer import transform_seat_availability_lean_frontend
import aiohttp

logger = logging.getLogger(__name__)

# Shared service instance to prevent token proliferation
_shared_flight_service = None

async def get_shared_flight_service():
    """Get or create a shared FlightService instance to prevent token proliferation."""
    global _shared_flight_service
    if _shared_flight_service is None:
        from quart import current_app
        _shared_flight_service = FlightService(config=dict(current_app.config))
        await _shared_flight_service.__aenter__()
        logger.info("Created shared FlightService instance for seat/service endpoints")
    return _shared_flight_service

# Create a Blueprint with a different name to avoid conflicts
bp = Blueprint('clean_seat_service', __name__, url_prefix='/api/verteil')

# Allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000", 
    "http://localhost:3001", 
    "http://127.0.0.1:3001",
    "https://flight-pearl.vercel.app"
]

def _get_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

def _create_error_response(message: str, status_code: int = 400, request_id: str = None) -> dict:
    """Create a standardized error response."""
    return {
        'status': 'error',
        'message': message,
        'request_id': request_id or _get_request_id()
    }

def _generate_seat_availability_cache_key(flight_price_response: dict, segment_key: str = None) -> str:
    """Generate a deterministic cache key for seat availability parameters."""
    # Extract key identifiers from flight price response
    offer_id = "unknown"
    shopping_response_id = "unknown"
    
    if isinstance(flight_price_response, dict):
        # Try to extract OfferID from the response
        if 'data' in flight_price_response and 'pricedFlightOffers' in flight_price_response['data']:
            offers = flight_price_response['data']['pricedFlightOffers']
            if offers and len(offers) > 0:
                offer_info = offers[0].get('OfferID', {})
                offer_id = offer_info.get('value', 'unknown')
        
        # Try to extract ShoppingResponseID
        if 'data' in flight_price_response:
            shopping_response_id = flight_price_response['data'].get('ShoppingResponseID', 'unknown')
    
    normalized_params = {
        'offer_id': str(offer_id),
        'shopping_response_id': str(shopping_response_id),
        'segment_key': str(segment_key) if segment_key else 'all'
    }
    
    param_string = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_params.items()) if v)
    cache_key = hashlib.md5(param_string.encode()).hexdigest()
    
    logger.debug(f"Generated seat availability cache key: {cache_key} for offer: {offer_id}")
    return f"seat_availability:{cache_key}"

def _generate_service_list_cache_key(flight_price_response: dict) -> str:
    """Generate a deterministic cache key for service list parameters."""
    # Extract key identifiers from flight price response
    offer_id = "unknown"
    shopping_response_id = "unknown"
    
    if isinstance(flight_price_response, dict):
        # Try to extract OfferID from the response
        if 'data' in flight_price_response and 'pricedFlightOffers' in flight_price_response['data']:
            offers = flight_price_response['data']['pricedFlightOffers']
            if offers and len(offers) > 0:
                offer_info = offers[0].get('OfferID', {})
                offer_id = offer_info.get('value', 'unknown')
        
        # Try to extract ShoppingResponseID
        if 'data' in flight_price_response:
            shopping_response_id = flight_price_response['data'].get('ShoppingResponseID', 'unknown')
    
    normalized_params = {
        'offer_id': str(offer_id),
        'shopping_response_id': str(shopping_response_id)
    }
    
    param_string = '|'.join(f"{k}:{v}" for k, v in sorted(normalized_params.items()) if v)
    cache_key = hashlib.md5(param_string.encode()).hexdigest()
    
    logger.debug(f"Generated service list cache key: {cache_key} for offer: {offer_id}")
    return f"service_list:{cache_key}"

@bp.route('/clean-test', methods=['GET'])
async def clean_test():
    """Test endpoint to verify clean routes work."""
    return jsonify({
        'status': 'success',
        'message': 'CLEAN ROUTES WORKING!',
        'timestamp': str(uuid.uuid4())
    })

@bp.route('/seat-availability/cache-check', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_seat_availability_cache():
    """
    Check if seat availability data exists in cache.
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Seat availability cache check request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json() or {}
        
        flight_price_cache_key = data.get('flight_price_cache_key')
        flight_price_response = data.get('flight_price_response')
        segment_key = data.get('segment_key')
        
        # Prefer cache key approach for retrieving raw response
        if flight_price_cache_key:
            try:
                redis_storage = RedisFlightStorage()
                cached_result = redis_storage.get_flight_price(flight_price_cache_key)
                if cached_result['success']:
                    flight_price_response = cached_result['data']
                    logger.info(f"Retrieved flight price response from cache key for cache check: {flight_price_cache_key}")
                else:
                    logger.warning(f"Failed to retrieve flight price response from cache key: {flight_price_cache_key}")
            except Exception as cache_error:
                logger.error(f"Error retrieving flight price response from cache: {cache_error}")
        
        if not flight_price_response:
            return jsonify({
                'status': 'cache_miss',
                'message': 'Missing flight_price_response or flight_price_cache_key for cache check',
                'request_id': request_id
            })
        
        # Generate cache key from the flight price response
        cache_key = _generate_seat_availability_cache_key(flight_price_response, segment_key)
        
        # Try to retrieve cached data from Redis
        redis_storage = RedisFlightStorage()
        cached_result = redis_storage.get_seat_availability(cache_key)
        
        if cached_result['success']:
            logger.info(f"Seat availability cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'data': cached_result['data'],
                'cache_key': cache_key,
                'request_id': request_id,
                'message': 'Cached seat availability data found'
            })
        else:
            logger.info(f"Seat availability cache miss for key: {cache_key} - Request ID: {request_id}")
            return jsonify({
                'status': 'cache_miss',
                'message': 'No cached seat availability data found',
                'cache_key': cache_key,
                'request_id': request_id
            })
        
    except Exception as e:
        logger.error(f"Seat availability cache check failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Cache check failed: {str(e)}", 500, request_id))

@bp.route('/service-list/cache-check', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_service_list_cache():
    """
    Check if service list data exists in cache.
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Service list cache check request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json() or {}
        
        flight_price_cache_key = data.get('flight_price_cache_key')
        flight_price_response = data.get('flight_price_response')
        
        # Prefer cache key approach for retrieving raw response
        if flight_price_cache_key:
            try:
                redis_storage = RedisFlightStorage()
                cached_result = redis_storage.get_flight_price(flight_price_cache_key)
                if cached_result['success']:
                    flight_price_response = cached_result['data']
                    logger.info(f"Retrieved flight price response from cache key for cache check: {flight_price_cache_key}")
                else:
                    logger.warning(f"Failed to retrieve flight price response from cache key: {flight_price_cache_key}")
            except Exception as cache_error:
                logger.error(f"Error retrieving flight price response from cache: {cache_error}")
        
        if not flight_price_response:
            return jsonify({
                'status': 'cache_miss',
                'message': 'Missing flight_price_response or flight_price_cache_key for cache check',
                'request_id': request_id
            })
        
        # Generate cache key from the flight price response
        cache_key = _generate_service_list_cache_key(flight_price_response)
        
        # Try to retrieve cached data from Redis
        redis_storage = RedisFlightStorage()
        cached_result = redis_storage.get_service_list(cache_key)
        
        if cached_result['success']:
            logger.info(f"Service list cache hit for key: {cache_key} - Request ID: {request_id}")
            
            # Return cached data with success status
            return jsonify({
                'status': 'success',
                'data': cached_result['data'],
                'cache_key': cache_key,
                'request_id': request_id,
                'message': 'Cached service list data found'
            })
        else:
            logger.info(f"Service list cache miss for key: {cache_key} - Request ID: {request_id}")
            return jsonify({
                'status': 'cache_miss',
                'message': 'No cached service list data found',
                'cache_key': cache_key,
                'request_id': request_id
            })
        
    except Exception as e:
        logger.error(f"Service list cache check failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Cache check failed: {str(e)}", 500, request_id))

@bp.route('/seat-availability', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def get_seat_availability():
    """
    CLEAN seat availability endpoint - completely bypasses old problematic code.
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"CLEAN SEAT ENDPOINT HIT - Request ID: {request_id}")
        logger.info(f"CLEAN SeatAvailability request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_cache_key = data.get('flight_price_cache_key')
        flight_price_response = data.get('flight_price_response')

        # Use cache_manager to get RAW flight price response (not Redis storage which has transformed data)
        if flight_price_cache_key:
            try:
                from utils.cache_manager import cache_manager
                logger.info(f"Attempting to retrieve RAW flight price response from cache with key: {flight_price_cache_key}")
                flight_price_response = cache_manager.get(flight_price_cache_key)
                if flight_price_response:
                    logger.info(f"✅ Successfully retrieved RAW flight price response from cache key: {flight_price_cache_key}")
                    logger.info(f"Retrieved response type: {type(flight_price_response)}, keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
                    # Check if it's wrapped in FlightPriceRS structure and unwrap for build script
                    if isinstance(flight_price_response, dict) and 'FlightPriceRS' in flight_price_response:
                        flight_price_response = flight_price_response['FlightPriceRS']
                        logger.info("Unwrapped FlightPriceRS structure for build script")
                else:
                    logger.warning(f"❌ RAW flight price response not found in cache: {flight_price_cache_key}")
                    # Check what keys exist in cache_manager (for debugging)
                    try:
                        cache_keys = list(cache_manager._cache.keys())
                        logger.info(f"Available cache keys: {cache_keys}")
                        # Look for similar keys
                        similar_keys = [k for k in cache_keys if 'flight_price_raw' in k]
                        logger.info(f"Similar flight_price_raw keys found: {similar_keys}")
                    except Exception:
                        logger.info("Could not inspect cache keys")
                    return jsonify(_create_error_response("Flight price data expired. Please request new pricing.", 404, request_id))
            except Exception as cache_error:
                logger.error(f"Error retrieving RAW flight price response from cache: {cache_error}")
                return jsonify(_create_error_response(f"Cache retrieval error: {cache_error}", 500, request_id))

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response or flight_price_cache_key is required", 400, request_id))

        # CRITICAL VALIDATION: Reject transformed responses, only accept raw NDC responses
        if isinstance(flight_price_response, dict):
            response_keys = list(flight_price_response.keys())
            # Check for transformed response indicators (these keys should NOT be present in raw NDC responses)
            transformed_keys = ['direction', 'fare_family', 'flight_segments', 'offer_id', 'original_offer_id', 'passengers', 'time_limits', 'total_price']
            if any(key in response_keys for key in transformed_keys):
                logger.error(f"❌ Rejected transformed flight price response with keys: {response_keys}")
                logger.error("Frontend sent transformed data instead of using flight_price_cache_key. This will cause API failures.")
                return jsonify(_create_error_response(
                    "Invalid request: Transformed flight price data detected. Please use flight_price_cache_key parameter to retrieve raw NDC response.", 
                    400, 
                    request_id
                ))
            
            # Check for required raw NDC response keys
            required_ndc_keys = ['PricedFlightOffers', 'DataLists']
            missing_keys = [key for key in required_ndc_keys if key not in response_keys]
            if missing_keys:
                logger.error(f"❌ Missing required NDC keys in flight price response: {missing_keys}")
                logger.error(f"Available keys: {response_keys}")
                return jsonify(_create_error_response(
                    f"Invalid flight price response: Missing required NDC keys: {missing_keys}. Please ensure raw NDC response is provided.", 
                    400, 
                    request_id
                ))
            
            logger.info(f"✅ Validated raw NDC flight price response with keys: {response_keys}")

        print(f"Building seat availability request...")
        print(f"Flight price response keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
        print(f"Flight price response type: {type(flight_price_response)}")
        
        # Build the request using the working script - always use index 0 since flight price response contains only one offer
        seatavailability_request = build_seatavailability_request(
            flight_price_response, 0
        )
        print(f"Built request successfully")
        
        # Extract airline code from flight price response for proper ThirdpartyId handling
        airline_code = None
        try:
            if 'PricedFlightOffers' in flight_price_response:
                priced_offers = flight_price_response['PricedFlightOffers'].get('PricedFlightOffer', [])
                if not isinstance(priced_offers, list):
                    priced_offers = [priced_offers] if priced_offers else []
                if priced_offers:
                    offer_id = priced_offers[0].get('OfferID', {})
                    airline_code = offer_id.get('Owner')
                    print(f"Extracted airline code for SeatAvailability: {airline_code}")
        except Exception as e:
            logger.warning(f"Could not extract airline code for SeatAvailability: {e}")
        
        # Use shared FlightService to prevent token proliferation
        flight_service = await get_shared_flight_service()
        
        # Make API call using centralized service with airline-specific ThirdpartyId
        print(f"Making SeatAvailability API call via shared service (airline: {airline_code})...")
        result = await flight_service._make_request(
            endpoint='/entrygate/rest/request:preSeatAvailability',
            payload=seatavailability_request,
            service_name='SeatAvailability',
            airline_code=airline_code,
            request_id=request_id
        )
                
        print(f"SeatAvailability API call successful via shared service")
        logger.info(f"SeatAvailability request completed via shared service - Request ID: {request_id}")
        
        # Transform the raw API response for frontend consumption
        print(f"Transforming SeatAvailability response for frontend...")
        try:
            transformed_result = transform_seat_availability_lean_frontend(result)
            
            if transformed_result['status'] == 'success':
                logger.info(f"Successfully transformed SeatAvailability response - Request ID: {request_id}")
                final_data = transformed_result['data']
            else:
                logger.warning(f"SeatAvailability transformation failed: {transformed_result.get('error')} - Request ID: {request_id}")
                final_data = transformed_result['data']  # Use fallback data
                
        except Exception as transform_error:
            logger.error(f"Error transforming SeatAvailability response: {str(transform_error)} - Request ID: {request_id}")
            # Fallback to raw data if transformation fails - use lean frontend format
            final_data = {
                "flights": [{
                    "cabin": [{
                        "seatDisplay": {
                            "columns": [{"value": "A", "position": "W"}],
                            "rows": {"first": 1, "last": 30, "upperDeckInd": False},
                            "component": []
                        }
                    }]
                }],
                "dataLists": {
                    "seatList": {
                        "seats": []
                    }
                },
                "raw_response": result  # Include raw data for debugging
            }
        
        # Cache the transformed result
        try:
            cache_key = _generate_seat_availability_cache_key(flight_price_response, data.get('segment_key'))
            redis_storage = RedisFlightStorage()
            cache_result = redis_storage.store_seat_availability(
                seat_data=final_data,  # Cache the transformed data
                session_id=cache_key,
                ttl=300  # 5 minutes
            )
            if cache_result['success']:
                logger.info(f"💾 Cached transformed seat availability data for key: {cache_key} - Request ID: {request_id}")
            else:
                logger.warning(f"Failed to cache seat availability data: {cache_result.get('message')} - Request ID: {request_id}")
        except Exception as cache_error:
            logger.error(f"Error caching seat availability data: {str(cache_error)} - Request ID: {request_id}")
        
        return jsonify({
            'status': 'success',
            'data': final_data,
            'request_id': request_id,
            'cache_key': cache_key,
            'message': 'SeatAvailability successfully transformed for frontend'
        })
                
    except Exception as e:
        print(f"ERROR in clean seat endpoint: {str(e)}")
        logger.error(f"CLEAN SeatAvailability request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"CLEAN SeatAvailability request failed: {str(e)}", 500, request_id))


@bp.route('/service-list', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def get_service_list():
    """
    CLEAN service list endpoint - completely bypasses old problematic code.
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"CLEAN SERVICE ENDPOINT HIT - Request ID: {request_id}")
        logger.info(f"CLEAN ServiceList request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_cache_key = data.get('flight_price_cache_key')
        flight_price_response = data.get('flight_price_response')

        # Use cache_manager to get RAW flight price response (not Redis storage which has transformed data)
        if flight_price_cache_key:
            try:
                from utils.cache_manager import cache_manager
                logger.info(f"Attempting to retrieve RAW flight price response from cache with key: {flight_price_cache_key}")
                flight_price_response = cache_manager.get(flight_price_cache_key)
                if flight_price_response:
                    logger.info(f"✅ Successfully retrieved RAW flight price response from cache key: {flight_price_cache_key}")
                    logger.info(f"Retrieved response type: {type(flight_price_response)}, keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
                    # Check if it's wrapped in FlightPriceRS structure and unwrap for build script
                    if isinstance(flight_price_response, dict) and 'FlightPriceRS' in flight_price_response:
                        flight_price_response = flight_price_response['FlightPriceRS']
                        logger.info("Unwrapped FlightPriceRS structure for build script")
                else:
                    logger.warning(f"❌ RAW flight price response not found in cache: {flight_price_cache_key}")
                    # Check what keys exist in cache_manager (for debugging)
                    try:
                        cache_keys = list(cache_manager._cache.keys())
                        logger.info(f"Available cache keys: {cache_keys}")
                        # Look for similar keys
                        similar_keys = [k for k in cache_keys if 'flight_price_raw' in k]
                        logger.info(f"Similar flight_price_raw keys found: {similar_keys}")
                    except Exception:
                        logger.info("Could not inspect cache keys")
                    return jsonify(_create_error_response("Flight price data expired. Please request new pricing.", 404, request_id))
            except Exception as cache_error:
                logger.error(f"Error retrieving RAW flight price response from cache: {cache_error}")
                return jsonify(_create_error_response(f"Cache retrieval error: {cache_error}", 500, request_id))

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response or flight_price_cache_key is required", 400, request_id))

        # CRITICAL VALIDATION: Reject transformed responses, only accept raw NDC responses
        if isinstance(flight_price_response, dict):
            response_keys = list(flight_price_response.keys())
            # Check for transformed response indicators (these keys should NOT be present in raw NDC responses)
            transformed_keys = ['direction', 'fare_family', 'flight_segments', 'offer_id', 'original_offer_id', 'passengers', 'time_limits', 'total_price']
            if any(key in response_keys for key in transformed_keys):
                logger.error(f"❌ Rejected transformed flight price response with keys: {response_keys}")
                logger.error("Frontend sent transformed data instead of using flight_price_cache_key. This will cause API failures.")
                return jsonify(_create_error_response(
                    "Invalid request: Transformed flight price data detected. Please use flight_price_cache_key parameter to retrieve raw NDC response.", 
                    400, 
                    request_id
                ))
            
            # Check for required raw NDC response keys
            required_ndc_keys = ['PricedFlightOffers', 'DataLists']
            missing_keys = [key for key in required_ndc_keys if key not in response_keys]
            if missing_keys:
                logger.error(f"❌ Missing required NDC keys in flight price response: {missing_keys}")
                logger.error(f"Available keys: {response_keys}")
                return jsonify(_create_error_response(
                    f"Invalid flight price response: Missing required NDC keys: {missing_keys}. Please ensure raw NDC response is provided.", 
                    400, 
                    request_id
                ))
            
            logger.info(f"✅ Validated raw NDC flight price response with keys: {response_keys}")

        print(f"Building service list request...")
        print(f"Flight price response keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
        print(f"Flight price response type: {type(flight_price_response)}")
        
        # Build the request using the working script - always use index 0 since flight price response contains only one offer
        servicelist_request = build_servicelist_request(
            flight_price_response, 0
        )
        print(f"Built request successfully")
        
        # Extract airline code from flight price response for proper ThirdpartyId handling
        airline_code = None
        try:
            if 'PricedFlightOffers' in flight_price_response:
                priced_offers = flight_price_response['PricedFlightOffers'].get('PricedFlightOffer', [])
                if not isinstance(priced_offers, list):
                    priced_offers = [priced_offers] if priced_offers else []
                if priced_offers:
                    offer_id = priced_offers[0].get('OfferID', {})
                    airline_code = offer_id.get('Owner')
                    print(f"Extracted airline code for ServiceList: {airline_code}")
        except Exception as e:
            logger.warning(f"Could not extract airline code for ServiceList: {e}")
        
        # Use shared FlightService to prevent token proliferation
        flight_service = await get_shared_flight_service()
        
        # Make API call using centralized service with airline-specific ThirdpartyId
        print(f"Making ServiceList API call via shared service (airline: {airline_code})...")
        result = await flight_service._make_request(
            endpoint='/entrygate/rest/request:preServiceList',
            payload=servicelist_request,
            service_name='ServiceList',
            airline_code=airline_code,
            request_id=request_id
        )
                
        print(f"ServiceList API call successful via shared service")
        logger.info(f"ServiceList request completed via shared service - Request ID: {request_id}")
        
        # Transform the raw API response for frontend consumption
        print(f"Transforming ServiceList response for frontend...")
        try:
            transformed_result = transform_service_list_lean_frontend(result)
            
            if transformed_result['status'] == 'success':
                logger.info(f"Successfully transformed ServiceList response - Request ID: {request_id}")
                final_data = transformed_result['data']
            else:
                logger.warning(f"ServiceList transformation failed: {transformed_result.get('error')} - Request ID: {request_id}")
                final_data = transformed_result['data']  # Use fallback data
                
        except Exception as transform_error:
            logger.error(f"Error transforming ServiceList response: {str(transform_error)} - Request ID: {request_id}")
            # Fallback to raw data if transformation fails - use lean frontend format
            final_data = {
                "services": {
                    "service": []
                },
                "shoppingResponseId": {
                    "responseId": {
                        "value": "unknown"
                    }
                },
                "raw_response": result  # Include raw data for debugging
            }
        
        # Cache the transformed result
        try:
            cache_key = _generate_service_list_cache_key(flight_price_response)
            redis_storage = RedisFlightStorage()
            cache_result = redis_storage.store_service_list(
                service_data=final_data,  # Cache the transformed data
                session_id=cache_key,
                ttl=300  # 5 minutes
            )
            if cache_result['success']:
                logger.info(f"💾 Cached transformed service list data for key: {cache_key} - Request ID: {request_id}")
            else:
                logger.warning(f"Failed to cache service list data: {cache_result.get('message')} - Request ID: {request_id}")
        except Exception as cache_error:
            logger.error(f"Error caching service list data: {str(cache_error)} - Request ID: {request_id}")
        
        return jsonify({
            'status': 'success',
            'data': final_data,
            'request_id': request_id,
            'cache_key': cache_key,
            'message': 'ServiceList successfully transformed for frontend'
        })
                
    except Exception as e:
        print(f"ERROR in clean service endpoint: {str(e)}")
        logger.error(f"CLEAN ServiceList request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"CLEAN ServiceList request failed: {str(e)}", 500, request_id))