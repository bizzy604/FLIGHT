"""AirShopping service - Flight search workflow."""

from typing import Dict, Any
from app.services.base import BaseVDCService
from app.builders.air_shopping import AirShoppingRequestBuilder
from app.transformers.air_shopping import AirShoppingTransformer
from app.models.requests.air_shopping import AirShoppingRequest
from app.validators.travel_dates import validate_travel_dates
from app.validators.passengers import validate_passenger_counts
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AirShoppingService(BaseVDCService):
    """
    Handles flight search workflow.
    
    Workflow:
    1. Validate input (dates, passengers)
    2. Build VDC AirShopping request
    3. Call VDC AirShopping API
    4. Transform response for frontend
    """
    
    async def execute(
        self,
        request: AirShoppingRequest
    ) -> Dict[str, Any]:
        """
        Execute flight search.
        
        Args:
            request: Validated search request
            
        Returns:
            Transformed flight offers with metadata
        """
        logger.info(f"🔍 Executing AirShopping for {request.trip_type} trip")
        
        # Validate travel dates
        validate_travel_dates(request.segments)
        
        # Validate passenger counts
        validate_passenger_counts(request.passengers)
        
        # Build VDC payload
        builder = AirShoppingRequestBuilder()
        vdc_payload = builder.build(request)
        
        # Call VDC API
        raw_response = await self._make_request(
            service_name="AirShopping",
            payload=vdc_payload
        )
        
        # Transform response
        transformer = AirShoppingTransformer()
        transformed = transformer.transform(
            response=raw_response,
            search_context=request.dict()
        )
        
        total_offers = sum(len(airline["offers"]) for airline in transformed.get("airlines", []))
        logger.info(f"✅ AirShopping complete - found {total_offers} offers across {len(transformed.get('airlines', []))} airlines")
        
        return transformed
