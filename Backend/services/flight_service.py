"""
Flight Service Module

This module contains the core businessLogic for interacting with the Verteil NDC API.
It handles the NDC workflow: AirShopping -> FlightPrice -> OrderCreate.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from json import JSONDecodeError
from typing import Dict, List, Any, Optional, Union
import asyncio
import aiohttp
import json
import time
import os
import sys
import uuid # Added for request_id generation if not provided
from functools import wraps
from requests.exceptions import RequestException, HTTPError # requests is not used for async, consider removing if not used elsewhere
from flask import current_app # Assuming Quart's current_app behaves similarly or this is for a Flask context
from typing import Awaitable, Callable, TypeVar, cast

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache_manager import cache_manager

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


# Type variable for async functions
T = TypeVar('T')

def async_cache(timeout: int = 300, key_prefix: str = 'acache_'):
    """
    Decorator to cache async function results.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
    """
    def decorator(f: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get cached result
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call the async function if not in cache
            result = await f(*args, **kwargs)
            
            # Cache the result
            if result is not None:
                cache_manager.set(cache_key, result, timeout)
                
            return result
        return decorated_function
    return decorator

# Rate limit decorator for async functions
def async_rate_limited(limit: int = 100, window: int = 60, key_prefix: str = 'arl_'):
    """
    Decorator to rate limit async function calls.
    
    Args:
        limit: Maximum number of requests allowed in the time window
        window: Time window in seconds (default: 60)
        key_prefix: Prefix for rate limit keys
    """
    def decorator(f: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Generate rate limit key
            rate_key = f"{key_prefix}{f.__name__}:{str(args)[:50]}"
            
            if cache_manager.rate_limit(rate_key, limit, window):
                raise RateLimitExceeded("Rate limit exceeded. Please try again later.")
                
            return await f(*args, **kwargs)
        return decorated_function
    return decorator

# Import request builders and auth
from utils.auth import TokenManager, AuthError
from utils.request_builders import (
    build_airshopping_rq,
    build_flightprice_rq,
    build_ordercreate_rq
)
# from utils.auth import TokenManager, AuthError # Duplicate import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CURRENCY = "USD" # Set a default currency
DEFAULT_LANGUAGE = "en"
DEFAULT_FARE_TYPE = "PUBL"

class FlightServiceError(Exception):
    """Custom exception for flight service errors"""
    pass

def get_verteil_headers(service_name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Get the headers for Verteil API requests using the static token
    
    Args:
        service_name: The name of the service (AirShopping, FlightPrice, OrderCreate)
        config: Configuration dictionary containing API settings
        
    Returns:
        Dict containing the necessary headers
        
    Raises:
        FlightServiceError: If required configuration is missing
    """
    # logger = logging.getLogger(__name__) # Logger already defined at module level
    
    # Get required configuration values from environment variables
    third_party_id = os.getenv('VERTEIL_THIRD_PARTY_ID')
    office_id = os.getenv('VERTEIL_OFFICE_ID')
    static_token = os.getenv('VERTEIL_STATIC_TOKEN')
    
    # Validate required configuration
    missing_configs = []
    if not third_party_id:
        missing_configs.append('VERTEIL_THIRD_PARTY_ID')
    if not office_id:
        missing_configs.append('VERTEIL_OFFICE_ID')
    if not static_token:
        missing_configs.append('VERTEIL_STATIC_TOKEN')
    
    if missing_configs:
        error_msg = f"Missing required configuration: {', '.join(missing_configs)}"
        logger.error(error_msg)
        raise FlightServiceError(error_msg)
    
    # Construct headers according to the required format
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'FLIGHT-Booking-Portal/1.0',
        'Accept-Encoding': 'gzip',
        'ThirdpartyId': third_party_id,
        'officeId': office_id,
        'Service': service_name,
        'Authorization': f'Bearer {static_token}'
    }
    
    # Log the headers (without sensitive data)
    safe_headers = headers.copy()
    if 'Authorization' in safe_headers:
        safe_headers['Authorization'] = 'Bearer [REDACTED]'
    logger.debug(f"Generated headers: {json.dumps(safe_headers, indent=2)}")
    
    return headers

