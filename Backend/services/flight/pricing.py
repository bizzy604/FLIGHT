"""
Flight Pricing Module

This module handles flight pricing operations using the Verteil NDC API.
"""
import json
import logging
from typing import Dict, Any, Optional, List
import uuid
import sys
import os

# Import the flight price transformer and request builder from their respective packages
from utils.flight_price_transformer import transform_for_frontend
from scripts.build_flightprice_rq import build_flight_price_request

# Import service components
from services.flight.core import FlightService
from services.flight.decorators import async_cache, async_rate_limited
from services.flight.exceptions import FlightServiceError, ValidationError
from services.flight.types import PricingResponse, SearchCriteria

# Import Phase 1 core infrastructure for multi-airline support
from utils.multi_airline_detector import MultiAirlineDetector
from utils.reference_extractor import EnhancedReferenceExtractor

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
    ) -> Dict[str, Any]:
        """
        Get pricing for a specific flight offer.
        
        Args:
            airshopping_response: The AirShopping response
            offer_id: The ID of the offer to price (frontend's offer ID)
            shopping_response_id: The ShoppingResponseID from AirShoppingRS
            currency: Currency code (default: USD)
            request_id: Optional request ID for tracking
            
        Returns:
            PricingResponse containing price details or error information
            
        Raises:
            ValidationError: If the request data is invalid
            APIError: If there's an error communicating with the API
        """
        logger.info(f"[INFO] Starting flight price request for offer ID: {offer_id}")
        
        try:
            # Validate input
            if not airshopping_response or not offer_id:
                raise ValidationError("Missing required parameters for flight pricing")

            # Allow frontend to pass placeholder for shopping_response_id in multi-airline scenarios
            if not shopping_response_id or shopping_response_id == 'BACKEND_WILL_EXTRACT':
                logger.info("Frontend requested backend to extract ShoppingResponseID from multi-airline response")
            
            # Generate a request ID if not provided
            request_id = request_id or str(uuid.uuid4())
            
            # Debug: Log the structure of the air shopping response
            logger.info(f"[DEBUG] Air shopping response keys: {list(airshopping_response.keys())}")
            if 'DataLists' in airshopping_response:
                data_lists = airshopping_response['DataLists']
                logger.info(f"[DEBUG] DataLists keys: {list(data_lists.keys())}")
                if 'AnonymousTravelerList' in data_lists:
                    travelers = data_lists['AnonymousTravelerList']
                    if isinstance(travelers, dict) and 'AnonymousTraveler' in travelers:
                        traveler_list = travelers['AnonymousTraveler']
                        if isinstance(traveler_list, list) and len(traveler_list) > 0:
                            first_traveler = traveler_list[0]
                            logger.info(f"[DEBUG] First traveler ObjectKey: {first_traveler.get('ObjectKey', 'N/A')}")

            # Extract airline code from the offer
            airline_code = self._extract_airline_code_from_offer(airshopping_response, offer_id)
            logger.info(f"Extracted airline code '{airline_code}' for offer {offer_id} (ReqID: {request_id})")

            # Get airline-specific ShoppingResponseID for multi-airline support
            if airline_code:
                airline_shopping_response_id = self._get_shopping_response_id_for_airline(airshopping_response, airline_code)
                if airline_shopping_response_id:
                    # Use airline-specific ShoppingResponseID if available
                    shopping_response_id = airline_shopping_response_id
                    logger.info(f"Using airline-specific ShoppingResponseID for {airline_code}: {shopping_response_id}")
                elif shopping_response_id == 'BACKEND_WILL_EXTRACT':
                    # Frontend requested backend extraction but we couldn't find airline-specific ID
                    raise ValidationError(f"Could not extract airline-specific ShoppingResponseID for airline {airline_code}")
                else:
                    logger.info(f"Using provided ShoppingResponseID: {shopping_response_id}")
            elif shopping_response_id == 'BACKEND_WILL_EXTRACT':
                # Frontend requested backend extraction but we couldn't determine airline
                raise ValidationError("Could not determine airline code for ShoppingResponseID extraction")

            # [PASSENGER DEBUG] Log passenger data from air shopping response
            if 'DataLists' in airshopping_response and 'AnonymousTravelerList' in airshopping_response['DataLists']:
                traveler_list = airshopping_response['DataLists']['AnonymousTravelerList']
                logger.info(f"[PASSENGER DEBUG] Flight Pricing Service - Input AnonymousTravelerList count: {len(traveler_list) if isinstance(traveler_list, list) else 1}")

            # Build the pricing payload
            pricing_payload = self._build_pricing_payload(
                airshopping_response=airshopping_response,
                offer_id=offer_id
            )

            # [PASSENGER DEBUG] Log passenger data in pricing payload
            if 'DataLists' in pricing_payload and 'AnonymousTravelerList' in pricing_payload['DataLists']:
                payload_travelers = pricing_payload['DataLists']['AnonymousTravelerList']
                logger.info(f"[PASSENGER DEBUG] Flight Pricing Service - Payload AnonymousTravelerList count: {len(payload_travelers) if isinstance(payload_travelers, list) else 1}")

            if 'Travelers' in pricing_payload and 'Traveler' in pricing_payload['Travelers']:
                payload_travelers_section = pricing_payload['Travelers']['Traveler']
                logger.info(f"[PASSENGER DEBUG] Flight Pricing Service - Payload Travelers count: {len(payload_travelers_section) if isinstance(payload_travelers_section, list) else 1}")

            # Log the request details
            logger.info(f"[INFO] Sending FlightPrice request for offer ID: {offer_id}")
            logger.debug(f"[DEBUG] FlightPrice request payload: {pricing_payload}")
            
            # Make the API request
            response = await self._make_request(
                endpoint='/entrygate/rest/request:flightPrice',
                payload=pricing_payload,
                service_name='FlightPrice',
                airline_code=airline_code,
                request_id=request_id
            )

            # [PASSENGER DEBUG] Log passenger data in flight price response
            if response and 'DataLists' in response and 'AnonymousTravelerList' in response['DataLists']:
                response_travelers = response['DataLists']['AnonymousTravelerList']
                logger.info(f"[PASSENGER DEBUG] Flight Price API Response - AnonymousTravelerList count: {len(response_travelers) if isinstance(response_travelers, list) else 1}")

            # Process the response, passing the frontend's offer_id to ensure consistency
            return {
                'status': 'success',
                'data': self._process_pricing_response(
                    response=response,
                    request_id=request_id,
                    frontend_offer_id=offer_id  # Pass the frontend's offer ID to maintain consistency
                ),
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
        Enhanced airline code extraction with multi-airline support.

        Args:
            airshopping_response: The AirShopping response containing offers
            offer_id: The ID of the offer to extract airline code from (can be index for multi-airline)

        Returns:
            The airline code (e.g., 'KQ', 'WY') or None if not found
        """
        try:
            logger.info(f"Starting enhanced airline code extraction for offer_id: {offer_id}")

            # Detect response type
            is_multi_airline = MultiAirlineDetector.is_multi_airline_response(airshopping_response)

            if is_multi_airline:
                return self._extract_airline_from_multi_airline_offer(airshopping_response, offer_id)
            else:
                return self._extract_airline_from_single_airline_offer(airshopping_response, offer_id)

        except Exception as e:
            logger.error(f"Error extracting airline code for offer {offer_id}: {str(e)}", exc_info=True)
            return None

    def _extract_airline_from_multi_airline_offer(self, airshopping_response: Dict[str, Any], offer_id: str) -> Optional[str]:
        """
        Extract airline code from multi-airline response using offer index.

        Args:
            airshopping_response: The multi-airline AirShopping response
            offer_id: The offer index (as string) from frontend

        Returns:
            The airline code or None if not found
        """
        try:
            # Convert offer_id (index) to integer
            offer_index = int(offer_id)
            logger.info(f"Extracting airline code from multi-airline offer at index {offer_index}")

            # Recreate the flattened offers array (matching transformer logic)
            offers_group = airshopping_response.get('OffersGroup', {})
            airline_offers_list = offers_group.get('AirlineOffers', [])

            logger.info(f"[DEBUG] OffersGroup keys: {list(offers_group.keys())}")
            logger.info(f"[DEBUG] AirlineOffers type: {type(airline_offers_list)}, length: {len(airline_offers_list) if isinstance(airline_offers_list, list) else 'N/A'}")

            all_offers = []
            for i, airline_offer_group in enumerate(airline_offers_list):
                logger.info(f"[DEBUG] AirlineOffer group {i} keys: {list(airline_offer_group.keys()) if isinstance(airline_offer_group, dict) else 'Not a dict'}")
                airline_offers = airline_offer_group.get('AirlineOffer', [])
                logger.info(f"[DEBUG] AirlineOffer group {i} has {len(airline_offers) if isinstance(airline_offers, list) else 'N/A'} offers")

                for j, offer in enumerate(airline_offers):
                    if offer.get('PricedOffer'):
                        all_offers.append(offer)
                        if j < 3:  # Log first 3 offers
                            offer_id_info = offer.get('OfferID', {})
                            logger.info(f"[DEBUG] Offer {len(all_offers)-1}: OfferID Owner = {offer_id_info.get('Owner', 'N/A')}")

            # Get the offer at the specified index
            logger.info(f"[DEBUG] Total offers found: {len(all_offers)}, requested index: {offer_index}")

            if 0 <= offer_index < len(all_offers):
                selected_offer = all_offers[offer_index]
                offer_id_data = selected_offer.get('OfferID', {})
                airline_code = offer_id_data.get('Owner')

                logger.info(f"[DEBUG] Selected offer OfferID structure: {offer_id_data}")
                logger.info(f"[DEBUG] Extracted airline code: {airline_code}")

                if airline_code:
                    logger.info(f"Extracted airline code '{airline_code}' from multi-airline offer index {offer_index}")
                    return airline_code
                else:
                    logger.warning(f"No Owner found in OfferID for multi-airline offer index {offer_index}")
                    return None
            else:
                logger.error(f"Multi-airline offer index {offer_index} out of range (total offers: {len(all_offers)})")
                return None

        except (ValueError, TypeError) as e:
            logger.error(f"Invalid offer_id format for multi-airline: {offer_id}, error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting airline code from multi-airline offer: {e}")
            return None

    def _extract_airline_from_single_airline_offer(self, airshopping_response: Dict[str, Any], offer_id: str) -> Optional[str]:
        """
        Extract airline code from single-airline response (legacy logic).

        Args:
            airshopping_response: The single-airline AirShopping response
            offer_id: The offer ID to search for

        Returns:
            The airline code or None if not found
        """
        try:
            logger.info(f"Extracting airline code from single-airline offer: {offer_id}")

            # Handle both wrapped and unwrapped response formats
            if 'AirShoppingRS' in airshopping_response:
                offers_group = airshopping_response['AirShoppingRS'].get('OffersGroup', {})
            else:
                offers_group = airshopping_response.get('OffersGroup', {})

            # Look for the specific offer
            air_line_offers = offers_group.get('AirlineOffers', [])
            if not isinstance(air_line_offers, list):
                air_line_offers = [air_line_offers]

            # Search for exact offer match
            for i, airline_offer in enumerate(air_line_offers):
                offers = airline_offer.get('AirlineOffer', [])
                if not isinstance(offers, list):
                    offers = [offers]

                for j, offer in enumerate(offers):
                    # Extract OfferID value properly
                    offer_id_obj = offer.get('OfferID', {})
                    current_offer_id = offer_id_obj.get('value', '') if isinstance(offer_id_obj, dict) else offer_id_obj

                    if current_offer_id == offer_id:
                        logger.info(f"Found matching single-airline offer at AirlineOffers[{i}].AirlineOffer[{j}]")

                        # Try multiple paths for airline code extraction
                        # 1. From Owner at airline_offer level
                        owner = airline_offer.get('Owner', {})
                        if isinstance(owner, dict):
                            airline_code = owner.get('value')
                            if airline_code:
                                logger.info(f"Found airline code '{airline_code}' from Owner")
                                return airline_code

                        # 2. From ValidatingCarrier in the offer
                        validating_carrier = offer.get('ValidatingCarrier', {})
                        if isinstance(validating_carrier, dict):
                            airline_code = validating_carrier.get('value')
                            if airline_code:
                                logger.info(f"Found airline code '{airline_code}' from ValidatingCarrier")
                                return airline_code

                        # 3. From FlightSegments if available
                        flight_segments = offer.get('FlightSegments', [])
                        if isinstance(flight_segments, list) and flight_segments:
                            for segment in flight_segments:
                                operating_carrier = segment.get('OperatingCarrier', {})
                                if isinstance(operating_carrier, dict):
                                    airline_code = operating_carrier.get('value')
                                    if airline_code:
                                        logger.info(f"Found airline code '{airline_code}' from OperatingCarrier")
                                        return airline_code

            logger.warning(f"Could not find single-airline offer {offer_id} in AirShopping response")
            return None

        except Exception as e:
            logger.error(f"Error extracting airline code from single-airline offer: {e}")
            return None

    def _get_shopping_response_id_for_airline(self, airshopping_response: Dict[str, Any], airline_code: str) -> Optional[str]:
        """
        Get the airline-specific ShoppingResponseID for multi-airline responses.

        Args:
            airshopping_response: The AirShopping response
            airline_code: The airline code to get ShoppingResponseID for

        Returns:
            The airline-specific ShoppingResponseID or None if not found
        """
        try:
            logger.info(f"Getting ShoppingResponseID for airline: {airline_code}")

            # Check if this is a multi-airline response
            is_multi_airline = MultiAirlineDetector.is_multi_airline_response(airshopping_response)

            if is_multi_airline:
                # Use the enhanced reference extractor to get airline-specific ShoppingResponseIDs
                extractor = EnhancedReferenceExtractor(airshopping_response)
                refs = extractor.extract_references()

                shopping_ids = refs.get('shopping_response_ids', {})
                airline_shopping_id = shopping_ids.get(airline_code)

                if airline_shopping_id:
                    logger.info(f"Found airline-specific ShoppingResponseID for {airline_code}: {airline_shopping_id}")
                    return airline_shopping_id
                else:
                    logger.warning(f"No ShoppingResponseID found for airline {airline_code}")
                    # Fallback to first available ShoppingResponseID
                    if shopping_ids:
                        fallback_id = next(iter(shopping_ids.values()))
                        logger.info(f"Using fallback ShoppingResponseID: {fallback_id}")
                        return fallback_id
                    return None
            else:
                # For single-airline responses, use the standard ShoppingResponseID
                shopping_response = airshopping_response.get('ShoppingResponse', {})
                shopping_response_id = shopping_response.get('ShoppingResponseID', {}).get('value')

                if shopping_response_id:
                    logger.info(f"Found single-airline ShoppingResponseID: {shopping_response_id}")
                    return shopping_response_id
                else:
                    logger.warning("No ShoppingResponseID found in single-airline response")
                    return None

        except Exception as e:
            logger.error(f"Error getting ShoppingResponseID for airline {airline_code}: {e}")
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
            offer_id: The ID of the offer to price (can be index or OfferID)

        Returns:
            Dictionary containing the request payload
        """
        try:
            logger.info(f"[DEBUG] Starting to build pricing payload for offer_id: {offer_id}")

            # Check if offer_id is a numeric index (new approach) or OfferID (legacy approach)
            is_index_based = offer_id.isdigit()

            if is_index_based:
                logger.info(f"[DEBUG] Using index-based approach with index: {offer_id}")
                selected_offer_index = int(offer_id)
            else:
                logger.info(f"[DEBUG] Using legacy OfferID approach with ID: {offer_id}")

            # Log the incoming airshopping_response structure
            logger.debug(f"[DEBUG] Incoming airshopping_response keys: {list(airshopping_response.keys())}")

            # Initialize variables
            original_response = None
            data = None

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
                unwrapped_response = air_shopping_data
            else:
                logger.info("[DEBUG] No AirShoppingRS wrapper found, using data directly")
                unwrapped_response = original_response

            if is_index_based:
                # NEW INDEX-BASED APPROACH: Map display index to original index
                display_index = selected_offer_index
                logger.info(f"[DEBUG] Using index-based approach: display index {display_index}")

                # Try to get transformed offers to map display index to original index
                transformed_offers = None

                # Check if we have the complete backend response structure
                if 'offers' in airshopping_response:
                    transformed_offers = airshopping_response['offers']
                elif 'data' in airshopping_response and isinstance(airshopping_response['data'], dict):
                    data_section = airshopping_response['data']
                    if 'offers' in data_section:
                        transformed_offers = data_section['offers']
                    elif 'data' in data_section and 'offers' in data_section['data']:
                        transformed_offers = data_section['data']['offers']
                else:
                    # If we don't have transformed offers, recreate them to get the mapping
                    try:
                        from transformers.enhanced_air_shopping_transformer import transform_air_shopping_for_results_enhanced
                        transformed_result = transform_air_shopping_for_results_enhanced(unwrapped_response)
                        transformed_offers = transformed_result.get('offers', [])
                        logger.info(f"Recreated {len(transformed_offers)} transformed offers for index mapping")
                    except Exception as e:
                        logger.warning(f"Failed to recreate transformed offers: {e}")
                        transformed_offers = None

                if transformed_offers and isinstance(transformed_offers, list):
                    # Map display index to original index using transformed offers
                    if 0 <= display_index < len(transformed_offers):
                        selected_offer = transformed_offers[display_index]
                        original_index = selected_offer.get('original_index')
                        if original_index is not None:
                            selected_offer_index = original_index
                            logger.info(f"Mapped display index {display_index} to original index {selected_offer_index}")
                        else:
                            logger.warning(f"No original_index found in offer at display index {display_index}, using display index")
                            selected_offer_index = display_index
                    else:
                        raise ValueError(f"Display index {display_index} is out of bounds. Total transformed offers: {len(transformed_offers)}")
                else:
                    logger.warning("No transformed offers found, using display index as original index")
                    selected_offer_index = display_index

                # Validate that the original index is within bounds of raw response
                offers_group = unwrapped_response.get('OffersGroup', {})
                airline_offers_list = offers_group.get('AirlineOffers', [])
                if not isinstance(airline_offers_list, list):
                    airline_offers_list = [airline_offers_list]

                # Count total offers to validate original index
                total_offers = 0
                for airline_offers_entry in airline_offers_list:
                    if isinstance(airline_offers_entry, dict):
                        airline_offers = airline_offers_entry.get('AirlineOffer', [])
                        if not isinstance(airline_offers, list):
                            airline_offers = [airline_offers]
                        total_offers += len(airline_offers)

                if selected_offer_index >= total_offers:
                    raise ValueError(f"Original index {selected_offer_index} is out of bounds. Total offers in raw response: {total_offers}")

                logger.info(f"[DEBUG] Original index {selected_offer_index} is valid (total offers: {total_offers})")

            else:
                # LEGACY OFFERID-BASED APPROACH: Keep the complex mapping for backward compatibility
                logger.info(f"[DEBUG] Using legacy OfferID approach for: {offer_id}")

                # Re-transform the raw response to create OfferID mapping
                from utils.air_shopping_transformer import transform_air_shopping_for_results
                transformed_data = transform_air_shopping_for_results(original_response)

                # Build mapping from original OfferIDs to their indices
                offers_group = unwrapped_response.get('OffersGroup', {})
                airline_offers_list = offers_group.get('AirlineOffers', [])
                if not isinstance(airline_offers_list, list):
                    airline_offers_list = [airline_offers_list]

                original_offer_mapping = {}
                all_original_ids = []
                offer_index = 0

                for airline_offers_entry in airline_offers_list:
                    if not isinstance(airline_offers_entry, dict):
                        continue

                    airline_offers = airline_offers_entry.get('AirlineOffer', [])
                    if not isinstance(airline_offers, list):
                        airline_offers = [airline_offers]

                    for offer in airline_offers:
                        if not isinstance(offer, dict):
                            continue

                        # Extract original OfferID from NDC format
                        original_offer_id = None
                        if 'OfferID' in offer:
                            offer_id_obj = offer['OfferID']
                            if isinstance(offer_id_obj, dict):
                                original_offer_id = offer_id_obj.get('value') or offer_id_obj.get('ObjectKey')
                            elif isinstance(offer_id_obj, str):
                                original_offer_id = offer_id_obj

                        if original_offer_id:
                            original_offer_mapping[original_offer_id] = offer_index
                            all_original_ids.append(original_offer_id)
                            logger.debug(f"[DEBUG] Mapped original offer ID {original_offer_id} to index {offer_index}")

                        offer_index += 1

                # Try to find the offer using different strategies
                offer_found = False
                if offer_id in original_offer_mapping:
                    selected_offer_index = original_offer_mapping[offer_id]
                    offer_found = True
                    logger.info(f"[DEBUG] Found direct match for offer_id: {offer_id} at index {selected_offer_index}")
                else:
                    # Suffix matching strategy
                    offer_suffix = offer_id.split('_', 1)[-1] if '_' in offer_id else offer_id
                    for original_id in all_original_ids:
                        original_suffix = original_id.split('_', 1)[-1] if '_' in original_id else original_id
                        if original_suffix == offer_suffix:
                            selected_offer_index = original_offer_mapping[original_id]
                            offer_found = True
                            logger.info(f"[DEBUG] Found suffix match: frontend {offer_id} matches original {original_id} at index {selected_offer_index}")
                            break

                if not offer_found:
                    error_msg = f"Offer ID {offer_id} not found in response. Available original offer IDs: {all_original_ids[:10]}..."
                    logger.error(f"[DEBUG] {error_msg}")
                    raise ValueError(f"Offer ID {offer_id} not found in response")
            
            # First, check if the offer has expired before building the payload
            self._validate_offer_expiration(unwrapped_response, selected_offer_index)

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

    def _validate_offer_expiration(self, airshopping_response: Dict[str, Any], selected_offer_index: int) -> None:
        """
        Validate that the selected offer has not expired.

        Args:
            airshopping_response: The raw AirShopping response
            selected_offer_index: Index of the selected offer

        Raises:
            ValidationError: If the offer has expired
        """
        try:
            from datetime import datetime, timezone

            # Navigate to the selected offer
            offers_group = airshopping_response.get("OffersGroup", {})
            airline_offers_list = offers_group.get("AirlineOffers", [])

            if not airline_offers_list or not isinstance(airline_offers_list, list):
                logger.warning("No AirlineOffers found for expiration validation")
                return

            # Get the first airline offers entry (default behavior)
            airline_offers_node = airline_offers_list[0]
            actual_offers = airline_offers_node.get("AirlineOffer", [])

            if selected_offer_index >= len(actual_offers):
                raise ValidationError(f"Selected offer index {selected_offer_index} is out of bounds")

            selected_offer = actual_offers[selected_offer_index]

            # Check TimeLimits for offer expiration
            time_limits = selected_offer.get("TimeLimits", {})
            offer_expiration = time_limits.get("OfferExpiration", {})
            expiration_datetime_str = offer_expiration.get("DateTime")

            if expiration_datetime_str:
                try:
                    # Parse the expiration datetime (assuming ISO format)
                    expiration_datetime = datetime.fromisoformat(expiration_datetime_str.replace('Z', '+00:00'))
                    current_datetime = datetime.now(timezone.utc)

                    # Ensure both datetimes are timezone-aware
                    if expiration_datetime.tzinfo is None:
                        expiration_datetime = expiration_datetime.replace(tzinfo=timezone.utc)

                    if current_datetime > expiration_datetime:
                        logger.error(f"Offer has expired. Expiration: {expiration_datetime_str}, Current: {current_datetime.isoformat()}")
                        raise ValidationError(f"This flight offer has expired at {expiration_datetime_str}. Please search for new flights.")
                    else:
                        time_remaining = expiration_datetime - current_datetime
                        logger.info(f"Offer is valid. Time remaining: {time_remaining}")

                except ValueError as e:
                    logger.warning(f"Could not parse offer expiration datetime '{expiration_datetime_str}': {e}")
            else:
                logger.info("No offer expiration time found, proceeding with pricing")

        except Exception as e:
            logger.error(f"Error validating offer expiration: {str(e)}")
            # Don't fail the request if we can't validate expiration, just log the error

    def _process_pricing_response(
        self, 
        response: Dict[str, Any], 
        request_id: Optional[str] = None,
        frontend_offer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process the FlightPrice API response using FlightPriceTransformer.
        
        Args:
            response: Raw API response from FlightPrice endpoint
            request_id: Request ID for caching purposes
            frontend_offer_id: The offer ID from the frontend to ensure consistency
            
        Returns:
            Transformed response data compatible with frontend
        """
        try:
            logger.info("Starting to process FlightPrice response")
            
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
            
            # Use transform_for_frontend to transform the response
            transformation_result = transform_for_frontend(flight_price_data)

            # Extract the offers array from the transformation result
            transformed_offers = transformation_result.get('offers', [])

            # If we have a frontend_offer_id, ensure it's used in the transformed offers
            if frontend_offer_id and transformed_offers:
                for offer in transformed_offers:
                    if 'offer_id' in offer:
                        offer['original_offer_id'] = offer['offer_id']
                        offer['offer_id'] = frontend_offer_id
            
            logger.info(f"Successfully transformed FlightPrice response with {len(transformed_offers)} offers")
            
            # Cache the raw flight price response for order creation
            from utils.cache_manager import cache_manager

            # Generate multiple cache keys for flight price response to ensure booking can find it
            cache_keys = [
                f"flight_price_response:{request_id or 'unknown'}",  # Primary key with request_id
            ]

            # Extract ShoppingResponseID and OfferID from response for additional cache keys
            try:
                shopping_response_id = None
                offer_id = None

                if response and 'ShoppingResponseID' in response:
                    shopping_response_id_node = response['ShoppingResponseID']
                    if isinstance(shopping_response_id_node, dict) and 'ResponseID' in shopping_response_id_node:
                        shopping_response_id = shopping_response_id_node['ResponseID'].get('value')

                if response and 'PricedFlightOffers' in response:
                    priced_offers = response['PricedFlightOffers']
                    if isinstance(priced_offers, dict) and 'PricedFlightOffer' in priced_offers:
                        priced_offer_list = priced_offers['PricedFlightOffer']
                        if isinstance(priced_offer_list, list) and len(priced_offer_list) > 0:
                            first_offer = priced_offer_list[0]
                            if 'OfferID' in first_offer:
                                offer_id_node = first_offer['OfferID']
                                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                                    offer_id = offer_id_node['value']

                # Add additional cache keys if we found the IDs
                if shopping_response_id:
                    cache_keys.append(f"flight_price_response:{shopping_response_id}")
                if offer_id:
                    cache_keys.append(f"flight_price_response:{offer_id}")

            except Exception as e:
                logger.warning(f"Could not extract IDs for additional cache keys: {str(e)}")

            # Store the complete raw response in cache for 30 minutes using all keys
            for cache_key in cache_keys:
                cache_manager.set(cache_key, response, ttl=1800)
                logger.info(f"Stored flight price response in cache with key: {cache_key}")
            
            # Cache the response using the primary cache key only
            
            # Return in a format compatible with frontend expectations
            result = {
                'priced_offers': transformed_offers,
                'total_offers': len(transformed_offers),
                'raw_response': response,  # Keep raw response for debugging
                'transformation_status': 'success',
                'metadata': {
                    'cache_key': cache_keys[0] if cache_keys else f"flight_price_response:{request_id or 'unknown'}",
                    'cached': True,
                    'request_id': request_id
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error transforming FlightPrice response: {str(e)}", exc_info=True)
            
            # Cache the raw flight price response even when transformation fails
            from utils.cache_manager import cache_manager

            # Generate multiple cache keys for flight price response to ensure booking can find it
            cache_keys = [
                f"flight_price_response:{request_id or 'unknown'}",  # Primary key with request_id
            ]

            # Extract ShoppingResponseID and OfferID from response for additional cache keys
            try:
                shopping_response_id = None
                offer_id = None

                if response and 'ShoppingResponseID' in response:
                    shopping_response_id_node = response['ShoppingResponseID']
                    if isinstance(shopping_response_id_node, dict) and 'ResponseID' in shopping_response_id_node:
                        shopping_response_id = shopping_response_id_node['ResponseID'].get('value')

                if response and 'PricedFlightOffers' in response:
                    priced_offers = response['PricedFlightOffers']
                    if isinstance(priced_offers, dict) and 'PricedFlightOffer' in priced_offers:
                        priced_offer_list = priced_offers['PricedFlightOffer']
                        if isinstance(priced_offer_list, list) and len(priced_offer_list) > 0:
                            first_offer = priced_offer_list[0]
                            if 'OfferID' in first_offer:
                                offer_id_node = first_offer['OfferID']
                                if isinstance(offer_id_node, dict) and 'value' in offer_id_node:
                                    offer_id = offer_id_node['value']

                # Add additional cache keys if we found the IDs
                if shopping_response_id:
                    cache_keys.append(f"flight_price_response:{shopping_response_id}")
                if offer_id:
                    cache_keys.append(f"flight_price_response:{offer_id}")

            except Exception as e:
                logger.warning(f"Could not extract IDs for additional cache keys: {str(e)}")

            # Store the complete raw response in cache for 30 minutes using all keys
            for cache_key in cache_keys:
                cache_manager.set(cache_key, response, ttl=1800)
                logger.info(f"Stored flight price response in cache with key: {cache_key}")
            
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
                'status': 'error',
                'data': {
                    'priced_offers': basic_offers,
                    'total_offers': len(basic_offers),
                    'raw_response': response,
                    'transformation_status': 'failed',
                    'transformation_error': str(e),
                    'error_type': error_type,
                    'cache_key': f"flight_price_response:{request_id or 'unknown'}"
                }
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
    
    Args:
        price_request: Dictionary containing:
            - air_shopping_response: The AirShopping response
            - offer_id: The frontend's offer ID (required)
            - shopping_response_id: The ShoppingResponseID from AirShoppingRS (required)
            - currency: Currency code (default: USD)
            - request_id: Optional request ID for tracking
            - config: Optional configuration overrides
    """
    config = price_request.pop('config', {})
    
    # Extract the offer_id from the request
    offer_id = price_request.get('offer_id', '')
    if not offer_id:
        raise ValueError("offer_id is required in price_request")
    
    # Log the request details
    logger.info(f"[INFO] Processing flight price request for offer ID: {offer_id}")
    
    # Use a single service instance to avoid creating multiple TokenManager instances
    service = FlightPricingService(config=config)
    try:
        # Pass the offer_id as the frontend_offer_id to maintain consistency
        return await service.get_flight_price(
            airshopping_response=price_request.get('air_shopping_response', {}),
            offer_id=offer_id,
            shopping_response_id=price_request.get('shopping_response_id', ''),
            currency=price_request.get('currency', 'USD'),
            request_id=price_request.get('request_id')
        )
    finally:
        await service.close()
