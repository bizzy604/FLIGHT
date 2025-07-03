"""Core Flight Service Module

This module contains the base FlightService class that provides core functionality
for interacting with the Verteil NDC API, including authentication, request handling,
and error management.
"""
import os
import json
import logging
import aiohttp
from aiohttp import BasicAuth
import time
import uuid # For X-Request-ID
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic, Type
from urllib.parse import urljoin, urlencode # urlencode might not be needed if aiohttp handles form data correctly
import asyncio # For asyncio.sleep

# Assuming these paths are correct relative to core.py
# If 'utils' or 'services.flight' are top-level packages in 'Backend', adjust paths if needed.
# e.g., from Backend.utils.cache_manager import cache_manager
# e.g., from Backend.services.flight.decorators import ...
from utils.cache_manager import cache_manager
from services.flight.decorators import async_cache, async_rate_limited
from services.flight.exceptions import (
    FlightServiceError,
    RateLimitExceeded,
    AuthenticationError,
    APIError
)
from services.flight.types import (
    SearchCriteria,
    FlightSearchResponse,
    PricingResponse,
    BookingResponse
)
from utils.auth import TokenManager

logger = logging.getLogger(__name__)

class FlightService:
    DEFAULT_CONFIG = {
        'VERTEIL_API_BASE_URL': 'https://api.stage.verteil.com', # Default, should be overridden by app config
        'VERTEIL_USERNAME': None,
        'VERTEIL_PASSWORD': None,
        'VERTEIL_TOKEN_ENDPOINT_PATH': '/oauth2/token', # Default path for token endpoint
        'VERTEIL_API_TIMEOUT': 30,  # Default API timeout in seconds
        'VERTEIL_MAX_RETRIES': 3,   # Default max retries for API calls
        'VERTEIL_RETRY_DELAY': 1,   # Default base delay for retries in seconds
        'OAUTH2_TOKEN_EXPIRY_BUFFER': 60,  # Seconds to subtract from token's expires_in for early refresh
        'CACHE_TIMEOUT': 300,      # Default cache timeout for @async_cache decorator
        'RATE_LIMIT': 100,         # Default rate limit for @async_rate_limited (requests)
        'RATE_WINDOW': 60,         # Default rate window for @async_rate_limited (seconds)
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._session: Optional[aiohttp.ClientSession] = None
        # Use the singleton TokenManager instance instead of creating a new one
        self._token_manager = TokenManager.get_instance()
        self._token_manager.set_config(self.config)

        # Validate essential configuration for OAuth
        # These keys should match what's loaded in Backend/config.py
        required_oauth_keys = [
            'VERTEIL_USERNAME', 'VERTEIL_PASSWORD',
            'VERTEIL_API_BASE_URL', 'VERTEIL_TOKEN_ENDPOINT_PATH'
        ]
        missing_keys = [key for key in required_oauth_keys if not self.config.get(key)]
        if missing_keys:
            raise FlightServiceError(f"FlightService missing critical OAuth configuration: {', '.join(missing_keys)}")
        logger.info("FlightService initialized with necessary OAuth configurations.")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout_seconds = float(self.config.get('VERTEIL_API_TIMEOUT', 30))
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        await self._get_session() # Ensure session is created on entry
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _get_access_token(self) -> str:
        """Get access token using the centralized TokenManager."""
        try:
            # TokenManager returns the token in 'Bearer <token>' format
            full_token = self._token_manager.get_token(self.config)
            # Extract just the token part (remove 'Bearer ' prefix)
            if full_token.startswith('Bearer '):
                return full_token[7:]  # Remove 'Bearer ' prefix
            return full_token
        except Exception as e:
            logger.error(f"Failed to get access token from TokenManager: {str(e)}", exc_info=True)
            raise AuthenticationError(f"Failed to get access token: {str(e)}") from e

    async def _get_headers(self, service_name: str, airline_code: Optional[str] = None) -> Dict[str, str]:
        access_token = await self._get_access_token()

        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Authorization': f'Bearer {access_token}',
            'OfficeId': self.config.get('VERTEIL_OFFICE_ID'),
            'service': service_name,
            'User-Agent': 'PostmanRuntime/7.41',  # Match Postman exactly
            'Cache-Control': 'no-cache',  # Add missing Postman header
            'Accept-Encoding': 'gzip, deflate, br',  # Add missing Postman header
            'Connection': 'keep-alive'  # Add missing Postman header
        }

        # For AirShopping: Completely omit ThirdpartyId header to get all airlines
        # For other services: Use specific airline code or default
        if service_name != 'AirShopping':
            # For FlightPrice and OrderCreate operations, use specific airline code
            third_party_id = airline_code if airline_code else self.config.get('VERTEIL_THIRD_PARTY_ID', '')
            headers['ThirdpartyId'] = third_party_id

        return headers

    @async_rate_limited(limit=100, window=60) # Decorators from original code
    @async_cache(timeout=300)                 # Decorators from original code
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        service_name: str,
        method: str = 'POST',
        airline_code: Optional[str] = None,
        **kwargs # Used to pass request_id from route context
    ) -> Dict[str, Any]:
        url = urljoin(str(self.config['VERTEIL_API_BASE_URL']).rstrip('/') + '/', endpoint.lstrip('/'))
        headers = await self._get_headers(service_name, airline_code) # _get_headers is now async

        # Propagate request_id from calling context (e.g., route handler) if available
        # Otherwise, use the one generated in _get_headers or generate a new one for logging
        log_request_id = kwargs.get('request_id', headers.get('X-Request-ID', str(uuid.uuid4())))
        
        # Ensure request_id is never in the payload - remove it if present
        api_payload = {k: v for k, v in payload.items() if k != 'request_id'}
        
        # If payload originally had request_id, use that for logging consistency
        if 'request_id' in payload:
            log_request_id = payload['request_id']

        logger.info(f"Making {method} request to {url} for service {service_name} (ReqID: {log_request_id}).")


        max_retries = int(self.config.get('VERTEIL_MAX_RETRIES', 3))
        retry_delay_base = int(self.config.get('VERTEIL_RETRY_DELAY', 1))

        for attempt in range(max_retries):
            try:
                session = await self._get_session()
                async with session.request(
                    method=method,
                    url=url,
                    json=api_payload, # Verteil API endpoints expect JSON body without request_id
                    headers=headers,
                    **{k:v for k,v in kwargs.items() if k != 'request_id'} # Pass other kwargs, but not request_id as it's in payload
                ) as response:
                    # Attempt to get JSON, but handle cases where it might not be (e.g. unexpected HTML error page)
                    try:
                        response_data = await response.json()
                    except aiohttp.ContentTypeError:
                        response_text = await response.text()
                        logger.error(f"API request for {service_name} (ReqID: {log_request_id}) failed with status {response.status}. Response was not JSON: {response_text[:500]}")
                        # If it's a 401, still try to invalidate token
                        if response.status == 401 and attempt < max_retries -1:
                             logger.warning(f"Received 401 (Unauthorized) with non-JSON response for {service_name} (ReqID: {log_request_id}). Clearing TokenManager token.")
                             self._token_manager.clear_token()
                             # Fall through to retry logic
                        else:
                             raise APIError(f"API request for {service_name} (ReqID: {log_request_id}) failed with status {response.status}. Response was not JSON: {response_text[:200]}", status_code=response.status)


                    if response.status >= 400:
                        error_msg = f"API request for {service_name} (ReqID: {log_request_id}) failed with status {response.status}. Response: {json.dumps(response_data)}"
                        if response.status == 401: # Unauthorized
                            logger.warning(f"Received 401 (Unauthorized) for {service_name} (ReqID: {log_request_id}). Clearing TokenManager token.")
                            self._token_manager.clear_token()
                            if attempt == max_retries - 1: # Last attempt
                                raise AuthenticationError(error_msg)
                            # Fall through to retry logic, will attempt to get new token on next _get_headers call
                        elif response.status == 429: # Rate limit
                            raise RateLimitExceeded(f"Rate limit exceeded for {service_name} (ReqID: {log_request_id}). Please try again later.")
                        else: # Other client/server errors
                            raise APIError(error_msg, status_code=response.status, response=response_data)
                    
                    if response.status == 200:
                        logger.info(f"Successfully received API response for {service_name} (ReqID: {log_request_id}) with status {response.status}")

                        # Log airline codes found in AirShopping response for debugging
                        if service_name == "AirShopping":
                            if 'DataLists' in response_data and 'AirlineList' in response_data['DataLists']:
                                airlines = response_data['DataLists']['AirlineList']
                                airline_codes = [airline.get('AirlineID', 'Unknown') for airline in airlines] if isinstance(airlines, list) else []
                                logger.info(f"Airlines found in response: {airline_codes}")
                            else:
                                logger.info(f"No AirlineList found in DataLists")

                        return response_data # Success
            
            except aiohttp.ClientError as e: # Includes ClientConnectionError, ClientTimeout etc.
                logger.warning(f"Attempt {attempt + 1}/{max_retries} for {service_name} (ReqID: {log_request_id}) failed with ClientError: {str(e)}.")
                if attempt == max_retries - 1:
                    raise APIError(f"Request for {service_name} (ReqID: {log_request_id}) failed after {max_retries} attempts due to ClientError: {str(e)}")
            # Catch other exceptions like JSONDecodeError from response.json() if content type is wrong but not caught by ContentTypeError
            except Exception as e: 
                logger.error(f"Attempt {attempt + 1}/{max_retries} for {service_name} (ReqID: {log_request_id}) failed with unexpected error: {str(e)}", exc_info=True)
                if attempt == max_retries - 1:
                    raise APIError(f"Request for {service_name} (ReqID: {log_request_id}) failed after {max_retries} attempts due to unexpected error: {str(e)}")
            
            # If we are here, it means an attempt failed and it's not the last one, so sleep and retry.
            sleep_duration = retry_delay_base * (2**attempt) # Exponential backoff
            logger.info(f"Retrying attempt {attempt + 2}/{max_retries} for {service_name} (ReqID: {log_request_id}) in {sleep_duration}s...")
            await asyncio.sleep(sleep_duration)
        
        # Should not be reached if max_retries > 0, as loop will either return or raise.
        # Adding for safety in case max_retries is 0 or loop logic changes.
        raise APIError(f"Request for {service_name} (ReqID: {log_request_id}) failed after all retries.")


    # Abstract methods to be implemented by subclasses
    async def search_flights(self, criteria: SearchCriteria) -> FlightSearchResponse:
        raise NotImplementedError("Subclasses must implement search_flights")
    
    async def get_flight_price(self, request_data: Dict[str, Any]) -> PricingResponse:
        raise NotImplementedError("Subclasses must implement get_flight_price")
    
    async def create_booking(self, booking_data: Dict[str, Any]) -> BookingResponse:
        raise NotImplementedError("Subclasses must implement create_booking")
