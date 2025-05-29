"""
Flight Service Module

This module contains the core business logic for interacting with the Verteil NDC API.
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
from functools import wraps
from requests.exceptions import RequestException, HTTPError
from flask import current_app
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
from utils.auth import TokenManager, AuthError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CURRENCY = ""
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
    logger = logging.getLogger(__name__)
    
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
    base_url = 'https://api.stage.verteil.com'
    
    # If config is provided, use it. Otherwise, try to get from current_app if available
    if config is None:
        try:
            config = current_app.config
        except RuntimeError:
            logger.warning("Running outside of application context, using environment variables")
            config = {}
    
    # Get base URL from config or environment
    base_url = config.get('VERTEIL_API_BASE_URL') or os.getenv('VERTEIL_API_BASE_URL') or base_url
    
    # Construct the full URL
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    # Log the request details
    logger.info(f"=== REQUEST TO VERTEIL API ===")
    logger.info(f"URL: {url}")
    logger.info(f"Method: {'POST'}")
    
    # Get headers for the request
    try:
        headers = get_verteil_headers(service_name, config)
        logger.info(f"Headers: {json.dumps({k: v if k != 'Authorization' else '[REDACTED]' for k, v in headers.items()}, indent=2)}")
    except Exception as e:
        error_msg = f"Failed to generate request headers: {str(e)}"
        logger.error(error_msg)
        raise FlightServiceError(error_msg) from e
    
    # Log the full request details
    safe_headers = headers.copy()
    if 'Authorization' in safe_headers:
        safe_headers['Authorization'] = 'Bearer [REDACTED]'
    
    logger.info(f"=== REQUEST TO VERTEIL API ===")
    logger.info(f"URL: {url}")
    logger.info(f"Method: POST")
    logger.info(f"Headers: {json.dumps(safe_headers, indent=2)}")
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
                
                # Log the exact request being sent
                logger.debug(f"Sending request to {url}")
                logger.debug(f"Request headers: {headers}")
                logger.debug(f"Request payload: {json.dumps(payload)}")
                
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
                        response_json = {}
                    
                    # Handle non-200 responses
                    if response.status >= 400:
                        error_details = {
                            "status": response.status,
                            "headers": dict(response.headers),
                            "body": response_text,
                            "request_headers": {k: v if k != 'Authorization' else '[REDACTED]' for k, v in headers.items()}
                        }
                        
                        logger.error(f"API request failed. Details: {json.dumps(error_details, indent=2)}")
                        
                        if response.status == 401:
                            # Clear the token cache on 401 to force a new token on next request
                            try:
                                # Get TokenManager instance and clear the token
                                token_manager = TokenManager()
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
                            error_msg = f"API request failed with status {response.status}"
                        
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
                continue
            else:
                raise FlightServiceError(f"Request to {service_name} timed out after {max_retries} attempts") from e
        
    # This should never be reached due to the raise in the loop, but just in case
    raise FlightServiceError(
        f"Failed to complete {service_name} request: {str(last_exception)}"
    )

# Keep the synchronous version for backward compatibility
def make_verteil_request(endpoint: str, payload: Dict[str, Any], service_name: str) -> Dict[str, Any]:
    """
    Synchronous wrapper around the async request function.
    This is kept for backward compatibility.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            make_async_verteil_request(endpoint, payload, service_name)
        )
    finally:
        loop.close()
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            # Get authentication headers with service-specific headers
            headers = get_verteil_headers(service_name)
            
            # Build the full URL
            base_url = current_app.config.get('VERTEIL_API_BASE_URL', 'https://api.stage.verteil.com')
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            # Log the request details
            logger.info(f"\n=== Making {service_name} Request ===")
            logger.info(f"URL: {url}")
            logger.info(f"Attempt: {attempt}/{max_retries}")
            logger.info("Headers:")
            for k, v in headers.items():
                if k.lower() == 'authorization':
                    logger.info(f"  {k}: [REDACTED]")
                else:
                    logger.info(f"  {k}: {v}")
            
            logger.info("Payload:")
            logger.info(json.dumps(payload, indent=2))
            
            # Make the request
            start_time = time.time()
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=current_app.config.get('REQUEST_TIMEOUT', 30)
                )
                duration = time.time() - start_time
                
                # Log the response details
                logger.info(f"\n=== {service_name} Response ===")
                logger.info(f"Status: {response.status_code}")
                logger.info(f"Time: {duration:.2f}s")
                
                # Log response headers
                logger.info("Response Headers:")
                for k, v in response.headers.items():
                    logger.info(f"  {k}: {v}")
                
                # Log raw response content for debugging
                content_type = response.headers.get('Content-Type', '').lower()
                logger.info("Response content type: %s", content_type)
                
                # Try to parse JSON response
                try:
                    if response.content:  # Only try to parse if there's content
                        response_data = response.json()
                        logger.debug("Response JSON structure: %s", list(response_data.keys()) if isinstance(response_data, dict) else f"List with {len(response_data)} items")
                        logger.debug("Response JSON (first 2000 chars):\n%s", json.dumps(response_data, indent=2, default=str)[:2000])
                        return response_data
                    else:
                        logger.warning("Empty response content")
                        return {}
                except JSONDecodeError as e:
                    logger.error("Failed to parse JSON response: %s", str(e))
                    logger.info("Raw response (first 2000 chars):\n%s", response.text[:2000])
                    
                    # Try to extract error message from non-JSON response
                    error_msg = "Invalid JSON response from server"
                    if response.text.strip():
                        error_msg = f"{error_msg}. Response: {response.text[:500]}"
                        
                        # Log the full error response for debugging
                        logger.error("Full error response:")
                        logger.error(json.dumps(response_data, indent=2))
                        
                        raise FlightServiceError(error_msg)
                        
                    # Check for empty or unexpected response
                    if not response_data:
                        error_msg = "Empty response received from API"
                        logger.error(error_msg)
                        raise FlightServiceError(error_msg)
                        
                    logger.info("Successfully parsed JSON response")
                    return response_data
                    
                except JSONDecodeError as je:
                    # If not JSON, log the raw response
                    logger.error(f"Failed to parse JSON response: {str(je)}")
                    logger.info("Raw response content type: %s", response.headers.get('Content-Type', 'unknown'))
                    logger.info("Raw response (first 2000 chars): %s", response.text[:2000])
                    
                    if not response.ok:
                        error_msg = f"HTTP {response.status_code} - {response.reason}"
                        logger.error(f"Request failed: {error_msg}")
                        
                        # Try to extract more error details from non-JSON response
                        error_detail = response.text.strip()
                        if error_detail:
                            logger.error(f"Error details: {error_detail}")
                            error_msg = f"{error_msg}: {error_detail}"
                            
                        response.raise_for_status()
                        
                    return {'status': 'success', 'data': response.text}
                    
            except requests.exceptions.SSLError as e:
                logger.error(f"SSL Error: {str(e)}")
                raise FlightServiceError(f"SSL Error: {str(e)}") from e
                
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timed out: {str(e)}")
                raise FlightServiceError("Request timed out") from e
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                raise FlightServiceError("Connection error") from e
                
        except HTTPError as e:
            last_error = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    last_error = json.dumps(error_data, indent=2)
                    logger.error(f"HTTP error {e.response.status_code}:")
                    logger.error(last_error)
                except JSONDecodeError:
                    last_error = e.response.text
                    logger.error(f"HTTP error {e.response.status_code}: {last_error}")
            
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning(f"Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            raise FlightServiceError(f"API request failed after {max_retries} attempts: {last_error}") from e
            
        except RequestException as e:
            last_error = str(e)
            logger.error(f"Request failed: {last_error}", exc_info=True)
            
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning(f"Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            raise FlightServiceError(f"Request failed after {max_retries} attempts: {last_error}") from e
            
        except Exception as e:
            last_error = str(e)
            logger.error(f"Unexpected error: {last_error}", exc_info=True)
            
            if attempt < max_retries:
                wait_time = retry_delay * attempt
                logger.warning(f"Attempt {attempt}/{max_retries} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            raise FlightServiceError(f"Unexpected error after {max_retries} attempts: {last_error}") from e
    
    # This should never be reached due to the raise in the loop
    raise FlightServiceError(f"Unexpected error in make_verteil_request: {last_error}")

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
    trip_type: str = "ONE_WAY"
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
        
    Returns:
        Dictionary containing flight search results
    """
    try:
        if not request_id:
            request_id = str(uuid.uuid4())
            
        logger.info(f"Processing flight search request {request_id}: {origin}-{destination} on {departure_date}")
        
        # Build the AirShopping request
        airshopping_rq = build_airshopping_rq(
            trip_type=trip_type.upper(),  # Ensure trip_type is uppercase
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
        
        # Get the configuration from the app context if available
        config = {}
        try:
            if hasattr(current_app, 'config'):
                config = {
                    'VERTEIL_API_BASE_URL': current_app.config.get('VERTEIL_API_BASE_URL'),
                    'VERTEIL_TOKEN_ENDPOINT': current_app.config.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
                    'VERTEIL_USERNAME': current_app.config.get('VERTEIL_USERNAME'),
                    'VERTEIL_PASSWORD': current_app.config.get('VERTEIL_PASSWORD'),
                    'VERTEIL_THIRD_PARTY_ID': current_app.config.get('VERTEIL_THIRD_PARTY_ID'),
                    'VERTEIL_OFFICE_ID': current_app.config.get('VERTEIL_OFFICE_ID'),
                    'OAUTH2_TOKEN_EXPIRY_BUFFER': current_app.config.get('OAUTH2_TOKEN_EXPIRY_BUFFER', 60)
                }
            else:
                # Fall back to environment variables if not in app context
                import os
                config = {
                    'VERTEIL_API_BASE_URL': os.environ.get('VERTEIL_API_BASE_URL'),
                    'VERTEIL_TOKEN_ENDPOINT': os.environ.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
                    'VERTEIL_USERNAME': os.environ.get('VERTEIL_USERNAME'),
                    'VERTEIL_PASSWORD': os.environ.get('VERTEIL_PASSWORD'),
                    'VERTEIL_THIRD_PARTY_ID': os.environ.get('VERTEIL_THIRD_PARTY_ID'),
                    'VERTEIL_OFFICE_ID': os.environ.get('VERTEIL_OFFICE_ID'),
                    'OAUTH2_TOKEN_EXPIRY_BUFFER': int(os.environ.get('OAUTH2_TOKEN_EXPIRY_BUFFER', '60'))
                }
        except RuntimeError as e:
            # Not in an application context, try environment variables
            import os
            config = {
                'VERTEIL_API_BASE_URL': os.environ.get('VERTEIL_API_BASE_URL'),
                'VERTEIL_TOKEN_ENDPOINT': os.environ.get('VERTEIL_TOKEN_ENDPOINT', '/oauth2/token'),
                'VERTEIL_USERNAME': os.environ.get('VERTEIL_USERNAME'),
                'VERTEIL_PASSWORD': os.environ.get('VERTEIL_PASSWORD'),
                'VERTEIL_THIRD_PARTY_ID': os.environ.get('VERTEIL_THIRD_PARTY_ID'),
                'VERTEIL_OFFICE_ID': os.environ.get('VERTEIL_OFFICE_ID'),
                'OAUTH2_TOKEN_EXPIRY_BUFFER': int(os.environ.get('OAUTH2_TOKEN_EXPIRY_BUFFER', '60'))
            }
            logger.warning(f"Running outside of application context, using environment variables. Error: {str(e)}")
            
        # Make the request to Verteil API using the async version
        logger.info("Sending request to Verteil API...")
        response = await make_async_verteil_request(
            endpoint="/entrygate/rest/request:airShopping",
            payload=airshopping_rq,
            service_name="AirShopping",
            config=config
        )
        
        logger.info("Received response from Verteil API")
        
        # Save full response to a file for debugging
        try:
            import os
            from datetime import datetime
            
            # Create a debug directory if it doesn't exist
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            # Create a timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(debug_dir, f'api_response_{timestamp}.json')
            
            # Write the full response to the file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Full API response saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save API response to file: {str(e)}")
        
        # Log a summary of the response for the console
        logger.debug("Response summary - status: %s, data keys: %s", 
                    response.get('status'), 
                    list(response.get('data', {}).keys()) if isinstance(response.get('data'), dict) else 'N/A')
        
        # Extract flight offers from the response
        try:
            # Check if response has a data object with flightOffers
            if isinstance(response, dict) and "data" in response and isinstance(response["data"], dict):
                data = response["data"]
                logger.info("Response data keys: %s", list(data.keys()))
                
                # Check for flightOffers in the data object
                if "flightOffers" in data and isinstance(data["flightOffers"], list):
                    flight_offers = data["flightOffers"]
                    logger.info("Found %d flight offers in data.flightOffers", len(flight_offers))
                    return {
                        "status": "success",
                        "data": {
                            "flightOffers": flight_offers,
                            "searchParams": data.get("searchParams", {})
                        },
                        "meta": {
                            "count": len(flight_offers),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                else:
                    logger.warning("No flightOffers found in data object")
                    flight_offers = []
            else:
                logger.warning("Unexpected response structure, no data object found")
                flight_offers = []
                
            # Fallback to check other possible locations (for backward compatibility)
            if not flight_offers:
                logger.warning("No flight offers found in data.flightOffers, checking other locations")
                if "flightOffers" in response and isinstance(response["flightOffers"], list):
                    flight_offers = response["flightOffers"]
                elif "AirShoppingRS" in response and "OffersGroup" in response["AirShoppingRS"]:
                    flight_offers = response["AirShoppingRS"]["OffersGroup"]
                    if not isinstance(flight_offers, list):
                        flight_offers = [flight_offers] if flight_offers else []
            
            logger.info("Extracted %d flight offers after fallback", len(flight_offers))
                            
        except Exception as e:
            logger.error("Error parsing flight offers: %s", str(e), exc_info=True)
            logger.error("Response that caused the error: %s", json.dumps(response, indent=2))
            flight_offers = []
            
            # If we still couldn't parse the offers, try to extract any available offers from the response
            logger.warning("Trying to extract offers from unexpected response structure")
            for key, value in response.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    if any(k in value[0] for k in ["OfferID", "flightNumber", "itineraries"]):
                        flight_offers.extend(value)
            
            if not flight_offers:
                logger.error("Could not extract any flight offers from response")
                logger.error("Available keys in response: %s", list(response.keys()))
                if isinstance(response, dict):
                    for key, value in response.items():
                        if isinstance(value, (dict, list)):
                            logger.error("Key %s type: %s", key, type(value).__name__)
                
                # Instead of raising an error, return an empty list to handle gracefully
                flight_offers = []
        
        # Return structured response
        result = {
            "status": "success",
            "data": {
                "flightOffers": flight_offers,
                "searchParams": {
                    "origin": origin,
                    "destination": destination,
                    "departureDate": departure_date,
                    "returnDate": return_date,
                    "adults": adults,
                    "children": children,
                    "infants": infants,
                    "cabinClass": cabin_class
                }
            },
            "meta": {
                "count": len(flight_offers),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_flights: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to search flights: {str(e)}") from e

get_flight_offers = search_flights  # Alias for backward compatibility

def get_flight_price(
    airshopping_response: Dict[str, Any],
    offer_index: int = 0,
    currency: str = DEFAULT_CURRENCY
) -> Dict[str, Any]:
    """
    Get price for a specific flight offer using FlightPrice request
    
    Args:
        airshopping_response: The AirShopping response
        offer_index: Index of the offer to price (default: 0)
        currency: Currency code (default: USD)
        
    Returns:
        Dictionary containing pricing information
    """
    try:
        # Build FlightPrice request
        flightprice_rq = build_flightprice_rq(airshopping_response, offer_index, currency)
        
        # Make request to Verteil API
        logger.info("Sending FlightPrice request to Verteil API...")
        response = make_verteil_request("/entrygate/rest/request:flightPrice", flightprice_rq, "FlightPrice")
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {
                "offer_index": offer_index
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_flight_price: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to get flight price: {str(e)}") from e

def create_booking(
    flight_price_response: Dict[str, Any],
    passenger_details: List[Dict[str, Any]],
    payment_details: Dict[str, Any],
    contact_info: Dict[str, str]
) -> Dict[str, Any]:
    """
    Create a flight booking using OrderCreate request
    
    Args:
        flight_price_response: The FlightPrice response
        passenger_details: List of passenger details
        payment_details: Payment information
        contact_info: Contact information
        
    Returns:
        Dictionary containing booking confirmation
    """
    try:
        # Build OrderCreate request
        ordercreate_rq = build_ordercreate_rq(
            flight_price_response,
            passenger_details,
            payment_details,
            contact_info
        )
        
        # Make request to Verteil API
        logger.info("Sending OrderCreate request to Verteil API...")
        response = make_verteil_request("/entrygate/rest/request:orderCreate", ordercreate_rq, "OrderCreate")
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_booking: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to create booking: {str(e)}") from e

def get_booking_details(booking_reference: str) -> Dict[str, Any]:
    """
    Get details for a specific booking
    
    Args:
        booking_reference: The booking reference number (OrderID)
        
    Returns:
        Dictionary containing booking details with the following structure:
        {
            "status": "success" | "error",
            "data": {
                "booking_reference": str,
                "status": str,
                "passengers": List[Dict],
                "flights": List[Dict],
                "price": Dict,
                "contact_info": Dict
            },
            "meta": {
                "timestamp": str,
                "reference": str
            }
        }
    """
    try:
        # Build the request to retrieve booking details
        request = {
                "Query": {
                    "Filters": {
                    "OrderID": {
                        "Owner": "WY",
                        "Channel": "NDC",
                        "value": booking_reference
                    }
                    }
                }
            }
        
        # Make request to Verteil API
        response = make_verteil_request("/entrygate/rest/request:orderRetrieve", request)
        
        # Transform and return the response
        return {
            "status": "success",
            "data": {
                "booking_reference": booking_reference,
                "status": response.get("Response", {}).get("Order", {}).get("OrderStatus", "UNKNOWN"),
                "passengers": [
                    {
                        "first_name": pax.get("Individual", {}).get("GivenName", ""),
                        "last_name": pax.get("Individual", {}).get("Surname", ""),
                        "type": pax.get("PTC", "ADT"),
                        "passenger_id": pax.get("PaxID", "")
                    }
                    for pax in response.get("Response", {}).get("DataLists", {})
                        .get("PassengerList", {}).get("Passenger", [])
                ],
                "flights": [
                    {
                        "flight_number": f"{segment.get('MarketingCarrier', {}).get('AirlineID', '')}{segment.get('MarketingCarrier', {}).get('FlightNumber', '')}",
                        "origin": segment.get("OriginLocation", {}).get("AirportCode", ""),
                        "destination": segment.get("DestinationLocation", {}).get("AirportCode", ""),
                        "departure_time": segment.get("Departure", {}).get("Date", "") + "T" + segment.get("Departure", {}).get("Time", ""),
                        "arrival_time": segment.get("Arrival", {}).get("Date", "") + "T" + segment.get("Arrival", {}).get("Time", ""),
                        "cabin_class": segment.get("CabinType", {}).get("CabinTypeCode", ""),
                        "booking_class": segment.get("ClassOfService", {}).get("Code", "")
                    }
                    for segment in response.get("Response", {}).get("DataLists", {})
                        .get("FlightSegmentList", {}).get("FlightSegment", [])
                ],
                "price": {
                    "total_amount": response.get("Response", {}).get("DataLists", {})
                        .get("PriceList", [{}])[0].get("TotalAmount", 0),
                    "currency": response.get("Response", {}).get("DataLists", {})
                        .get("PriceList", [{}])[0].get("TotalAmount", {}).get("Code", "USD")
                },
                "contact_info": {
                    "email": response.get("Response", {}).get("DataLists", {})
                        .get("ContactInfoList", {}).get("ContactInformation", {})
                        .get("Contact", {}).get("EmailContact", {}).get("EmailAddress", ""),
                    "phone": next((phone.get("PhoneNumber", "") for phone in 
                        response.get("Response", {}).get("DataLists", {})
                        .get("ContactInfoList", {}).get("ContactInformation", {})
                        .get("Contact", {}).get("PhoneContact", []) 
                        if phone.get("Label") == "MOBILE"), "")
                }
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "reference": booking_reference
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_booking_details: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to retrieve booking details: {str(e)}") from e
    try:
        # Build OrderRetrieve request
        order_retrieve_rq = {
            "OrderRetrieveRQ": {
                "Query": {
                    "OrderID": booking_reference
                }
            }
        }
        
        # Make request to Verteil API
        response = make_verteil_request("/ndc/orderretrieve", order_retrieve_rq)
        
        # Process and return response
        return {
            "status": "success",
            "data": response,
            "meta": {}
        }
        
    except Exception as e:
        logger.error(f"Error in get_booking_details: {str(e)}", exc_info=True)
        raise FlightServiceError(f"Failed to get booking details: {str(e)}") from e

async def process_air_shopping(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process flight search request and return available flight offers.
    
    Args:
        search_criteria: Dictionary containing search parameters with od_segments
        
    Returns:
        Dictionary containing flight offers and metadata
    """
    try:
        trip_type = search_criteria.get('trip_type', 'ONE_WAY')
        od_segments = search_criteria.get('od_segments', [])
        
        if not od_segments:
            raise ValueError("At least one origin-destination segment is required")
            
        # Get the first segment (we'll handle round trips later)
        first_segment = od_segments[0]
        
        # Call the search_flights function with the first segment and await the result
        flight_results = await search_flights(
            origin=first_segment.get('Origin', ''),
            destination=first_segment.get('Destination', ''),
            departure_date=first_segment.get('DepartureDate', ''),
            return_date=od_segments[1].get('DepartureDate') if len(od_segments) > 1 else None,
            adults=search_criteria.get('num_adults', 1),
            children=search_criteria.get('num_children', 0),
            infants=search_criteria.get('num_infants', 0),
            cabin_class=search_criteria.get('cabin_preference', 'ECONOMY'),
            request_id=search_criteria.get('request_id'),
            trip_type=trip_type
        )
        
        # Transform the results to match the frontend's expected format
        transformed_results = {
            "offers": [],
            "trip_type": trip_type,
            "search_criteria": search_criteria,
            "status": "success"
        }
        
        # Log the full response for debugging
        logger.info("=== Verteil API Response ===")
        logger.info(f"Response keys: {list(flight_results.keys())}")
        
        # Initialize the list to store all airline offers
        airline_offers = []
        
        # Log the full response structure for debugging
        logger.info(f"Full response structure: {json.dumps(flight_results, indent=2)[:1000]}...")
        
        # First, get the data object from the response
        if 'data' in flight_results and isinstance(flight_results['data'], dict):
            data = flight_results['data']
            logger.info(f"Data keys: {list(data.keys())}")
            
            # Check for flightOffers in the data object
            if 'flightOffers' in data and isinstance(data['flightOffers'], list):
                logger.info(f"Found {len(data['flightOffers'])} flight offers")
                
                # Process each flight offer
                for offer in data['flightOffers']:
                    if isinstance(offer, dict):
                        # Transform the offer to match our expected format
                        transformed_offer = {
                            "id": offer.get('id', ''),
                            "price": {
                                "amount": float(offer.get('price', {}).get('total', 0)),
                                "currency": offer.get('price', {}).get('currency', 'USD')
                            },
                            "segments": []
                        }
                        
                        # Add segments if available
                        if 'itineraries' in offer and isinstance(offer['itineraries'], list):
                            for itinerary in offer['itineraries']:
                                if 'segments' in itinerary and isinstance(itinerary['segments'], list):
                                    for segment in itinerary['segments']:
                                        transformed_offer['segments'].append({
                                            "departure": {
                                                "iataCode": segment.get('departure', {}).get('iataCode', ''),
                                                "at": segment.get('departure', {}).get('at', '')
                                            },
                                            "arrival": {
                                                "iataCode": segment.get('arrival', {}).get('iataCode', ''),
                                                "at": segment.get('arrival', {}).get('at', '')
                                            },
                                            "carrierCode": segment.get('carrierCode', ''),
                                            "number": segment.get('number', '')
                                        })
                        
                        airline_offers.append(transformed_offer)
        # If no flightOffers found, try the OffersGroup structure as fallback
        elif 'OffersGroup' in flight_results and isinstance(flight_results['OffersGroup'], dict):
            offers_group = flight_results['OffersGroup']
            logger.info(f"OffersGroup keys: {list(offers_group.keys())}")
            
            # Get all airline offers from AirlineOffers array
            if 'AirlineOffers' in offers_group and isinstance(offers_group['AirlineOffers'], list):
                for airline_offer_group in offers_group['AirlineOffers']:
                    if 'AirlineOffer' in airline_offer_group:
                        offers = airline_offer_group['AirlineOffer']
                        if not isinstance(offers, list):
                            offers = [offers]
                            
                        for offer in offers:
                            if 'PricedOffer' in offer and 'OfferPrice' in offer['PricedOffer']:
                                # Transform the offer to our format
                                transformed_offer = {
                                    "id": offer.get('OfferID', {}).get('value', ''),
                                    "price": {
                                        "amount": 0,  # Will be updated from OfferPrice
                                        "currency": 'USD'  # Default, will be updated from OfferPrice
                                    },
                                    "segments": []
                                }
                                
                                # Process prices
                                offer_prices = offer['PricedOffer']['OfferPrice']
                                if not isinstance(offer_prices, list):
                                    offer_prices = [offer_prices]
                                    
                                for price in offer_prices:
                                    if 'PriceDetail' in price and 'TotalAmount' in price['PriceDetail']:
                                        total = price['PriceDetail']['TotalAmount']
                                        if 'SimpleCurrencyPrice' in total:
                                            transformed_offer['price'] = {
                                                "amount": float(total['SimpleCurrencyPrice'].get('value', 0)),
                                                "currency": total['SimpleCurrencyPrice'].get('Code', 'USD')
                                            }
                                            break
                                
                                # Process segments
                                for price in offer_prices:
                                    if 'RequestedDate' in price and 'Associations' in price['RequestedDate']:
                                        for assoc in price['RequestedDate']['Associations']:
                                            if 'ApplicableFlight' in assoc and 'FlightSegmentReference' in assoc['ApplicableFlight']:
                                                segments = assoc['ApplicableFlight']['FlightSegmentReference']
                                                if not isinstance(segments, list):
                                                    segments = [segments]
                                                    
                                                for segment in segments:
                                                    if 'ClassOfService' in segment and 'MarketingName' in segment['ClassOfService']:
                                                        transformed_offer['segments'].append({
                                                            "departure": {
                                                                "iataCode": segment.get('Departure', {}).get('AirportCode', ''),
                                                                "at": segment.get('Departure', {}).get('Date', '') + 'T' + segment.get('Departure', {}).get('Time', '')
                                                            },
                                                            "arrival": {
                                                                "iataCode": segment.get('Arrival', {}).get('AirportCode', ''),
                                                                "at": segment.get('Arrival', {}).get('Date', '') + 'T' + segment.get('Arrival', {}).get('Time', '')
                                                            },
                                                            "carrierCode": segment.get('MarketingCarrier', {}).get('AirlineID', ''),
                                                            "number": segment.get('MarketingCarrier', {}).get('FlightNumber', ''),
                                                            "cabinClass": segment['ClassOfService']['MarketingName'].get('value', 'ECONOMY')
                                                        })
                                
                                airline_offers.append(transformed_offer)
        
        logger.info(f"Found {len(airline_offers)} airline offers in the response")
        
        # Transform each offer
        for offer in airline_offers:
            transformed_offer = {
                "id": offer.get('OfferID', {}).get('value', ''),
                "price": {
                    "amount": float(offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {}).get('value', 0)),
                    "currency": offer.get('TotalPrice', {}).get('SimpleCurrencyPrice', {}).get('currency_code', 'USD')
                },
                "segments": []
            }
            
            # Get the offer items (flights)
            offer_items = offer.get('OfferItem', [])
            if not isinstance(offer_items, list):
                offer_items = [offer_items]
                
            for item in offer_items:
                # Get the flight segment references
                segment_refs = item.get('Service', {}).get('ServiceDefinitionRef', {})
                if not isinstance(segment_refs, list):
                    segment_refs = [segment_refs]
                    
                for seg_ref in segment_refs:
                    segment_id = seg_ref.get('value', '')
                    # Find the segment in the flight segment list
                    for flight_segment in air_shopping_rs.get('DataLists', {}).get('FlightSegmentList', {}).get('FlightSegment', []):
                        if flight_segment.get('SegmentKey', '') == segment_id:
                            departure = flight_segment.get('Departure', {})
                            arrival = flight_segment.get('Arrival', {})
                            marketing_airline = flight_segment.get('MarketingCarrierInfo', {}).get('Carrier', {})
                            
                            transformed_segment = {
                                "origin": departure.get('AirportCode', {}).get('value', ''),
                                "destination": arrival.get('AirportCode', {}).get('value', ''),
                                "departure_time": departure.get('Date', '') + 'T' + departure.get('Time', ''),
                                "arrival_time": arrival.get('Date', '') + 'T' + arrival.get('Time', ''),
                                "flight_number": flight_segment.get('MarketingCarrierInfo', {}).get('FlightNumber', ''),
                                "airline": marketing_airline.get('AirlineID', ''),
                                "airline_name": marketing_airline.get('Name', ''),
                                "cabin_class": search_criteria.get('cabin_preference', 'ECONOMY'),
                                "equipment": flight_segment.get('Equipment', {}).get('AircraftCode', '')
                            }
                            transformed_offer["segments"].append(transformed_segment)
            
            if transformed_offer["segments"]:  # Only add offers with valid segments
                transformed_results["offers"].append(transformed_offer)
        
        return transformed_results
        
    except FlightServiceError as e:
        logger.error(f"Error in process_air_shopping: {str(e)}")
        return {"error": str(e), "status": "error"}
    except Exception as e:
        logger.error(f"Unexpected error in process_air_shopping: {str(e)}", exc_info=True)
        return {"error": f"An unexpected error occurred: {str(e)}", "status": "error"}

def process_flight_price(price_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process flight pricing request and return detailed pricing information.
    
    Args:
        price_request: Dictionary containing pricing request data
        
    Returns:
        Dictionary containing detailed pricing information
    """
    try:
        # Call the get_flight_price function
        return get_flight_price(
            airshopping_response=price_request['airshopping_response'],
            offer_index=price_request.get('offer_index', 0)
        )
        
    except FlightServiceError as e:
        logger.error(f"Error in process_flight_price: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in process_flight_price: {str(e)}")
        return {"error": "An unexpected error occurred while pricing the flight"}

def process_order_create(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process order creation request and return booking confirmation.
    
    Args:
        order_data: Dictionary containing order data with the following structure:
        {
            "flight_offer": Dict,  # Flight price response
            "passengers": List[Dict],  # List of passenger details
            "payment": Dict,  # Payment information
            "contact_info": Dict  # Contact information
        }
        
    Returns:
        Dictionary containing booking confirmation with the following structure:
        {
            "status": "success" | "error",
            "data": {
                "booking_reference": str,
                "status": str,
                "etickets": List[Dict],
                "amount_paid": float,
                "currency": str
            },
            "meta": {
                "timestamp": str,
                "reference": str
            }
        }
    """
    try:
        # Extract data from order_data
        flight_offer = order_data.get("flight_offer", {})
        passengers = order_data.get("passengers", [])
        payment = order_data.get("payment", {})
        contact_info = order_data.get("contact_info", {})
        
        # Validate required fields
        if not flight_offer:
            raise FlightServiceError("Missing required field: flight_offer")
        if not passengers:
            raise FlightServiceError("Missing required field: passengers")
        if not payment:
            raise FlightServiceError("Missing required field: payment")
        if not contact_info:
            raise FlightServiceError("Missing required field: contact_info")
        
        # Create the booking
        booking_response = create_booking(
            flight_price_response=flight_offer,
            passenger_details=passengers,
            payment_details=payment,
            contact_info=contact_info
        )
        
        # Extract relevant data from the response
        order_response = booking_response.get("data", {})
        order_id = order_response.get("Response", {}).get("Order", {}).get("OrderID", "")
        
        if not order_id:
            raise FlightServiceError("Failed to retrieve order ID from the booking response")
        
        # Transform the response
        return {
            "status": "success",
            "data": {
                "booking_reference": order_id,
                "status": order_response.get("Response", {}).get("Order", {}).get("OrderStatus", "CONFIRMED"),
                "etickets": [
                    {
                        "ticket_number": doc.get("TicketDocInfo", {}).get("TicketDocument", {})
                            .get("TicketDocNbr", ""),
                        "passenger_name": doc.get("PassengerReference", {}).get("PassengerID", ""),
                        "status": doc.get("TicketDocInfo", {}).get("Status", {})
                            .get("StatusCode", "ISSUED")
                    }
                    for doc in order_response.get("Response", {}).get("DataLists", {})
                        .get("TicketDocInfoList", {}).get("TicketDocInfo", [])
                ],
                "amount_paid": order_response.get("Response", {}).get("DataLists", {})
                    .get("PriceList", [{}])[0].get("TotalAmount", {}).get("value", 0),
                "currency": order_response.get("Response", {}).get("DataLists", {})
                    .get("PriceList", [{}])[0].get("TotalAmount", {}).get("Code", "USD")
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "reference": order_id
            }
        }
        
    except FlightServiceError as e:
        logger.error(f"Error in process_order_create: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        error_msg = f"Unexpected error in process_order_create: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise FlightServiceError(error_msg) from e

# Transformation functions for backward compatibility
def _transform_airshopping_rs(airshopping_rs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform AirShopping response for the frontend
    
    Args:
        airshopping_rs: Raw AirShopping response
        
    Returns:
        Transformed response for the frontend
    """
    # This is a placeholder - implement transformation as needed
    return airshopping_rs

def _transform_flightprice_rs(flightprice_rs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform FlightPrice response for the frontend
    
    Args:
        flightprice_rs: Raw FlightPrice response
        
    Returns:
        Transformed response for the frontend
    """
    # This is a placeholder - implement transformation as needed
    return flightprice_rs

def _transform_ordercreate_rs(ordercreate_rs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform OrderCreate response for the frontend
    
    Args:
        ordercreate_rs: Raw OrderCreate response
        
    Returns:
        Transformed response for the frontend
    """
    # This is a placeholder - implement transformation as needed
    return ordercreate_rs
