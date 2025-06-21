"""
Flight Pricing Module

This module handles flight pricing operations using the Verteil NDC API.
"""
import logging
from typing import Dict, Any, Optional, List
import uuid
import sys
import os

# Import the flight data transformer and request builder from their respective packages
from utils.flight_datatransformer import FlightPriceTransformer
from scripts.build_flightprice_rq import build_flight_price_request

# Import service components
from services.flight.core import FlightService
from services.flight.decorators import async_cache, async_rate_limited
from services.flight.exceptions import FlightServiceError, ValidationError
from services.flight.types import PricingResponse, SearchCriteria

logger = logging.getLogger(__name__)

class FlightPricingService(FlightService):
    """Service for handling flight pricing operations."""
    
    @async_rate_limited(limit=100, window=60)
    @async_cache(timeout=300)
    async def get_flight_price(
        self,
        airshopping_response: Dict[str, Any],
        offer_id: str,
        shopping_response_id: str,
        currency: str = "USD",
        request_id: Optional[str] = None,
    ) -> PricingResponse:
        """
        Get pricing for a specific flight offer.
        
        Args:
            airshopping_response: The AirShopping response
            offer_id: The ID of the offer to price
            shopping_response_id: The ShoppingResponseID from AirShoppingRS
            currency: Currency code (default: USD)
            request_id: Optional request ID for tracking
            
        Returns:
            PricingResponse containing price details or error information
            
        Raises:
            ValidationError: If the request data is invalid
            APIError: If there's an error communicating with the API
        """
        try:
            # Validate input
            if not airshopping_response or not offer_id or not shopping_response_id:
                raise ValidationError("Missing required parameters for flight pricing")
            
            # Generate a request ID if not provided
            request_id = request_id or str(uuid.uuid4())
            
            # Extract airline code from the offer for dynamic thirdPartyId
            airline_code = self._extract_airline_code_from_offer(airshopping_response, offer_id)
            logger.info(f"Extracted airline code '{airline_code}' for offer {offer_id} (ReqID: {request_id})")
            
            # Build the request payload
            payload = self._build_pricing_payload(
                airshopping_response=airshopping_response,
                offer_id=offer_id
            )
            
            # Make the API request with dynamic airline code
            response = await self._make_request(
                endpoint='/entrygate/rest/request:flightPrice',
                payload=payload,
                service_name='FlightPrice',
                airline_code=airline_code,
                request_id=request_id
            )
            
            # Process and return the response
            return {
                'status': 'success',
                'data': self._process_pricing_response(response, request_id),
                'request_id': request_id
            }
            
        except ValidationError as e:
            logger.error(f"Validation error in get_flight_price: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'request_id': request_id
            }
        except Exception as e:
            logger.error(f"Error in get_flight_price: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': f"Failed to get flight price: {str(e)}",
                'request_id': request_id
            }
    
    def _extract_airline_code_from_offer(self, airshopping_response: Dict[str, Any], offer_id: str) -> Optional[str]:
        """
        Extract airline code from the AirShopping response for a specific offer.
        
        Args:
            airshopping_response: The AirShopping response containing offers
            offer_id: The ID of the offer to extract airline code from
            
        Returns:
            The airline code (e.g., 'KQ', 'WY') or None if not found
        """
        try:
            # Handle both wrapped and unwrapped response formats
            # Check if response is wrapped in 'AirShoppingRS'
            if 'AirShoppingRS' in airshopping_response:
                offers_group = airshopping_response['AirShoppingRS'].get('OffersGroup', {})
            else:
                offers_group = airshopping_response.get('OffersGroup', {})
            
            # Look for the specific offer
            air_line_offers = offers_group.get('AirlineOffers', [])
            if not isinstance(air_line_offers, list):
                air_line_offers = [air_line_offers]
            
            # First pass: Look for exact offer match
            for airline_offer in air_line_offers:
                # The structure is AirlineOffers -> AirlineOffer (not 'Offer')
                offers = airline_offer.get('AirlineOffer', [])
                if not isinstance(offers, list):
                    offers = [offers]
                
                for offer in offers:
                    # Extract OfferID value properly
                    offer_id_obj = offer.get('OfferID', {})
                    current_offer_id = offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj
                    if current_offer_id == offer_id:
                        # Try multiple paths for airline code extraction
                        # 1. From Owner at airline_offer level
                        owner = airline_offer.get('Owner', {})
                        if isinstance(owner, dict):
                            airline_code = owner.get('value')
                            if airline_code:
                                logger.info(f"Found airline code '{airline_code}' for offer {offer_id} from Owner")
                                return airline_code
                        
                        # 2. From ValidatingCarrier in the offer
                        validating_carrier = offer.get('ValidatingCarrier', {})
                        if isinstance(validating_carrier, dict):
                            airline_code = validating_carrier.get('value')
                            if airline_code:
                                logger.info(f"Found airline code '{airline_code}' for offer {offer_id} from ValidatingCarrier")
                                return airline_code
                        
                        # 3. From FlightSegments if available
                        flight_segments = offer.get('FlightSegments', [])
                        if isinstance(flight_segments, list) and flight_segments:
                            for segment in flight_segments:
                                operating_carrier = segment.get('OperatingCarrier', {})
                                if isinstance(operating_carrier, dict):
                                    airline_code = operating_carrier.get('value')
                                    if airline_code:
                                        logger.info(f"Found airline code '{airline_code}' for offer {offer_id} from FlightSegments")
                                        return airline_code
            
            # If we reach here, the specific offer was not found
            logger.warning(f"Could not find offer {offer_id} in AirShopping response")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting airline code for offer {offer_id}: {str(e)}", exc_info=True)
            return None
    
    def _build_pricing_payload(
        self,
        airshopping_response: Dict[str, Any],
        offer_id: str
    ) -> Dict[str, Any]:
        """
        Build the FlightPrice request payload using the request builder.
        
        Args:
            airshopping_response: The AirShopping response (may be transformed frontend format)
            offer_id: The ID of the offer to price
            
        Returns:
            Dictionary containing the request payload
        """
        try:
            # Check if we received transformed frontend data (has 'metadata' and 'offers' keys)
            if 'metadata' in airshopping_response and 'offers' in airshopping_response:
                logger.info("DEBUG: Received transformed frontend data, retrieving original from cache")
                
                # Get the cache key from metadata
                cache_key = airshopping_response['metadata'].get('cache_key')
                if not cache_key:
                    logger.error("DEBUG: No cache_key found in metadata")
                    raise ValueError("Cache key not found in response metadata")
                
                # Retrieve the original cached data
                from utils.cache_manager import cache_manager
                cached_data = cache_manager.get(cache_key)
                
                if not cached_data:
                    logger.error(f"DEBUG: No cached data found for key: {cache_key}")
                    raise ValueError(f"Original response data not found in cache for key: {cache_key}")
                
                # Extract the raw_response (original AirShoppingRS format)
                # The cached data contains the complete result['data'] structure
                logger.info(f"DEBUG: Cached data keys: {list(cached_data.keys()) if isinstance(cached_data, dict) else 'Not a dict'}")
                
                raw_response = cached_data.get('raw_response')
                if not raw_response:
                    logger.error("DEBUG: No raw_response found in cached data")
                    logger.error(f"DEBUG: Available cached_data structure: {str(cached_data)[:500]}...")
                    raise ValueError("Original AirShoppingRS data not found in cache")
                
                logger.info("DEBUG: Successfully retrieved original AirShoppingRS data from cache")
                logger.info(f"DEBUG: raw_response keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'Not a dict'}")
                
                # Use the original raw response
                original_response = raw_response
            else:
                logger.info("DEBUG: Received raw AirShoppingRS data directly")
                original_response = airshopping_response
            
            # Find the selected offer index based on offer_id
            selected_offer_index = 0
            
            # Handle both wrapped and unwrapped response formats
            # Check if response is wrapped in 'AirShoppingRS'
            if 'AirShoppingRS' in original_response:
                logger.info("DEBUG: Found AirShoppingRS wrapper, unwrapping data")
                air_shopping_data = original_response['AirShoppingRS']
                offers_group = air_shopping_data.get('OffersGroup', {})
                # Pass the unwrapped data to build_flight_price_request
                unwrapped_response = air_shopping_data
            else:
                logger.info("DEBUG: No AirShoppingRS wrapper found, using data directly")
                offers_group = original_response.get('OffersGroup', {})
                unwrapped_response = original_response
            
            # Validate that we have the expected data structure
            airline_offers_list = offers_group.get('AirlineOffers', [])
            if not airline_offers_list or not isinstance(airline_offers_list, list):
                logger.error(f"DEBUG: No valid AirlineOffers found. OffersGroup keys: {list(offers_group.keys()) if isinstance(offers_group, dict) else 'Not a dict'}")
                raise ValueError("No AirlineOffers found in the response data")
            
            # Find the matching offer index
            if airline_offers_list and isinstance(airline_offers_list, list):
                airline_offers = airline_offers_list[0].get('AirlineOffer', [])
                logger.info(f"DEBUG: Found {len(airline_offers)} offers in first AirlineOffers entry")
                for i, offer in enumerate(airline_offers):
                    # Extract OfferID value properly - it's a dict with 'value' field
                    offer_id_obj = offer.get('OfferID', {})
                    current_offer_id = offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj
                    if current_offer_id == offer_id:
                        selected_offer_index = i
                        logger.info(f"Found matching offer at index {i} for offer_id: {offer_id}")
                        break
            
            # Use the request builder to create the payload with unwrapped data
            payload = build_flight_price_request(
                airshopping_response=unwrapped_response,
                selected_offer_index=selected_offer_index
            )
            
            logger.info(f"Built FlightPrice payload for offer {offer_id} at index {selected_offer_index}")
            return payload
            
        except Exception as e:
            logger.error(f"Error building FlightPrice payload: {str(e)}")
            raise ValidationError(f"Failed to build pricing payload: {str(e)}") from e
    
    def _process_pricing_response(self, response: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process the FlightPrice API response using FlightPriceTransformer.
        
        Args:
            response: Raw API response from FlightPrice endpoint
            request_id: Request ID for caching purposes
            
        Returns:
            Transformed response data compatible with frontend
        """
        try:
            # Check if response contains FlightPriceRS
            if 'FlightPriceRS' in response:
                flight_price_data = response['FlightPriceRS']
            else:
                flight_price_data = response
            
            # Debug: Log the structure of flight_price_data
            logger.info(f"[DEBUG] FlightPrice data structure keys: {list(flight_price_data.keys()) if isinstance(flight_price_data, dict) else 'Not a dict'}")
            
            # Check for API errors first
            if 'Errors' in flight_price_data:
                errors = flight_price_data['Errors']
                error_messages = []
                if 'Error' in errors:
                    for error in errors['Error']:
                        error_msg = f"Code: {error.get('Code', 'Unknown')}, Text: {error.get('value', 'Unknown error')}, Owner: {error.get('Owner', 'Unknown')}"
                        error_messages.append(error_msg)
                        logger.error(f"[API ERROR] FlightPrice API returned error: {error_msg}")
                
                raise ValueError(f"FlightPrice API returned errors: {'; '.join(error_messages)}")
            
            # Check if required keys exist for FlightPriceTransformer
            required_keys = ['DataLists', 'PricedFlightOffers']
            missing_keys = [key for key in required_keys if key not in flight_price_data]
            
            if missing_keys:
                logger.warning(f"[DEBUG] Missing required keys for FlightPriceTransformer: {missing_keys}")
                logger.info(f"[DEBUG] Available keys in flight_price_data: {list(flight_price_data.keys()) if isinstance(flight_price_data, dict) else 'Not a dict'}")
                
                # Check if DataLists exists but with different structure
                if 'DataLists' in flight_price_data:
                    data_lists = flight_price_data['DataLists']
                    logger.info(f"[DEBUG] DataLists keys: {list(data_lists.keys()) if isinstance(data_lists, dict) else 'Not a dict'}")
                    
                    # Check for FlightSegmentList
                    if 'FlightSegmentList' not in data_lists:
                        logger.warning(f"[DEBUG] FlightSegmentList missing from DataLists")
                
                # For now, skip transformation if required structure is missing
                raise ValueError(f"FlightPrice response missing required structure. Missing keys: {missing_keys}")
            
            # Use FlightPriceTransformer to transform the response
            transformer = FlightPriceTransformer(flight_price_data)
            transformed_offers = transformer.transform()
            
            logger.info(f"Successfully transformed FlightPrice response with {len(transformed_offers)} offers")
            
            # Cache the raw flight price response for order creation
            from utils.cache_manager import cache_manager
            
            # Generate cache key for flight price response
            flight_price_cache_key = f"flight_price_response:{request_id or 'unknown'}"
            
            # Store the complete raw response in cache for 30 minutes
            cache_manager.set(flight_price_cache_key, response, ttl=1800)
            logger.info(f"Stored flight price response in cache with key: {flight_price_cache_key}")
            
            # Cache the response using the primary cache key only
            
            # Return in a format compatible with frontend expectations
            result = {
                'priced_offers': transformed_offers,
                'total_offers': len(transformed_offers),
                'raw_response': response,  # Keep raw response for debugging
                'transformation_status': 'success',
                'metadata': {
                    'cache_key': flight_price_cache_key,
                    'cached': True,
                    'request_id': request_id
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error transforming FlightPrice response: {str(e)}", exc_info=True)
            
            # Cache the raw flight price response even when transformation fails
            from utils.cache_manager import cache_manager
            
            # Generate cache key for flight price response
            flight_price_cache_key = f"flight_price_response:{request_id or 'unknown'}"
            
            # Store the complete raw response in cache for 30 minutes
            cache_manager.set(flight_price_cache_key, response, ttl=1800)
            logger.info(f"Stored flight price response in cache with key: {flight_price_cache_key}")
            
            # Try to extract basic offer information for fallback
            basic_offers = []
            try:
                # Check if response contains FlightPriceRS
                if 'FlightPriceRS' in response:
                    flight_price_data = response['FlightPriceRS']
                else:
                    flight_price_data = response
                
                # Try to extract basic pricing information
                if 'PricedFlightOffers' in flight_price_data:
                    priced_offers = flight_price_data['PricedFlightOffers'].get('PricedFlightOffer', [])
                    for offer in priced_offers:
                        basic_offer = {
                            'offer_id': offer.get('OfferID', {}).get('value', 'unknown'),
                            'raw_offer': offer
                        }
                        basic_offers.append(basic_offer)
                    logger.info(f"Extracted {len(basic_offers)} basic offers as fallback")
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {str(fallback_error)}")
            
            # Determine error type and provide appropriate response
            error_type = 'processing_error'
            if 'FlightPrice API returned errors:' in str(e):
                error_type = 'api_error'
                logger.error(f"FlightPrice API error: {str(e)}")
            elif 'missing required structure' in str(e):
                error_type = 'structure_error'
                logger.error(f"FlightPrice response structure error: {str(e)}")
            
            # Try to extract basic offer information for fallback (only if not an API error)
            if error_type != 'api_error':
                try:
                    # Check if response contains FlightPriceRS
                    if 'FlightPriceRS' in response:
                        flight_price_data = response['FlightPriceRS']
                    else:
                        flight_price_data = response
                    
                    # Try to extract basic pricing information
                    if 'PricedFlightOffers' in flight_price_data:
                        priced_offers = flight_price_data['PricedFlightOffers'].get('PricedFlightOffer', [])
                        for offer in priced_offers:
                            basic_offer = {
                                'offer_id': offer.get('OfferID', {}).get('value', 'unknown'),
                                'raw_offer': offer
                            }
                            basic_offers.append(basic_offer)
                        logger.info(f"Extracted {len(basic_offers)} basic offers as fallback")
                except Exception as fallback_error:
                    logger.error(f"Fallback processing also failed: {str(fallback_error)}")
            
            # Return appropriate error response
            return {
                'priced_offers': basic_offers,
                'total_offers': len(basic_offers),
                'raw_response': response,
                'transformation_status': 'failed',
                'transformation_error': str(e),
                'error_type': error_type,
                'cache_key': flight_price_cache_key
            }


# Helper functions for backward compatibility
async def get_flight_price(
    airshopping_response: Dict[str, Any],
    offer_id: str,
    shopping_response_id: str,
    currency: str = "USD",
    request_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> PricingResponse:
    """
    Get price for a specific flight offer.
    
    This is a backward-compatible wrapper around the FlightPricingService.
    """
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightPricingService(config=config or {})
    try:
        return await service.get_flight_price(
            airshopping_response=airshopping_response,
            offer_id=offer_id,
            shopping_response_id=shopping_response_id,
            currency=currency,
            request_id=request_id
        )
    finally:
        await service.close()


async def process_flight_price(price_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process flight price request.
    
    This is a backward-compatible wrapper around the FlightPricingService.
    """
    config = price_request.pop('config', {})
    
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightPricingService(config=config)
    try:
        return await service.get_flight_price(
            airshopping_response=price_request.get('air_shopping_response', {}),
            offer_id=price_request.get('offer_id', ''),
            shopping_response_id=price_request.get('shopping_response_id', ''),
            currency=price_request.get('currency', 'USD'),
            request_id=price_request.get('request_id')
        )
    finally:
        await service.close()
