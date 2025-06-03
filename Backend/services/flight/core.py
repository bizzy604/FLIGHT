"""
Core Flight Service Module

This module contains the base functionality for interacting with the Verteil NDC API.
It handles common operations like making API requests and managing authentication.
"""
import os
import json
import logging
import aiohttp
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic, Type
from urllib.parse import urljoin

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
    BookingResponse,
    ODSegment,
    PassengerCounts
)

# Configure logging
logger = logging.getLogger(__name__)

class FlightService:
    """
    Base class for flight service operations.
    
    This class provides common functionality for interacting with the Verteil NDC API,
    including request handling, authentication, and error management.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'VERTEIL_API_BASE_URL': 'https://api.verteil.com/ndc',
        'VERTEIL_API_KEY': None,
        'VERTEIL_API_SECRET': None,
        'VERTEIL_API_TIMEOUT': 30,
        'VERTEIL_MAX_RETRIES': 3,
        'VERTEIL_RETRY_DELAY': 1,
        'CACHE_TIMEOUT': 300,  # 5 minutes
        'RATE_LIMIT': 100,     # requests
        'RATE_WINDOW': 60,     # seconds
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the FlightService with configuration.
        
        Args:
            config: Optional configuration dictionary. Will be merged with defaults.
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._session = None
        self._token_manager = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config['VERTEIL_API_TIMEOUT'])
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close the aiohttp session if it exists."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _get_headers(self, service_name: str) -> Dict[str, str]:
        """
        Get headers for Verteil API requests.
        
        Args:
            service_name: The name of the service (AirShopping, FlightPrice, OrderCreate)
            
        Returns:
            Dictionary containing the necessary headers
            
        Raises:
            AuthenticationError: If required configuration is missing
        """
        api_key = self.config.get('VERTEIL_API_KEY')
        api_secret = self.config.get('VERTEIL_API_SECRET')
        
        if not api_key or not api_secret:
            raise AuthenticationError("Missing API key or secret in configuration")
        
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-Key': api_key,
            'X-API-Secret': api_secret,
            'X-Service-Name': service_name,
            'X-Request-ID': str(hash(f"{service_name}_{os.urandom(8).hex()}"))
        }
    
    @async_rate_limited(limit=100, window=60)
    @async_cache(timeout=300)
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        service_name: str,
        method: str = 'POST',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an asynchronous request to the Verteil NDC API.
        
        Args:
            endpoint: API endpoint (e.g., 'airshopping', 'flightprice')
            payload: Request payload as a dictionary
            service_name: Name of the service for logging and headers
            method: HTTP method (default: 'POST')
            **kwargs: Additional arguments to pass to aiohttp request
            
        Returns:
            API response as a dictionary
            
        Raises:
            APIError: If the request fails after retries
        """
        url = urljoin(self.config['VERTEIL_API_BASE_URL'].rstrip('/') + '/', endpoint.lstrip('/'))
        headers = self._get_headers(service_name)
        
        # Add request ID to payload if not present
        if 'request_id' in kwargs and 'request_id' not in payload:
            payload['request_id'] = kwargs['request_id']
        
        logger.info(f"Making {method} request to {url} with payload: {payload}")
        
        max_retries = self.config['VERTEIL_MAX_RETRIES']
        retry_delay = self.config['VERTEIL_RETRY_DELAY']
        
        for attempt in range(max_retries):
            try:
                session = await self._get_session()
                
                async with session.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    **kwargs
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        error_msg = f"API request failed with status {response.status}: {response_data}"
                        if response.status == 401:
                            raise AuthenticationError(error_msg)
                        elif response.status == 429:
                            raise RateLimitExceeded("Rate limit exceeded. Please try again later.")
                        else:
                            raise APIError(
                                error_msg,
                                status_code=response.status,
                                response=response_data
                            )
                    
                    return response_data
                    
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise APIError(f"Request failed after {max_retries} attempts: {str(e)}")
                
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    
    async def search_flights(self, criteria: SearchCriteria) -> FlightSearchResponse:
        """
        Search for flights based on the given criteria.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement search_flights")
    
    async def get_flight_price(self, request_data: Dict[str, Any]) -> PricingResponse:
        """
        Get pricing for a specific flight offer.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_flight_price")
    
    async def create_booking(self, booking_data: Dict[str, Any]) -> BookingResponse:
        """
        Create a new flight booking.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement create_booking")
    
    async def get_booking_details(self, booking_reference: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific booking.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_booking_details")
