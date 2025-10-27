"""AirShopping request models."""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from app.models.common import PassengerCount, FlightSegment
from app.utils.constants import TripType, CabinClass, FareType, SortOption


class SearchPreferences(BaseModel):
    """Search preferences and filters."""
    
    cabin_class: CabinClass = Field(default="Y", description="Preferred cabin class")
    fare_types: List[FareType] = Field(
        default=["PUBL", "PVT"], 
        description="Fare types to search"
    )
    sort_by: SortOption = Field(default="PRICE", description="Sort results by")
    include_baggage: bool = Field(default=True, description="Include baggage information")
    max_stops: Optional[int] = Field(None, ge=0, le=3, description="Maximum number of stops")
    airlines: Optional[List[str]] = Field(None, description="Preferred airlines (IATA codes)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cabin_class": "Y",
                "fare_types": ["PUBL", "PVT"],
                "sort_by": "PRICE",
                "include_baggage": True,
                "max_stops": 1,
                "airlines": ["AA", "DL", "UA"]
            }
        }
    )


class AirShoppingRequest(BaseModel):
    """
    AirShopping request model.
    
    This model represents a flight search request with support for:
    - One-way trips (1 segment)
    - Round-trip (2 segments)
    - Multi-city (2-5 segments)
    """
    
    trip_type: TripType = Field(..., description="Trip type: ONE_WAY, ROUND_TRIP, MULTI_CITY")
    segments: List[FlightSegment] = Field(..., min_length=1, max_length=5, description="Flight segments")
    passengers: PassengerCount = Field(..., description="Passenger counts by type")
    preferences: Optional[SearchPreferences] = Field(default_factory=SearchPreferences)
    
    @field_validator('segments')
    @classmethod
    def validate_segments(cls, v: List[FlightSegment], info) -> List[FlightSegment]:
        """Validate segment count matches trip type."""
        if not v:
            raise ValueError("At least one segment is required")
        
        # Get trip_type from validation info if available
        trip_type = info.data.get('trip_type')
        if not trip_type:
            return v
            
        segment_count = len(v)
        
        if trip_type == "ONE_WAY" and segment_count != 1:
            raise ValueError("ONE_WAY trip must have exactly 1 segment")
        elif trip_type == "ROUND_TRIP" and segment_count != 2:
            raise ValueError("ROUND_TRIP must have exactly 2 segments")
        elif trip_type == "MULTI_CITY" and not (2 <= segment_count <= 5):
            raise ValueError("MULTI_CITY must have 2-5 segments")
        
        return v
    
    @field_validator('passengers')
    @classmethod
    def validate_passengers(cls, v: PassengerCount) -> PassengerCount:
        """Validate passenger counts."""
        if v.infants > v.adults:
            raise ValueError("Number of infants cannot exceed number of adults")
        
        if v.total() > 9:
            raise ValueError("Total passengers cannot exceed 9")
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trip_type": "ROUND_TRIP",
                "segments": [
                    {
                        "origin": "LHR",
                        "destination": "DXB",
                        "departure_date": "2025-12-01"
                    },
                    {
                        "origin": "DXB",
                        "destination": "LHR",
                        "departure_date": "2025-12-15"
                    }
                ],
                "passengers": {
                    "adults": 2,
                    "children": 1,
                    "infants": 0
                },
                "preferences": {
                    "cabin_class": "Y",
                    "fare_types": ["PUBL", "PVT"],
                    "sort_by": "PRICE"
                }
            }
        }
    )
