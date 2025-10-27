"""FlightPrice request models."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any


class FlightPriceRequest(BaseModel):
    """
    FlightPrice request model.
    
    Used to get detailed pricing for a selected offer from AirShopping results.
    
    Note: airline_owner is REQUIRED because FlightPrice operates in single-airline
    context only. Even if AirShopping returned multi-airline results, the user must
    have selected a specific airline's offer before pricing.
    """
    
    air_shopping_response: Dict[str, Any] = Field(
        ..., 
        description="Complete AirShopping response containing the selected offer"
    )
    offer_index: int = Field(
        ..., 
        ge=0, 
        description="Index of the selected offer within the airline's offers (not global index)"
    )
    airline_owner: str = Field(
        ...,
        min_length=2,
        max_length=3,
        description="Airline code (e.g., 'EK', 'BA', 'LH') - REQUIRED for single-airline pricing"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "air_shopping_response": {"OffersGroup": {"AirlineOffers": []}},
                "offer_index": 0,
                "airline_owner": "EK"
            }
        }
    )
