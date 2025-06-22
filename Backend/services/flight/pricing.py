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
            logger.info(f"[DEBUG] Starting airline code extraction for offer_id: {offer_id}")
            
            # Log the full response structure for debugging
            logger.debug(f"[DEBUG] Full airshopping_response keys: {list(airshopping_response.keys())}")
            
            # Handle both wrapped and unwrapped response formats
            if 'AirShoppingRS' in airshopping_response:
                logger.debug("[DEBUG] Found AirShoppingRS wrapper")
                offers_group = airshopping_response['AirShoppingRS'].get('OffersGroup', {})
            else:
                logger.debug("[DEBUG] No AirShoppingRS wrapper found, using response directly")
                offers_group = airshopping_response.get('OffersGroup', {})
            
            logger.debug(f"[DEBUG] OffersGroup keys: {list(offers_group.keys())}")
            
            # Look for the specific offer
            air_line_offers = offers_group.get('AirlineOffers', [])
            if not isinstance(air_line_offers, list):
                air_line_offers = [air_line_offers]
            
            logger.info(f"[DEBUG] Found {len(air_line_offers)} AirlineOffers entries")
            
            # First pass: Look for exact offer match
            for i, airline_offer in enumerate(air_line_offers):
                logger.debug(f"[DEBUG] Processing AirlineOffers[{i}] with keys: {list(airline_offer.keys())}")
                
                # The structure is AirlineOffers -> AirlineOffer (not 'Offer')
                offers = airline_offer.get('AirlineOffer', [])
                if not isinstance(offers, list):
                    offers = [offers]
                
                logger.info(f"[DEBUG] Found {len(offers)} offers in AirlineOffers[{i}].AirlineOffer")
                
                for j, offer in enumerate(offers):
                    logger.debug(f"[DEBUG] Processing offer {j} with keys: {list(offer.keys())}")
                    
                    # Extract OfferID value properly
                    offer_id_obj = offer.get('OfferID', {})
                    current_offer_id = offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj
                    
                    logger.debug(f"[DEBUG] Comparing offer_id: {offer_id} with current_offer_id: {current_offer_id}")
                    
                    if current_offer_id == offer_id:
                        logger.info(f"[DEBUG] Found matching offer at AirlineOffers[{i}].AirlineOffer[{j}]")
                        
                        # Try multiple paths for airline code extraction
                        # 1. From Owner at airline_offer level
                        owner = airline_offer.get('Owner', {})
                        if isinstance(owner, dict):
                            airline_code = owner.get('value')
                            if airline_code:
                                logger.info(f"[DEBUG] Found airline code '{airline_code}' for offer {offer_id} from Owner")
                                return airline_code
                        
                        # 2. From ValidatingCarrier in the offer
                        validating_carrier = offer.get('ValidatingCarrier', {})
                        if isinstance(validating_carrier, dict):
                            airline_code = validating_carrier.get('value')
                            if airline_code:
                                logger.info(f"[DEBUG] Found airline code '{airline_code}' for offer {offer_id} from ValidatingCarrier")
                                return airline_code
                        
                        # 3. From FlightSegments if available
                        flight_segments = offer.get('FlightSegments', [])
                        if isinstance(flight_segments, list) and flight_segments:
                            for k, segment in enumerate(flight_segments):
                                logger.debug(f"[DEBUG] Processing FlightSegment {k} with keys: {list(segment.keys())}")
                                operating_carrier = segment.get('OperatingCarrier', {})
                                if isinstance(operating_carrier, dict):
                                    airline_code = operating_carrier.get('value')
                                    if airline_code:
                                        logger.info(f"[DEBUG] Found airline code '{airline_code}' for offer {offer_id} from FlightSegments[{k}].OperatingCarrier")
                                        return airline_code
                        
                        # 4. From MarketingCarrier if available
                        if isinstance(flight_segments, list) and flight_segments:
                            for k, segment in enumerate(flight_segments):
                                marketing_carrier = segment.get('MarketingCarrier', {})
                                if isinstance(marketing_carrier, dict):
                                    airline_code = marketing_carrier.get('value')
                                    if airline_code:
                                        logger.info(f"[DEBUG] Found airline code '{airline_code}' for offer {offer_id} from FlightSegments[{k}].MarketingCarrier")
                                        return airline_code
            
            # If we reach here, the specific offer was not found
            logger.warning(f"[DEBUG] Could not find offer {offer_id} in AirShopping response")
            
            # Log all offer IDs for debugging
            all_offer_ids = []
            for airline_offer in air_line_offers:
                offers = airline_offer.get('AirlineOffer', [])
                if not isinstance(offers, list):
                    offers = [offers]
                for offer in offers:
                    offer_id_obj = offer.get('OfferID', {})
                    current_offer_id = offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj
                    all_offer_ids.append(current_offer_id)
            
            logger.warning(f"[DEBUG] Available offer IDs in response: {all_offer_ids}")
            
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
            logger.info(f"[DEBUG] Starting to build pricing payload for offer_id: {offer_id}")
            
            # Log the incoming airshopping_response structure
            logger.debug(f"[DEBUG] Incoming airshopping_response keys: {list(airshopping_response.keys())}")
            
            # Initialize variables
            original_response = None
            data = None
            selected_offer_index = 0
            offer_found = False
            
            # Check if we have the transformed frontend format with nested data
            if 'data' in airshopping_response and isinstance(airshopping_response['data'], dict):
                logger.info("[DEBUG] Found nested data structure in air shopping response")
                data = airshopping_response['data']
                
                # Check if we have the raw response in the data
                if 'raw_response' in data:
                    logger.info("[DEBUG] Using raw_response from nested data")
                    original_response = data['raw_response']
                elif 'data' in data and 'raw_response' in data['data']:
                    logger.info("[DEBUG] Using deeply nested raw_response")
                    original_response = data['data']['raw_response']
                else:
                    logger.info("[DEBUG] No raw_response found, using data directly")
                    original_response = data
            else:
                logger.info("[DEBUG] Using airshopping_response directly")
                original_response = airshopping_response
            
            # Log the structure of the response for debugging
            logger.debug(f"[DEBUG] Original response keys: {list(original_response.keys())}")
            
            # Handle both wrapped and unwrapped response formats
            if 'AirShoppingRS' in original_response:
                logger.info("[DEBUG] Found AirShoppingRS wrapper, unwrapping data")
                air_shopping_data = original_response['AirShoppingRS']
                offers_group = air_shopping_data.get('OffersGroup', {})
                unwrapped_response = air_shopping_data
            else:
                logger.info("[DEBUG] No AirShoppingRS wrapper found, using data directly")
                offers_group = original_response.get('OffersGroup', {})
                unwrapped_response = original_response
            
            # Log the structure of the response for debugging
            logger.debug(f"[DEBUG] OffersGroup keys: {list(offers_group.keys())}")
            
            # Validate that we have the expected data structure
            airline_offers_list = offers_group.get('AirlineOffers', [])
            if not isinstance(airline_offers_list, list):
                airline_offers_list = [airline_offers_list]
            
            if not airline_offers_list:
                # Try to find airline offers in other possible locations
                if 'offers' in original_response:
                    logger.info("[DEBUG] Found 'offers' key, using it as AirlineOffers")
                    airline_offers_list = [{'AirlineOffer': original_response['offers']}]
                else:
                    error_msg = f"No AirlineOffers found in the response data. Top-level keys: {list(original_response.keys())}"
                    logger.error(f"[DEBUG] {error_msg}")
                    raise ValueError("No AirlineOffers found in the response data")
            
            logger.info(f"[DEBUG] Found {len(airline_offers_list)} AirlineOffers entries")
            
            # Find the matching offer index
            for airline_offers_entry in airline_offers_list:
                if not isinstance(airline_offers_entry, dict):
                    continue
                    
                # Support both AirlineOffer and offers keys for flexibility
                airline_offers = airline_offers_entry.get('AirlineOffer', airline_offers_entry.get('offers', []))
                if not isinstance(airline_offers, list):
                    airline_offers = [airline_offers]
                
                logger.info(f"[DEBUG] Processing {len(airline_offers)} offers in AirlineOffers entry")
                
                for i, offer in enumerate(airline_offers):
                    if not isinstance(offer, dict):
                        continue
                        
                    # Try multiple ways to get the offer ID
                    current_offer_id = None
                    
                    # Check direct ID first (frontend format)
                    if 'id' in offer:
                        current_offer_id = str(offer['id'])
                    # Then check OfferID object (NDC format)
                    elif 'OfferID' in offer:
                        offer_id_obj = offer['OfferID']
                        current_offer_id = str(offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj)
                    
                    if not current_offer_id:
                        logger.debug(f"[DEBUG] Skipping offer {i} - no valid ID found")
                        continue
                    
                    logger.debug(f"[DEBUG] Checking offer {i}: {current_offer_id} (looking for: {offer_id})")
                    
                    # Check for exact match or match without _return suffix for round-trip
                    if (str(current_offer_id) == str(offer_id) or 
                        (offer_id.endswith('_return') and 
                         str(current_offer_id) == str(offer_id[:-7]))):  # Remove '_return' suffix
                        selected_offer_index = i
                        offer_found = True
                        logger.info(f"[DEBUG] Found matching offer at index {i} for offer_id: {offer_id}")
                        break
                
                if offer_found:
                    break
            
            if not offer_found:
                # Log all available offer IDs for debugging
                all_offer_ids = []
                for entry in airline_offers_list:
                    if not isinstance(entry, dict):
                        continue
                        
                    offers = entry.get('AirlineOffer', entry.get('offers', []))
                    if not isinstance(offers, list):
                        offers = [offers]
                    
                    for offer in offers:
                        if not isinstance(offer, dict):
                            continue
                            
                        # Try to extract offer ID from different possible locations
                        if 'id' in offer:
                            all_offer_ids.append(str(offer['id']))
                        elif 'OfferID' in offer:
                            offer_id_obj = offer['OfferID']
                            current_id = offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj
                            if current_id:
                                all_offer_ids.append(str(current_id))
                
                # If we have a _return suffix, try without it for better error message
                base_offer_id = offer_id[:-7] if offer_id.endswith('_return') else None
                
                error_msg = f"Offer ID {offer_id} not found in response. "
                if base_offer_id:
                    error_msg += f"Tried both {offer_id} and {base_offer_id}. "
                error_msg += f"Available offer IDs: {all_offer_ids}"
                
                logger.error(f"[DEBUG] {error_msg}")
                raise ValueError(f"Offer ID {offer_id} not found in response")
            
            # Use the request builder to create the payload with unwrapped data
            logger.info(f"[DEBUG] Building FlightPrice payload for offer {offer_id} at index {selected_offer_index}")
            payload = build_flight_price_request(
                airshopping_response=unwrapped_response,
                selected_offer_index=selected_offer_index
            )
            
            logger.info("[DEBUG] Successfully built FlightPrice payload")
            return payload
            
        except Exception as e:
            logger.error(f"[ERROR] Error building FlightPrice payload: {str(e)}", exc_info=True)
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
