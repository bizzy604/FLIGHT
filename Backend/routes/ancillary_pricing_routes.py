"""
Ancillary pricing routes for handling PricedInd=false scenarios.
These endpoints handle additional FlightPrice calls for pricing selected services and seats.
"""
import json
import logging
import uuid
from quart import Blueprint, request, jsonify, current_app
from quart_cors import route_cors
from utils.auth import TokenManager
from utils.api_logger import api_logger
from scripts.build_flightprice_ancillary_rq import (
    build_flightprice_ancillary_request,
    detect_pricing_required
)
from services.simple_flight_cache import SimpleFlightCache
import aiohttp

logger = logging.getLogger(__name__)

# Initialize cache manager
simple_flight_cache = SimpleFlightCache()

# Create a Blueprint for ancillary pricing routes
bp = Blueprint('ancillary_pricing', __name__, url_prefix='/api/verteil')

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

def _create_error_response(message: str, status_code: int = 400, request_id: str = None) -> tuple:
    """Create a standardized error response with status code."""
    return (
        {
            'status': 'error',
            'message': message,
            'request_id': request_id or _get_request_id()
        },
        status_code
    )

@bp.route('/pricing/check-requirements', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def check_pricing_requirements():
    """
    Check if selected services and seats require additional pricing.
    
    POST JSON Body:
    - servicelist_response: ServiceList response data
    - seatavailability_response: SeatAvailability response data
    - selected_services: List of selected service ObjectKeys
    - selected_seats: List of selected seat ObjectKeys
    
    Returns:
    - Pricing requirements analysis
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Checking pricing requirements - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])

        # Detect pricing requirements
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        logger.info(f"Pricing requirements check completed - Request ID: {request_id}")
        
        return jsonify({
            'status': 'success',
            'data': pricing_info,
            'request_id': request_id
        })
                
    except Exception as e:
        logger.error(f"Pricing requirements check failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Pricing requirements check failed: {str(e)}", 500, request_id))

@bp.route('/pricing/price-ancillaries', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def price_ancillaries():
    """
    Price selected services and seats using FlightPrice API.
    
    POST JSON Body:
    - flight_price_cache_key: Cache key for retrieving raw flight price response (PREFERRED)
    - seat_availability_cache_key: Cache key for retrieving seat availability response (PREFERRED)
    - service_list_cache_key: Cache key for retrieving service list response (PREFERRED)
    - flight_price_response: Original FlightPrice response (FALLBACK - will be deprecated)
    - servicelist_response: ServiceList response data (FALLBACK - will be deprecated)
    - seatavailability_response: SeatAvailability response data (FALLBACK - will be deprecated)
    - selected_services: List of selected service ObjectKeys
    - selected_seats: List of selected seat ObjectKeys
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Priced FlightPrice response with selected services and seats
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Pricing ancillaries request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        flight_price_cache_key = data.get('flight_price_cache_key')
        servicelist_response = data.get('servicelist_response')
        seatavailability_response = data.get('seatavailability_response')
        seat_availability_cache_key = data.get('seat_availability_cache_key')
        service_list_cache_key = data.get('service_list_cache_key')
        selected_services = data.get('selected_services', [])
        selected_seats = data.get('selected_seats', [])
        selected_offer_index = data.get('selected_offer_index', 0)

        # 🚀 CRITICAL FIX: Retrieve RAW flight price response from Redis using cache key
        # This matches the pattern used by seat and service endpoints
        if flight_price_cache_key:
            try:
                logger.info(f"Attempting to retrieve RAW flight price response from cache with key: {flight_price_cache_key}")
                cached_result = simple_flight_cache.get_flight_price(flight_price_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    flight_price_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved RAW flight price response from Redis key: {flight_price_cache_key}")
                    logger.info(f"Retrieved response type: {type(flight_price_response)}, keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
                    
                    # Check if it's wrapped in FlightPriceRS structure and unwrap for build script
                    if isinstance(flight_price_response, dict) and 'FlightPriceRS' in flight_price_response:
                        flight_price_response = flight_price_response['FlightPriceRS']
                        logger.info("Unwrapped FlightPriceRS structure for build script")
                        logger.info(f"After unwrap - keys: {list(flight_price_response.keys()) if isinstance(flight_price_response, dict) else 'Not a dict'}")
                    
                    # Verify critical fields are present
                    if isinstance(flight_price_response, dict):
                        has_shopping_id = 'ShoppingResponseID' in flight_price_response
                        has_offers = 'PricedFlightOffers' in flight_price_response
                        has_datalists = 'DataLists' in flight_price_response
                        logger.info(f"🔍 Flight Price Structure Check: ShoppingResponseID={has_shopping_id}, PricedFlightOffers={has_offers}, DataLists={has_datalists}")
                        
                        if has_shopping_id:
                            shopping_id_node = flight_price_response.get('ShoppingResponseID', {})
                            response_id_value = shopping_id_node.get('ResponseID', {}).get('value')
                            logger.info(f"✅ ShoppingResponseID found: {response_id_value}")
                        else:
                            logger.error("❌ ShoppingResponseID MISSING from flight price response!")
                else:
                    logger.warning(f"❌ RAW flight price response not found in Redis: {flight_price_cache_key}")
                    logger.warning(f"Redis result: {cached_result}")
                    return jsonify(_create_error_response("Flight price data expired or not found. Please request new pricing.", 404, request_id))
            except Exception as cache_error:
                logger.error(f"Error retrieving RAW flight price response from Redis: {cache_error}")
                return jsonify(_create_error_response(f"Cache retrieval error: {cache_error}", 500, request_id))

        # 🚀 NEW: Retrieve seat availability response from Redis if cache key provided
        if seat_availability_cache_key and not seatavailability_response:
            try:
                logger.info(f"Attempting to retrieve seat availability response from cache with key: {seat_availability_cache_key}")
                cached_result = simple_flight_cache.get_seat_availability(seat_availability_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    seatavailability_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved seat availability response from Redis key: {seat_availability_cache_key}")
                    
                    # Check if we need to extract raw_response for build script
                    if isinstance(seatavailability_response, dict) and 'raw_response' in seatavailability_response:
                        seatavailability_response = seatavailability_response['raw_response']
                        logger.info("Extracted raw_response from seat availability data for build script")
                else:
                    logger.warning(f"⚠️ Seat availability response not found in Redis: {seat_availability_cache_key}")
                    logger.info("Continuing without seat availability data - seats won't be priced")
            except Exception as cache_error:
                logger.warning(f"Error retrieving seat availability response from Redis: {cache_error}")
                logger.info("Continuing without seat availability data - seats won't be priced")

        # 🚀 NEW: Retrieve service list response from Redis if cache key provided
        if service_list_cache_key and not servicelist_response:
            try:
                logger.info(f"Attempting to retrieve service list response from cache with key: {service_list_cache_key}")
                cached_result = simple_flight_cache.get_service_list(service_list_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    servicelist_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved service list response from Redis key: {service_list_cache_key}")
                    
                    # Check if we need to extract raw_response for build script
                    if isinstance(servicelist_response, dict) and 'raw_response' in servicelist_response:
                        servicelist_response = servicelist_response['raw_response']
                        logger.info("Extracted raw_response from service list data for build script")
                else:
                    logger.warning(f"⚠️ Service list response not found in Redis: {service_list_cache_key}")
                    logger.info("Continuing without service list data - services won't be priced")
            except Exception as cache_error:
                logger.warning(f"Error retrieving service list response from Redis: {cache_error}")
                logger.info("Continuing without service list data - services won't be priced")

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

        # Log data availability status
        logger.info("📊 Data Availability Status:")
        logger.info(f"  ✅ Flight Price Response: {'Available' if flight_price_response else 'Missing'}")
        logger.info(f"  {'✅' if seatavailability_response else '⚠️'} Seat Availability Response: {'Available' if seatavailability_response else 'Not Available'}")
        logger.info(f"  {'✅' if servicelist_response else '⚠️'} Service List Response: {'Available' if servicelist_response else 'Not Available'}")

        # Check if pricing is actually required
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        if not pricing_info['requires_pricing']:
            logger.info(f"No pricing required, returning original response - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': flight_price_response,
                'pricing_info': pricing_info,
                'request_id': request_id,
                'message': 'No additional pricing required'
            })

        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Extract airline code from flight_price_response for ThirdPartyId header
        airline_code = None
        try:
            # Try to get airline from PricedFlightOffers > OfferID > Owner
            priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if isinstance(priced_offers, list) and len(priced_offers) > 0:
                airline_code = priced_offers[0].get('OfferID', {}).get('Owner')
            elif isinstance(priced_offers, dict):
                airline_code = priced_offers.get('OfferID', {}).get('Owner')
            
            # Fallback: Try ShoppingResponseID Owner
            if not airline_code:
                airline_code = flight_price_response.get('ShoppingResponseID', {}).get('Owner')
            
            logger.info(f"Extracted airline code for ThirdPartyId: {airline_code}")
        except Exception as e:
            logger.warning(f"Could not extract airline code: {e}")
        
        # 🚀 CRITICAL FIX: Separate pricing for services and seats per NDC specification
        # According to reference examples (9_FlightPriceRQ.json), ancillary items should be 
        # priced separately, not all together in one request
        
        from scripts.build_flightprice_ancillary_rq import (
            build_flightprice_request_for_services,
            build_flightprice_request_for_seats
        )
        
        config = current_app.config
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice"
        
        # Determine which pricing calls are needed
        has_services = pricing_info.get('services_require_pricing', [])
        has_seats = pricing_info.get('seats_require_pricing', [])
        
        logger.info(f"🔍 Pricing Strategy: Services={len(has_services)}, Seats={len(has_seats)}")
        
        final_result = None
        intermediate_offer_id = None
        
        # STEP 1: Price services first (if any)
        if has_services and servicelist_response:
            logger.info(f"📦 STEP 1: Pricing {len(has_services)} services")
            
            services_request = build_flightprice_request_for_services(
                flight_price_response=flight_price_response,
                servicelist_response=servicelist_response,
                selected_services=selected_services,
                selected_offer_index=selected_offer_index
            )
            
            # Create headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Authorization': bearer_token,
                'OfficeId': config.get('VERTEIL_OFFICE_ID'),
                'ThirdpartyId': airline_code if airline_code else config.get('VERTEIL_THIRD_PARTY_ID', ''),
                'service': 'FlightPrice',
                'User-Agent': 'PostmanRuntime/7.41',
                'Cache-Control': 'no-cache',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Log request
            api_logger.log_request(
                service_name='AncillaryPricing_Services',
                request_id=f"{request_id}_services",
                payload=services_request,
                endpoint='/entrygate/rest/request:preFlightPrice',
                headers=headers
            )
            
            # Make API call for services
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=services_request, timeout=30) as response:
                    services_result = await response.json()
                    
                    logger.info(f"✅ Services pricing completed - Status: {response.status}")
                    
                    # Log response
                    api_logger.log_response(
                        service_name='AncillaryPricing_Services',
                        request_id=f"{request_id}_services",
                        response=services_result,
                        status_code=response.status
                    )
                    
                    # Check for errors
                    if 'Errors' in services_result:
                        logger.error(f"❌ Services pricing failed: {services_result.get('Errors')}")
                        return jsonify({
                            'status': 'error',
                            'message': 'Services pricing failed',
                            'data': services_result,
                            'request_id': request_id
                        })
                    
                    # Extract the new OfferID for chaining
                    if 'PricedFlightOffers' in services_result:
                        priced_offers = services_result['PricedFlightOffers'].get('PricedFlightOffer', [])
                        if isinstance(priced_offers, list) and len(priced_offers) > 0:
                            intermediate_offer_id = priced_offers[0].get('OfferID', {}).get('value')
                            logger.info(f"🔗 Extracted new OfferID for chaining: {intermediate_offer_id}")
                    
                    final_result = services_result
        
        # STEP 2: Price seats (if any)
        if has_seats and seatavailability_response:
            logger.info(f"💺 STEP 2: Pricing {len(has_seats)} seats")
            
            # If we priced services first, use the intermediate offer ID
            # Otherwise use the original flight price response
            base_response = final_result if final_result else flight_price_response
            
            seats_request = build_flightprice_request_for_seats(
                flight_price_response=base_response,
                seatavailability_response=seatavailability_response,
                selected_seats=selected_seats,
                selected_offer_index=selected_offer_index,
                base_offer_id=intermediate_offer_id  # Chain with previous pricing if available
            )
            
            # Create headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Authorization': bearer_token,
                'OfficeId': config.get('VERTEIL_OFFICE_ID'),
                'ThirdpartyId': airline_code if airline_code else config.get('VERTEIL_THIRD_PARTY_ID', ''),
                'service': 'FlightPrice',
                'User-Agent': 'PostmanRuntime/7.41',
                'Cache-Control': 'no-cache',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Log request
            api_logger.log_request(
                service_name='AncillaryPricing_Seats',
                request_id=f"{request_id}_seats",
                payload=seats_request,
                endpoint='/entrygate/rest/request:preFlightPrice',
                headers=headers
            )
            
            # Make API call for seats
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=seats_request, timeout=30) as response:
                    seats_result = await response.json()
                    
                    logger.info(f"✅ Seats pricing completed - Status: {response.status}")
                    
                    # Log response
                    api_logger.log_response(
                        service_name='AncillaryPricing_Seats',
                        request_id=f"{request_id}_seats",
                        response=seats_result,
                        status_code=response.status
                    )
                    
                    # Check for errors
                    if 'Errors' in seats_result:
                        logger.error(f"❌ Seats pricing failed: {seats_result.get('Errors')}")
                        return jsonify({
                            'status': 'error',
                            'message': 'Seats pricing failed',
                            'data': seats_result,
                            'request_id': request_id
                        })
                    
                    final_result = seats_result
        
        # Ensure we have a result
        if not final_result:
            logger.error("❌ No pricing result generated")
            return jsonify(_create_error_response("No pricing result generated", 500, request_id))
        
        # CRITICAL FIX: Ensure ShoppingResponseID is preserved in the result
        if final_result and 'ShoppingResponseID' not in final_result:
            # Copy ShoppingResponseID from original flight_price_response
            if 'ShoppingResponseID' in flight_price_response:
                final_result['ShoppingResponseID'] = flight_price_response['ShoppingResponseID']
                logger.info(f"✅ Copied ShoppingResponseID to ancillary pricing result")
            else:
                logger.warning("⚠️ ShoppingResponseID not found in original flight price response")
        elif final_result and 'ShoppingResponseID' in final_result:
            shopping_id_value = final_result['ShoppingResponseID'].get('ResponseID', {}).get('value')
            logger.info(f"✅ ShoppingResponseID already in result: {shopping_id_value}")
        
        logger.info(f"🎉 Ancillary pricing completed successfully - Request ID: {request_id}")
        
        return jsonify({
            'status': 'success',
            'data': final_result,
            'pricing_info': pricing_info,
            'request_id': request_id,
            'pricing_strategy': {
                'services_priced': len(has_services) > 0,
                'seats_priced': len(has_seats) > 0,
                'sequential': len(has_services) > 0 and len(has_seats) > 0
            }
        })
                
    except Exception as e:
        logger.error(f"Ancillary pricing request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Ancillary pricing request failed: {str(e)}", 500, request_id))

@bp.route('/pricing/price-services-only', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def price_services_only():
    """
    Price only selected services (no seats).
    
    POST JSON Body:
    - flight_price_cache_key: Cache key for retrieving raw flight price response (PREFERRED)
    - flight_price_response: Original FlightPrice response (FALLBACK - will be deprecated)
    - servicelist_response: ServiceList response data
    - selected_services: List of selected service ObjectKeys
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Priced FlightPrice response with selected services
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Pricing services only request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        flight_price_cache_key = data.get('flight_price_cache_key')
        servicelist_response = data.get('servicelist_response')
        service_list_cache_key = data.get('service_list_cache_key')
        selected_services = data.get('selected_services', [])
        selected_offer_index = data.get('selected_offer_index', 0)

        # 🚀 CRITICAL FIX: Retrieve RAW flight price response from Redis using cache key
        if flight_price_cache_key:
            try:
                logger.info(f"Attempting to retrieve RAW flight price response from cache with key: {flight_price_cache_key}")
                cached_result = simple_flight_cache.get_flight_price(flight_price_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    flight_price_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved RAW flight price response from Redis key: {flight_price_cache_key}")
                    
                    # Check if it's wrapped in FlightPriceRS structure and unwrap
                    if isinstance(flight_price_response, dict) and 'FlightPriceRS' in flight_price_response:
                        flight_price_response = flight_price_response['FlightPriceRS']
                        logger.info("Unwrapped FlightPriceRS structure for build script")
                else:
                    logger.warning(f"❌ RAW flight price response not found in Redis: {flight_price_cache_key}")
                    return jsonify(_create_error_response("Flight price data expired or not found. Please request new pricing.", 404, request_id))
            except Exception as cache_error:
                logger.error(f"Error retrieving RAW flight price response from Redis: {cache_error}")
                return jsonify(_create_error_response(f"Cache retrieval error: {cache_error}", 500, request_id))

        # 🚀 NEW: Retrieve service list response from Redis if cache key provided
        if service_list_cache_key and not servicelist_response:
            try:
                logger.info(f"Attempting to retrieve service list response from cache with key: {service_list_cache_key}")
                cached_result = simple_flight_cache.get_service_list(service_list_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    servicelist_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved service list response from Redis key: {service_list_cache_key}")
                    
                    # Check if we need to extract raw_response for build script
                    if isinstance(servicelist_response, dict) and 'raw_response' in servicelist_response:
                        servicelist_response = servicelist_response['raw_response']
                        logger.info("Extracted raw_response from service list data for build script")
                else:
                    logger.warning(f"⚠️ Service list response not found in Redis: {service_list_cache_key}")
                    logger.info("Continuing without service list data - services won't be priced")
            except Exception as cache_error:
                logger.warning(f"Error retrieving service list response from Redis: {cache_error}")
                logger.info("Continuing without service list data - services won't be priced")

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response or flight_price_cache_key is required", 400, request_id))

        # CRITICAL VALIDATION: Validate raw NDC response
        if isinstance(flight_price_response, dict):
            response_keys = list(flight_price_response.keys())
            required_ndc_keys = ['PricedFlightOffers', 'DataLists']
            missing_keys = [key for key in required_ndc_keys if key not in response_keys]
            if missing_keys:
                logger.error(f"❌ Missing required NDC keys in flight price response: {missing_keys}")
                return jsonify(_create_error_response(
                    f"Invalid flight price response: Missing required NDC keys: {missing_keys}.", 
                    400, 
                    request_id
                ))
            logger.info(f"✅ Validated raw NDC flight price response with keys: {response_keys}")

        # Check if pricing is required for services
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            selected_services=selected_services
        )
        
        if not pricing_info['requires_pricing']:
            logger.info(f"No service pricing required - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': flight_price_response,
                'pricing_info': pricing_info,
                'request_id': request_id,
                'message': 'No additional pricing required for services'
            })

        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Extract airline code from flight_price_response for ThirdPartyId header
        airline_code = None
        try:
            # Try to get airline from PricedFlightOffers > OfferID > Owner
            priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if isinstance(priced_offers, list) and len(priced_offers) > 0:
                airline_code = priced_offers[0].get('OfferID', {}).get('Owner')
            elif isinstance(priced_offers, dict):
                airline_code = priced_offers.get('OfferID', {}).get('Owner')
            
            # Fallback: Try ShoppingResponseID Owner
            if not airline_code:
                airline_code = flight_price_response.get('ShoppingResponseID', {}).get('Owner')
            
            logger.info(f"Extracted airline code for ThirdPartyId: {airline_code}")
        except Exception as e:
            logger.warning(f"Could not extract airline code: {e}")
        
        # Build the service pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            servicelist_response=servicelist_response,
            selected_services=selected_services,
            selected_offer_index=selected_offer_index
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'ThirdpartyId': airline_code if airline_code else config.get('VERTEIL_THIRD_PARTY_ID', ''),
            'service': 'FlightPrice',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Log service pricing request to api_logs
        api_logger.log_request(
            service_name='AncillaryPricing',
            request_id=request_id,
            payload=ancillary_request,
            endpoint='/entrygate/rest/request:preFlightPrice',
            headers=headers
        )
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ancillary_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Service pricing request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                # Log service pricing response to api_logs
                api_logger.log_response(
                    service_name='AncillaryPricing',
                    request_id=request_id,
                    response=result,
                    status_code=response.status
                )
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Service pricing request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Service pricing request failed: {str(e)}", 500, request_id))

@bp.route('/pricing/price-seats-only', methods=['POST', 'OPTIONS'])
@route_cors(
    allow_origin=ALLOWED_ORIGINS,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    allow_credentials=True,
    max_age=600
)
async def price_seats_only():
    """
    Price only selected seats (no services).
    
    POST JSON Body:
    - flight_price_cache_key: Cache key for retrieving raw flight price response (PREFERRED)
    - flight_price_response: Original FlightPrice response (FALLBACK - will be deprecated)
    - seatavailability_response: SeatAvailability response data
    - selected_seats: List of selected seat ObjectKeys
    - selected_offer_index: Index of the selected offer (default: 0)
    
    Returns:
    - Priced FlightPrice response with selected seats
    """
    request_id = _get_request_id()
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        logger.info(f"Pricing seats only request received - Request ID: {request_id}")
        
        # Get request data
        data = await request.get_json()
        if not data:
            return jsonify(_create_error_response("No data provided", 400, request_id))

        flight_price_response = data.get('flight_price_response')
        flight_price_cache_key = data.get('flight_price_cache_key')
        seatavailability_response = data.get('seatavailability_response')
        seat_availability_cache_key = data.get('seat_availability_cache_key')
        selected_seats = data.get('selected_seats', [])
        selected_offer_index = data.get('selected_offer_index', 0)

        # 🚀 CRITICAL FIX: Retrieve RAW flight price response from Redis using cache key
        if flight_price_cache_key:
            try:
                logger.info(f"Attempting to retrieve RAW flight price response from cache with key: {flight_price_cache_key}")
                cached_result = simple_flight_cache.get_flight_price(flight_price_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    flight_price_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved RAW flight price response from Redis key: {flight_price_cache_key}")
                    
                    # Check if it's wrapped in FlightPriceRS structure and unwrap
                    if isinstance(flight_price_response, dict) and 'FlightPriceRS' in flight_price_response:
                        flight_price_response = flight_price_response['FlightPriceRS']
                        logger.info("Unwrapped FlightPriceRS structure for build script")
                else:
                    logger.warning(f"❌ RAW flight price response not found in Redis: {flight_price_cache_key}")
                    return jsonify(_create_error_response("Flight price data expired or not found. Please request new pricing.", 404, request_id))
            except Exception as cache_error:
                logger.error(f"Error retrieving RAW flight price response from Redis: {cache_error}")
                return jsonify(_create_error_response(f"Cache retrieval error: {cache_error}", 500, request_id))

        # 🚀 NEW: Retrieve seat availability response from Redis if cache key provided
        if seat_availability_cache_key and not seatavailability_response:
            try:
                logger.info(f"Attempting to retrieve seat availability response from cache with key: {seat_availability_cache_key}")
                cached_result = simple_flight_cache.get_seat_availability(seat_availability_cache_key)
                
                if cached_result.get('success') and cached_result.get('data'):
                    seatavailability_response = cached_result['data']
                    logger.info(f"✅ Successfully retrieved seat availability response from Redis key: {seat_availability_cache_key}")
                    
                    # Check if we need to extract raw_response for build script
                    if isinstance(seatavailability_response, dict) and 'raw_response' in seatavailability_response:
                        seatavailability_response = seatavailability_response['raw_response']
                        logger.info("Extracted raw_response from seat availability data for build script")
                else:
                    logger.warning(f"⚠️ Seat availability response not found in Redis: {seat_availability_cache_key}")
                    logger.info("Continuing without seat availability data - seats won't be priced")
            except Exception as cache_error:
                logger.warning(f"Error retrieving seat availability response from Redis: {cache_error}")
                logger.info("Continuing without seat availability data - seats won't be priced")
                logger.error(f"Error retrieving RAW flight price response from Redis: {cache_error}")
                return jsonify(_create_error_response(f"Cache retrieval error: {cache_error}", 500, request_id))

        if not flight_price_response:
            return jsonify(_create_error_response("flight_price_response or flight_price_cache_key is required", 400, request_id))

        # CRITICAL VALIDATION: Validate raw NDC response
        if isinstance(flight_price_response, dict):
            response_keys = list(flight_price_response.keys())
            required_ndc_keys = ['PricedFlightOffers', 'DataLists']
            missing_keys = [key for key in required_ndc_keys if key not in response_keys]
            if missing_keys:
                logger.error(f"❌ Missing required NDC keys in flight price response: {missing_keys}")
                return jsonify(_create_error_response(
                    f"Invalid flight price response: Missing required NDC keys: {missing_keys}.", 
                    400, 
                    request_id
                ))
            logger.info(f"✅ Validated raw NDC flight price response with keys: {response_keys}")

        # Check if pricing is required for seats
        pricing_info = detect_pricing_required(
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        if not pricing_info['requires_pricing']:
            logger.info(f"No seat pricing required - Request ID: {request_id}")
            return jsonify({
                'status': 'success',
                'data': flight_price_response,
                'pricing_info': pricing_info,
                'request_id': request_id,
                'message': 'No additional pricing required for seats'
            })

        # Get TokenManager token
        token_manager = TokenManager.get_instance()
        bearer_token = token_manager.get_token()
        
        # Extract airline code from flight_price_response for ThirdPartyId header
        airline_code = None
        try:
            # Try to get airline from PricedFlightOffers > OfferID > Owner
            priced_offers = flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
            if isinstance(priced_offers, list) and len(priced_offers) > 0:
                airline_code = priced_offers[0].get('OfferID', {}).get('Owner')
            elif isinstance(priced_offers, dict):
                airline_code = priced_offers.get('OfferID', {}).get('Owner')
            
            # Fallback: Try ShoppingResponseID Owner
            if not airline_code:
                airline_code = flight_price_response.get('ShoppingResponseID', {}).get('Owner')
            
            logger.info(f"Extracted airline code for ThirdPartyId: {airline_code}")
        except Exception as e:
            logger.warning(f"Could not extract airline code: {e}")
        
        # Build the seat pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats,
            selected_offer_index=selected_offer_index
        )
        
        # Create headers
        config = current_app.config
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': bearer_token,
            'OfficeId': config.get('VERTEIL_OFFICE_ID'),
            'ThirdpartyId': airline_code if airline_code else config.get('VERTEIL_THIRD_PARTY_ID', ''),
            'service': 'FlightPrice',
            'User-Agent': 'PostmanRuntime/7.41',
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        # Log seat pricing request to api_logs
        api_logger.log_request(
            service_name='AncillaryPricing',
            request_id=request_id,
            payload=ancillary_request,
            endpoint='/entrygate/rest/request:preFlightPrice',
            headers=headers
        )
        
        # Make API call
        api_url = f"{config.get('VERTEIL_API_BASE_URL')}/entrygate/rest/request:preFlightPrice"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=ancillary_request, timeout=30) as response:
                result = await response.json()
                
                logger.info(f"Seat pricing request completed successfully - Status: {response.status} - Request ID: {request_id}")
                
                # Log seat pricing response to api_logs
                api_logger.log_response(
                    service_name='AncillaryPricing',
                    request_id=request_id,
                    response=result,
                    status_code=response.status
                )
                
                return jsonify({
                    'status': 'success',
                    'data': result,
                    'pricing_info': pricing_info,
                    'request_id': request_id
                })
                
    except Exception as e:
        logger.error(f"Seat pricing request failed: {str(e)} - Request ID: {request_id}", exc_info=True)
        return jsonify(_create_error_response(f"Seat pricing request failed: {str(e)}", 500, request_id))