async def make_async_verteil_request(
    endpoint: str, 
    payload: Dict[str, Any], 
    service_name: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make an asynchronous request to the Verteil NDC API.
    
    Args:
        endpoint: API endpoint (e.g., 'airshopping', 'flightprice')
        payload: Request payload
        service_name: Name of the service for logging
        config: Optional configuration dictionary. If not provided, will try to use current_app.config
        
    Returns:
        API response as a dictionary
        
    Raises:
        FlightServiceError: If the request fails after retries
    """
    
    # Get the base URL from config or use default
    default_base_url = 'https://api.stage.verteil.com'
    
    # If config is provided, use it. Otherwise, try to get from current_app if available
    if config is None:
        try:
            # Ensure current_app is available and has a config attribute
            if 'current_app' in globals() and hasattr(current_app, 'config'):
                config = current_app.config
            else:
                logger.warning("current_app or current_app.config not available, using environment variables.")
                config = {} # Initialize config to empty dict if current_app is not available
        except RuntimeError: # Handles cases where current_app is not available (e.g. running script directly)
            logger.warning("Running outside of application context, using environment variables")
            config = {}
    
    # Get base URL from config or environment
    base_url = config.get('VERTEIL_API_BASE_URL') or os.getenv('VERTEIL_API_BASE_URL') or default_base_url
    
    # Construct the full URL
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    # Log the request details
    logger.info(f"=== REQUEST TO VERTEIL API ===")
    logger.info(f"URL: {url}")
    logger.info(f"Method: {'POST'}")
    
    # Get headers for the request
    try:
        headers = get_verteil_headers(service_name, config) # Pass config here
        logger.info(f"Headers: {json.dumps({k: v if k != 'Authorization' else '[REDACTED]' for k, v in headers.items()}, indent=2)}")
    except Exception as e:
        error_msg = f"Failed to generate request headers: {str(e)}"
        logger.error(error_msg)
        raise FlightServiceError(error_msg) from e
    
    # Log the full request details (headers already logged above)
    logger.info(f"Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
    logger.info("==============================")
    
    # Make the request with retries
    max_retries = 3
    retry_delay = 1  # seconds
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"Attempt {attempt}/{max_retries} - Making {service_name} request to {url}")
                
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)  # 30 second timeout
                ) as response:
                    response_text = await response.text()
                    
                    # Log response details
                    logger.info(f"=== RESPONSE FROM VERTEIL API ===")
                    logger.info(f"Status: {response.status}")
                    logger.info(f"Headers: {dict(response.headers)}")
                    
                    # Parse the response
                    try:
                        response_json = json.loads(response_text) if response_text else {}
                        logger.info(f"Response body (JSON): {json.dumps(response_json, indent=2) if response_json else 'Empty response'}")
                    except json.JSONDecodeError:
                        logger.warning(f"Response is not valid JSON. Raw response: {response_text}")
                        response_json = {} # Or handle as an error
                    
                    # Handle non-200 responses
                    if response.status >= 400:
                        error_details = {
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body": response_text, # Log the raw text for errors
                            "request_headers": {k: v if k != 'Authorization' else '[REDACTED]' for k, v in headers.items()}
                        }
                        
                        logger.error(f"API request failed. Details: {json.dumps(error_details, indent=2)}")
                        
                        if response.status == 401:
                            # Clear the token cache on 401 to force a new token on next request
                            try:
                                # Get TokenManager instance and clear the token
                                token_manager = TokenManager() # Assuming TokenManager is accessible
                                token_manager.clear_token()
                                logger.info("Cleared token cache due to 401 response")
                                
                                # If we have a config, update the token manager with it
                                if config:
                                    token_manager.set_config(config)
                                    logger.debug("Updated TokenManager config after clearing token")
                                    
                            except Exception as e:
                                logger.error(f"Failed to clear token cache: {str(e)}", exc_info=True)
                            
                            error_msg = "Authentication failed. The token has been cleared and will be refreshed on the next request."
                        else:
                            error_msg = f"API request failed with status {response.status}: {response_text[:500]}" # Include part of response
                        
                        raise FlightServiceError(error_msg)
                    
                    logger.info("=== END RESPONSE ===")
                    return response_json
                    
        except aiohttp.ClientError as e:
            last_exception = e
            error_msg = f"Network error during {service_name} request: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Max retries ({max_retries}) exceeded for {service_name} request")
                raise FlightServiceError(
                    f"Failed to complete {service_name} request after {max_retries} attempts: {str(e)}"
                ) from e
        except asyncio.TimeoutError as e:
            last_exception = e
            error_msg = f"Request to {service_name} timed out after 30 seconds"
            logger.error(error_msg)
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                continue # Important: continue to the next attempt
            else:
                raise FlightServiceError(f"Request to {service_name} timed out after {max_retries} attempts") from e
        
    # This should ideally not be reached if retries are handled correctly
    if last_exception: # Check if last_exception was set
        raise FlightServiceError(
            f"Failed to complete {service_name} request: {str(last_exception)}"
        )
    else: # Fallback if loop finishes without setting last_exception (should not happen)
        raise FlightServiceError(f"Unknown error in {service_name} request after all retries.")


# Keep the synchronous version for backward compatibility
# This synchronous version needs to be updated to use the async one or removed if not needed.
# For now, I'll comment it out as it's not directly part of the async flow and might cause issues
# if not properly managed with event loops in a Quart/Flask async context.
"""
def make_verteil_request(endpoint: str, payload: Dict[str, Any], service_name: str) -> Dict[str, Any]:
    # Synchronous wrapper around the async request function.
    # This is kept for backward compatibility.
    # loop = asyncio.new_event_loop() # Be careful with new_event_loop in async frameworks
    # asyncio.set_event_loop(loop)
    try:
        # This might not work correctly in an async app without proper loop management
        return asyncio.run( 
            make_async_verteil_request(endpoint, payload, service_name)
        )
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            # If already in an event loop, try to schedule it differently or use nest_asyncio if appropriate
            # For simplicity, let's re-raise for now or log a more specific error
            logger.error("make_verteil_request (sync) called from within an async event loop. This is problematic.")
            raise FlightServiceError("Synchronous request called from async context.") from e
        raise
    # finally:
        # loop.close() # Closing loop might also be problematic depending on context
"""

@async_rate_limited(limit=30, window=60)  # 30 requests per minute
@async_cache(timeout=1800, key_prefix='flight_search_')  # Cache for 30 minutes
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    cabin_class: str = "ECONOMY",
    fare_type: str = DEFAULT_FARE_TYPE,
    request_id: Optional[str] = None,
    trip_type: str = "ONE_WAY" # Added trip_type
) -> Dict[str, Any]:
    """
    Search for flights using AirShopping request with caching and rate limiting.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (for round trips)
        adults: Number of adult passengers
        children: Number of child passengers
        infants: Number of infant passengers
        cabin_class: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        fare_type: Fare type code (default: PUBL for published fares)
        request_id: Optional request ID for tracking
        trip_type: Type of trip (ONE_WAY, ROUND_TRIP, MULTI_CITY)
        
    Returns:
        Dictionary containing flight search results
    """
    try:
        if not request_id:
            request_id = str(uuid.uuid4()) # Use uuid for request_id
            
        logger.info(f"Processing flight search request {request_id}: {origin}-{destination} on {departure_date}, Type: {trip_type}")
        
        # Build the AirShopping request
        airshopping_rq = build_airshopping_rq(
            trip_type=trip_type.upper(),
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            cabin_class=cabin_class,
            fare_type=fare_type
        )
        
        # Get the configuration (simplified for clarity, assuming config is passed or globally available)
        config = {} # Placeholder, ideally get from current_app.config or os.environ
        try:
            if 'current_app' in globals() and hasattr(current_app, 'config'):
                config = current_app.config
        except RuntimeError:
            logger.warning("Running outside of app context for search_flights config.")


        logger.info("Sending request to Verteil API...")
        response = await make_async_verteil_request(
            endpoint="/entrygate/rest/request:airShopping", # Ensure endpoint is correct
            payload=airshopping_rq,
            service_name="AirShopping",
            config=config # Pass config
        )
        
        logger.info("Received response from Verteil API")
        
        # Save full response to a file for debugging (optional)
        # ... (code for saving response, can be kept or removed)
        
        return response # Return the raw response, transformation will happen in process_air_shopping

    except Exception as e:
        logger.error(f"Error in search_flights: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to search flights: {str(e)}") from e

get_flight_offers = search_flights  # Alias for backward compatibility

async def get_flight_price( # Made async
    airshopping_response: Dict[str, Any],
    offer_id: str, # Changed from offer_index to offer_id for clarity
    shopping_response_id: str, # Added for FlightPriceRQ
    currency: str = DEFAULT_CURRENCY,
    request_id: Optional[str] = None, # Added request_id
    config: Optional[Dict[str, Any]] = None # Added config
) -> Dict[str, Any]:
    """
    Get price for a specific flight offer using FlightPrice request (async)
    
    Args:
        airshopping_response: The AirShopping response (full or relevant parts for FlightPriceRQ)
        offer_id: The ID of the offer to price
        shopping_response_id: The ShoppingResponseID from AirShoppingRS
        currency: Currency code (default: USD)
        request_id: Optional request ID
        config: Optional application config
        
    Returns:
        Dictionary containing pricing information
    """
    try:
        if not request_id:
            request_id = str(uuid.uuid4())

        # Build FlightPrice request
        flightprice_rq = build_flightprice_rq(
            airshopping_response=airshopping_response, 
            offer_id=offer_id, 
            shopping_response_id=shopping_response_id, # Pass this
            currency=currency
        )
        
        # Make request to Verteil API
        logger.info(f"Sending FlightPrice request ({request_id}) to Verteil API for offer {offer_id}...")
        response = await make_async_verteil_request(
            endpoint="/entrygate/rest/request:flightPrice", 
            payload=flightprice_rq, 
            service_name="FlightPrice",
            config=config
        )
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {
                "offer_id": offer_id,
                "request_id": request_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_flight_price ({request_id}): {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to get flight price for offer {offer_id}: {str(e)}") from e


async def create_booking( # Made async
    flight_price_response: Dict[str, Any],
    passengers: List[Dict[str, Any]], # Renamed from passenger_details
    payment_info: Dict[str, Any], # Renamed from payment_details
    contact_info: Dict[str, str],
    request_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a flight booking using OrderCreate request (async)
    
    Args:
        flight_price_response: The FlightPrice response
        passengers: List of passenger details
        payment_info: Payment information
        contact_info: Contact information
        request_id: Optional request ID
        config: Optional application config
        
    Returns:
        Dictionary containing booking confirmation
    """
    try:
        if not request_id:
            request_id = str(uuid.uuid4())
        # Build OrderCreate request
        ordercreate_rq = build_ordercreate_rq(
            flight_price_response=flight_price_response,
            passengers=passengers, # Use renamed arg
            payment_info=payment_info, # Use renamed arg
            contact_info=contact_info
        )
        
        # Make request to Verteil API
        logger.info(f"Sending OrderCreate request ({request_id}) to Verteil API...")
        response = await make_async_verteil_request(
            endpoint="/entrygate/rest/request:orderCreate", 
            payload=ordercreate_rq, 
            service_name="OrderCreate",
            config=config
        )
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_booking ({request_id}): {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to create booking: {str(e)}") from e

async def get_booking_details(booking_reference: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: # Made async
    """
    Get details for a specific booking (async)
    
    Args:
        booking_reference: The booking reference number (OrderID)
        config: Optional application config
        
    Returns:
        Dictionary containing booking details
    """
    try:
        # Build the request to retrieve booking details (example structure)
        request_payload = {
            "Query": {
                "Filters": {
                    "OrderID": {
                        # "Owner": "WY", # Owner might be needed depending on API
                        # "Channel": "NDC",
                        "value": booking_reference
                    }
                }
            }
        }
        
        # Make request to Verteil API
        logger.info(f"Sending OrderRetrieve request for booking {booking_reference}...")
        response = await make_async_verteil_request(
            endpoint="/entrygate/rest/request:orderRetrieve", # Verify this endpoint
            payload=request_payload,
            service_name="OrderRetrieve",
            config=config
        )
        
        # Transform and return the response (simplified, needs actual transformation based on OrderRetrieveRS)
        # This is a placeholder transformation, actual structure of OrderRetrieveRS needs to be handled
        transformed_data = {
            "booking_reference": booking_reference,
            "status": response.get("Response", {}).get("Order", {}).get("OrderStatus", "UNKNOWN"),
            "raw_response": response # Include raw response for now
        }

        return {
            "status": "success",
            "data": transformed_data,
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "reference": booking_reference
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_booking_details for {booking_reference}: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to retrieve booking details for {booking_reference}: {str(e)}") from e


async def process_air_shopping(search_criteria: Dict[str, Any]) -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Process flight search request, call search_flights, and transform the response.
    
    Args:
        search_criteria: Dictionary containing search parameters.
        
    Returns:
        A list of transformed flight offers or an error dictionary.
    """
    try:
        trip_type = search_criteria.get('trip_type', 'ONE_WAY')
        od_segments_criteria = search_criteria.get('od_segments', [])
        request_id = search_criteria.get('request_id', str(uuid.uuid4()))

        if not od_segments_criteria:
            logger.error("No origin-destination segments provided in search_criteria.")
            return {"error": "Origin-destination segments are required.", "status": "error"}
            
        first_segment = od_segments_criteria[0]
        return_date_criteria = None
        if trip_type == "ROUND_TRIP" and len(od_segments_criteria) > 1:
            # For round trip, Verteil's AirShoppingRQ builder might infer the return from the second segment
            # or expect a specific returnDate parameter. Assuming build_airshopping_rq handles this.
             pass # build_airshopping_rq should handle this based on trip_type and segments

        logger.info(f"process_air_shopping: Calling search_flights for request_id {request_id}")
        flight_results_raw = await search_flights(
            origin=first_segment.get('Origin', ''),
            destination=first_segment.get('Destination', ''),
            departure_date=first_segment.get('DepartureDate', ''),
            return_date=od_segments_criteria[1].get('DepartureDate') if trip_type == "ROUND_TRIP" and len(od_segments_criteria) > 1 else None,
            adults=search_criteria.get('num_adults', 1),
            children=search_criteria.get('num_children', 0),
            infants=search_criteria.get('num_infants', 0),
            cabin_class=search_criteria.get('cabin_preference', 'ECONOMY'),
            request_id=request_id,
            trip_type=trip_type
        )

        if not flight_results_raw or flight_results_raw.get("status") == "error":
            logger.error(f"search_flights returned an error or no results: {flight_results_raw}")
            return flight_results_raw if isinstance(flight_results_raw, dict) else {"error": "Failed to fetch flight results", "status": "error"}

        # The actual API response is expected to be in flight_results_raw directly if search_flights returns it
        # If search_flights wraps it, adjust here. Assuming flight_results_raw IS the API JSON.
        
        transformed_offers = []
        data_lists = flight_results_raw.get('DataLists', {})
        flight_segment_map = {
            segment.get('SegmentKey'): segment
            for segment in data_lists.get('FlightSegmentList', {}).get('FlightSegment', [])
            if segment.get('SegmentKey') # Ensure SegmentKey exists
        }

        offers_group = flight_results_raw.get('OffersGroup', {})
        airline_offers_list = offers_group.get('AirlineOffers', [])

        for airline_offer_group in airline_offers_list:
            for offer_detail in airline_offer_group.get('AirlineOffer', []):
                offer_id = offer_detail.get('OfferID', {}).get('value')
                total_price_info = offer_detail.get('TotalPrice', {}).get('SimpleCurrencyPrice', {})
                
                if not offer_id or not total_price_info:
                    logger.warning(f"Skipping offer due to missing OfferID or TotalPrice: {offer_detail.get('OfferID')}")
                    continue

                offer_price_amount = float(total_price_info.get('value', 0))
                offer_price_currency = total_price_info.get('Code', DEFAULT_CURRENCY)
                
                current_offer_segments = []
                # Use a set to track segment keys for the current offer to avoid duplicates
                processed_segment_keys_for_current_offer = set()

                priced_offer_details = offer_detail.get('PricedOffer', {})
                for offer_price_item in priced_offer_details.get('OfferPrice', []):
                    requested_date_info = offer_price_item.get('RequestedDate', {})
                    for association in requested_date_info.get('Associations', []):
                        applicable_flight = association.get('ApplicableFlight', {})
                        for segment_ref in applicable_flight.get('FlightSegmentReference', []):
                            segment_key = segment_ref.get('ref')
                            if segment_key and segment_key not in processed_segment_keys_for_current_offer:
                                matching_segment = flight_segment_map.get(segment_key)
                                if matching_segment:
                                    departure_info = matching_segment.get('Departure', {})
                                    arrival_info = matching_segment.get('Arrival', {})
                                    marketing_carrier = matching_segment.get('MarketingCarrier', {})
                                    
                                    dep_airport_code = departure_info.get('AirportCode', {}).get('value')
                                    arr_airport_code = arrival_info.get('AirportCode', {}).get('value')
                                    dep_date = departure_info.get('Date')
                                    dep_time = departure_info.get('Time')
                                    arr_date = arrival_info.get('Date')
                                    arr_time = arrival_info.get('Time')
                                    flight_num = marketing_carrier.get('FlightNumber', {}).get('value')
                                    airline_code = marketing_carrier.get('AirlineID', {}).get('value')

                                    if not all([dep_airport_code, arr_airport_code, dep_date, dep_time, arr_date, arr_time, flight_num, airline_code]):
                                        logger.warning(f"Skipping segment {segment_key} due to missing critical data.")
                                        continue
                                        
                                    transformed_segment = {
                                        "origin": dep_airport_code,
                                        "destination": arr_airport_code,
                                        "departure_time": f"{dep_date}T{dep_time}",
                                        "arrival_time": f"{arr_date}T{arr_time}",
                                        "flight_number": flight_num,
                                        "airline": airline_code
                                    }
                                    current_offer_segments.append(transformed_segment)
                                    processed_segment_keys_for_current_offer.add(segment_key)
                                else:
                                    logger.warning(f"SegmentKey {segment_key} not found in DataLists.FlightSegmentList.")
                
                if current_offer_segments:
                    # Determine overall airline and flight number from the first segment for simplicity
                    # Frontend might need a more sophisticated way to display multi-leg/airline trips
                    overall_airline = current_offer_segments[0]['airline']
                    overall_flight_number = current_offer_segments[0]['flight_number'] # This might not be representative for multi-segment

                    transformed_offers.append({
                        "id": offer_id,
                        "price": {
                            "amount": offer_price_amount,
                            "currency": offer_price_currency
                        },
                        "segments": current_offer_segments,
                        "airline": overall_airline, 
                        "flight_number": overall_flight_number 
                    })
                else:
                    logger.warning(f"Offer {offer_id} had no processable segments.")
        
        logger.info(f"Successfully transformed {len(transformed_offers)} offers for request_id {request_id}.")
        return transformed_offers

    except FlightServiceError as e:
        logger.error(f"FlightServiceError in process_air_shopping (request_id {search_criteria.get('request_id', 'N/A')}): {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error"}
    except Exception as e:
        logger.error(f"Unexpected error in process_air_shopping (request_id {search_criteria.get('request_id', 'N/A')}): {str(e)}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}", "status": "error"}


async def process_flight_price(price_request: Dict[str, Any]) -> Dict[str, Any]: # Made async
    """
    Process flight pricing request and return detailed pricing information. (async)
    
    Args:
        price_request: Dictionary containing pricing request data
        
    Returns:
        Dictionary containing detailed pricing information
    """
    try:
        # Assuming get_flight_price is now async
        return await get_flight_price(
            airshopping_response=price_request['airshopping_response'], # This needs to be the full AirShoppingRS or relevant parts
            offer_id=price_request['offer_id'],
            shopping_response_id=price_request['shopping_response_id'], # Ensure this is passed
            currency=price_request.get('currency', DEFAULT_CURRENCY),
            request_id=price_request.get('request_id')
            # config=price_request.get('config') # Pass config if needed by get_flight_price
        )
        
    except FlightServiceError as e:
        logger.error(f"Error in process_flight_price: {str(e)}")
        return {"error": str(e), "status": "error"} # Ensure status is included
    except Exception as e:
        logger.error(f"Unexpected error in process_flight_price: {str(e)}", exc_info=True)
        return {"error": "An unexpected error occurred while pricing the flight", "status": "error"}


async def process_order_create(order_data: Dict[str, Any]) -> Dict[str, Any]: # Made async
    """
    Process order creation request and return booking confirmation. (async)
    
    Args:
        order_data: Dictionary containing order data
        
    Returns:
        Dictionary containing booking confirmation
    """
    try:
        # Extract data from order_data
        flight_offer_priced = order_data.get("flight_offer", {}) # This should be FlightPriceRS
        passengers_list = order_data.get("passengers", [])
        payment_info_data = order_data.get("payment", {}) # Renamed for clarity
        contact_info_data = order_data.get("contact_info", {}) # Renamed for clarity
        request_id = order_data.get("request_id", str(uuid.uuid4()))
        
        # Validate required fields
        if not flight_offer_priced:
            raise FlightServiceError("Missing required field: flight_offer (FlightPriceRS)")
        if not passengers_list:
            raise FlightServiceError("Missing required field: passengers")
        if not payment_info_data:
            raise FlightServiceError("Missing required field: payment")
        if not contact_info_data:
            raise FlightServiceError("Missing required field: contact_info")
        
        # Create the booking using the async version
        booking_response = await create_booking(
            flight_price_response=flight_offer_priced,
            passengers=passengers_list,
            payment_info=payment_info_data,
            contact_info=contact_info_data,
            request_id=request_id
            # config=order_data.get('config') # Pass config if needed
        )
        
        # Extract relevant data from the response (assuming OrderCreateRS structure)
        # This part needs to be adapted based on the actual structure of OrderCreateRS
        order_create_rs = booking_response.get("data", {}).get("OrderCreateRS", {}) # Example path
        order_info = order_create_rs.get("Response", {}).get("Order", {})
        order_id = order_info.get("OrderID")
        
        if not order_id: # Check if order_id is a dict with 'value' or direct string
            if isinstance(order_info.get("OrderID"), dict):
                 order_id = order_info.get("OrderID", {}).get("value")

        if not order_id:
            logger.error(f"Failed to retrieve OrderID. Full booking response: {json.dumps(booking_response, indent=2)}")
            raise FlightServiceError("Failed to retrieve OrderID from the booking response.")
        
        # Placeholder for e-ticket and payment details extraction
        # This needs to be based on the actual OrderCreateRS structure
        etickets_data = [] 
        payment_data_list = order_create_rs.get("Response", {}).get("DataLists", {}).get("PaymentFunctionsList", {}).get("PaymentProcessingDetails", [])
        amount_paid_val = 0
        currency_val = DEFAULT_CURRENCY

        if payment_data_list: # Check if list is not empty
            # Assuming first payment detail is relevant, adjust if multiple payments are possible
            # and need specific handling.
            payment_detail = payment_data_list[0] if isinstance(payment_data_list, list) else payment_data_list
            amount_info = payment_detail.get("Amount", {})
            amount_paid_val = float(amount_info.get("value", 0))
            currency_val = amount_info.get("Code", DEFAULT_CURRENCY)


        # Transform the response
        return {
            "status": "success",
            "data": {
                "booking_reference": order_id,
                "status": order_info.get("OrderStatus", "CONFIRMED"),
                "etickets": etickets_data, # Populate this based on OrderCreateRS
                "amount_paid": amount_paid_val,
                "currency": currency_val
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "reference": order_id, # Using order_id as reference
                "request_id": request_id
            }
        }
        
    except FlightServiceError as e:
        logger.error(f"Error in process_order_create: {str(e)}", exc_info=True)
        raise # Re-raise FlightServiceError to be caught by route handler
    except Exception as e:
        error_msg = f"Unexpected error in process_order_create: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise FlightServiceError(error_msg) from e

# Transformation functions for backward compatibility (placeholders)
def _transform_airshopping_rs(airshopping_rs: Dict[str, Any]) -> Dict[str, Any]:
    logger.warning("_transform_airshopping_rs is a placeholder and should be implemented if used.")
    return airshopping_rs

def _transform_flightprice_rs(flightprice_rs: Dict[str, Any]) -> Dict[str, Any]:
    logger.warning("_transform_flightprice_rs is a placeholder and should be implemented if used.")
    return flightprice_rs

def _transform_ordercreate_rs(ordercreate_rs: Dict[str, Any]) -> Dict[str, Any]:
    logger.warning("_transform_ordercreate_rs is a placeholder and should be implemented if used.")
    return ordercreate_rs
