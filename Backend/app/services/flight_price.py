"""FlightPrice service - Offer pricing workflow."""

from typing import Dict, Any
from app.services.base import BaseVDCService
from app.builders.flight_price import FlightPriceRequestBuilder
from app.transformers.flight_price import FlightPriceTransformer
from app.core.exceptions import BusinessLogicError, ValidationError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FlightPriceService(BaseVDCService):
    """
    Handles offer pricing workflow.
    
    Workflow:
    1. Validate input (airline_owner, offer_index, air_shopping_response)
    2. Build VDC FlightPrice request
    3. Call VDC FlightPrice API
    4. Transform response for frontend
    
    Note: FlightPrice operates in single-airline context only.
    The airline_owner must be provided to identify which airline's offer to price.
    """
    
    async def execute(
        self,
        offer_index: int,
        airline_owner: str,
        air_shopping_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute offer pricing.
        
        Args:
            offer_index: Index of the offer within the airline's offers
            airline_owner: Airline code (e.g., 'EK', 'BA', 'LH') - REQUIRED
            air_shopping_response: The complete AirShopping response
            
        Returns:
            Transformed pricing data with detailed breakdown
            
        Raises:
            ValidationError: If required parameters are missing or invalid
            BusinessLogicError: If offer not found or airline not available
        """
        logger.info(
            f"💰 Executing FlightPrice for airline '{airline_owner}', "
            f"offer index {offer_index}"
        )
        
        # Validate required parameters
        self._validate_input(offer_index, airline_owner, air_shopping_response)
        
        # Build VDC FlightPrice request
        try:
            builder = FlightPriceRequestBuilder(air_shopping_response)
            vdc_payload = builder.build(
                offer_index=offer_index,
                airline_owner=airline_owner
            )
        except BusinessLogicError as e:
            logger.error(f"❌ Failed to build FlightPrice request: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error building FlightPrice request: {e}", exc_info=True)
            raise BusinessLogicError(f"Failed to build pricing request: {str(e)}")
        
        # Call VDC FlightPrice API
        try:
            # Save the request payload for debugging
            import json
            with open("debug_flightprice_request.json", "w") as f:
                json.dump(vdc_payload, f, indent=2)
            logger.info("💾 Saved FlightPrice request to debug_flightprice_request.json")
            
            raw_response = await self._make_request(
                service_name="FlightPrice",
                payload=vdc_payload,
                airline_owner=airline_owner  # For ThirdpartyId header
            )
            
            # Save the response for debugging
            with open("debug_flightprice_response.json", "w") as f:
                json.dump(raw_response, f, indent=2)
            logger.info("💾 Saved FlightPrice response to debug_flightprice_response.json")
            
        except Exception as e:
            logger.error(f"❌ VDC FlightPrice API call failed: {e}", exc_info=True)
            raise
        
        # Transform response
        try:
            transformer = FlightPriceTransformer()
            transformed = transformer.transform(raw_response)
            # Include raw response for downstream services (SeatAvailability, ServiceList)
            transformed["raw_response"] = raw_response
        except Exception as e:
            logger.error(f"❌ Failed to transform FlightPrice response: {e}", exc_info=True)
            raise BusinessLogicError(f"Failed to transform pricing response: {str(e)}")
        
        logger.info(
            f"✅ FlightPrice complete - total: {transformed.get('pricing', {}).get('total', 'N/A')}"
        )
        
        return transformed
    
    def _validate_input(
        self,
        offer_index: int,
        airline_owner: str,
        air_shopping_response: Dict[str, Any]
    ) -> None:
        """
        Validate FlightPrice input parameters.
        
        Args:
            offer_index: Offer index
            airline_owner: Airline code
            air_shopping_response: AirShopping response
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate airline_owner
        if not airline_owner:
            raise ValidationError("airline_owner is required for FlightPrice")
        
        if not isinstance(airline_owner, str):
            raise ValidationError("airline_owner must be a string")
        
        if len(airline_owner) < 2:
            raise ValidationError("airline_owner must be at least 2 characters")
        
        # Validate offer_index
        if not isinstance(offer_index, int):
            raise ValidationError("offer_index must be an integer")
        
        if offer_index < 0:
            raise ValidationError("offer_index must be non-negative")
        
        # Validate air_shopping_response
        if not air_shopping_response:
            raise ValidationError("air_shopping_response is required")
        
        if not isinstance(air_shopping_response, dict):
            raise ValidationError("air_shopping_response must be a dictionary")
        
        # Check for required AirShopping response structure
        if "OffersGroup" not in air_shopping_response:
            raise ValidationError(
                "Invalid air_shopping_response: missing 'OffersGroup'. "
                "Please provide the complete AirShopping response."
            )
        
        logger.debug(
            f"✅ Input validated: airline={airline_owner}, "
            f"offer_index={offer_index}"
        )
