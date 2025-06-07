"""
Flight Pricing Module

This module handles flight pricing operations using the Verteil NDC API.
"""
import logging
from typing import Dict, Any, Optional, List
import uuid
import sys
import os

# Add the scripts directory to the path to import the request builder
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts'))
from build_flightprice_rq import build_flight_price_request

from .core import FlightService
from .decorators import async_cache, async_rate_limited
from .exceptions import FlightServiceError, ValidationError
from .types import PricingResponse, SearchCriteria

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
            
            # Build the request payload
            payload = self._build_pricing_payload(
                airshopping_response=airshopping_response,
                offer_id=offer_id,
                shopping_response_id=shopping_response_id,
                currency=currency,
                request_id=request_id
            )
            
            # Make the API request
            response = await self._make_request(
                endpoint='flightprice',
                payload=payload,
                service_name='FlightPrice',
                request_id=request_id
            )
            
            # Process and return the response
            return {
                'status': 'success',
                'data': self._process_pricing_response(response),
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
    
    def _build_pricing_payload(
        self,
        airshopping_response: Dict[str, Any],
        offer_id: str,
        shopping_response_id: str,
        currency: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Build the FlightPrice request payload using the request builder.
        
        Args:
            airshopping_response: The AirShopping response
            offer_id: The ID of the offer to price
            shopping_response_id: The ShoppingResponseID from AirShoppingRS
            currency: Currency code
            request_id: Request ID for tracking
            
        Returns:
            Dictionary containing the request payload
        """
        try:
            # Find the selected offer index based on offer_id
            selected_offer_index = 0
            offers_group = airshopping_response.get('OffersGroup', {})
            airline_offers_list = offers_group.get('AirlineOffers', [])
            
            if airline_offers_list and isinstance(airline_offers_list, list):
                airline_offers = airline_offers_list[0].get('AirlineOffer', [])
                for i, offer in enumerate(airline_offers):
                    if offer.get('OfferID') == offer_id:
                        selected_offer_index = i
                        break
            
            # Use the request builder to create the payload
            payload = build_flight_price_request(
                airshopping_response=airshopping_response,
                selected_offer_index=selected_offer_index
            )
            
            logger.info(f"Built FlightPrice payload for offer {offer_id} at index {selected_offer_index}")
            return payload
            
        except Exception as e:
            logger.error(f"Error building FlightPrice payload: {str(e)}")
            raise ValidationError(f"Failed to build pricing payload: {str(e)}") from e
    
    def _process_pricing_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the FlightPrice API response.
        
        Args:
            response: Raw API response
            
        Returns:
            Processed response data
        """
        # This is a simplified example - adapt based on the actual API response structure
        processed = {
            'offer_id': response.get('OfferID'),
            'price_info': response.get('PriceInfo', {}),
            'fare_rules': response.get('FareRules', []),
            'pricing_response_id': response.get('ResponseID'),
            'transaction_id': response.get('TransactionID')
        }
        
        # Process price breakdown if available
        if 'PriceInfo' in response and 'TotalAmount' in response['PriceInfo']:
            processed['total_amount'] = response['PriceInfo']['TotalAmount']
            processed['currency'] = response['PriceInfo'].get('CurrencyCode', 'USD')
        
        return processed


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
