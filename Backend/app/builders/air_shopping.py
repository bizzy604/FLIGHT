"""AirShopping request builder."""

from typing import Dict, Any, List, Optional
from app.models.requests.air_shopping import AirShoppingRequest
from app.utils.helpers import format_date
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AirShoppingRequestBuilder:
    """
    Builds VDC-compliant AirShopping request payloads.
    
    Supports:
    - One-way trips (1 segment)
    - Round-trip (2 segments)
    - Multi-city (2-5 segments)
    """
    
    def build(self, request: AirShoppingRequest) -> Dict[str, Any]:
        """
        Build AirShopping request payload.
        
        Args:
            request: Validated AirShopping request
            
        Returns:
            VDC AirShopping request payload
        """
        logger.info(f"🔨 Building AirShopping request for {request.trip_type}")
        
        # Build origin-destination segments
        origin_destinations = []
        od_references = []
        
        for i, segment in enumerate(request.segments, 1):
            od_key = f"OD{i}"
            od_references.append(od_key)
            
            origin_destinations.append({
                "OriginDestinationKey": od_key,
                "Departure": {
                    "AirportCode": {"value": segment.origin.upper()},
                    "Date": format_date(segment.departure_date)
                },
                "Arrival": {
                    "AirportCode": {"value": segment.destination.upper()}
                }
            })
        
        # Build travelers
        travelers = self._build_travelers(
            adults=request.passengers.adults,
            children=request.passengers.children,
            infants=request.passengers.infants
        )
        
        # Build cabin preferences
        cabin_preferences = self._build_cabin_preferences(
            cabin_class=request.preferences.cabin_class,
            od_references=od_references
        )
        
        # Build fare preferences
        fare_preferences = self._build_fare_preferences(
            fare_types=request.preferences.fare_types
        )
        
        # Build sort order
        sort_order = self._build_sort_order(
            sort_by=request.preferences.sort_by
        )
        
        # Assemble the request
        payload = {
            "Preference": {
                "CabinPreferences": cabin_preferences,
                "FarePreferences": fare_preferences
            },
            "ResponseParameters": {
                "SortOrder": sort_order,
                "ShopResultPreference": "FULL"
            },
            "Travelers": {
                "Traveler": travelers
            },
            "CoreQuery": {
                "OriginDestinations": {
                    "OriginDestination": origin_destinations
                }
            }
        }
        
        logger.debug(f"Built AirShopping payload: {payload}")
        return payload
    
    def _build_travelers(
        self, 
        adults: int, 
        children: int = 0, 
        infants: int = 0
    ) -> List[Dict[str, Any]]:
        """Build travelers list."""
        travelers = []
        
        # Add adults
        for _ in range(adults):
            travelers.append({
                "AnonymousTraveler": [{"PTC": {"value": "ADT"}}]
            })
        
        # Add children
        for _ in range(children):
            travelers.append({
                "AnonymousTraveler": [{"PTC": {"value": "CHD"}}]
            })
        
        # Add infants
        for _ in range(infants):
            travelers.append({
                "AnonymousTraveler": [{"PTC": {"value": "INF"}}]
            })
        
        return travelers
    
    def _build_cabin_preferences(
        self, 
        cabin_class: str, 
        od_references: List[str]
    ) -> Dict[str, Any]:
        """Build cabin preferences."""
        cabin_types = []
        
        for od_ref in od_references:
            cabin_types.append({
                "Code": cabin_class,
                "OriginDestinationReferences": [od_ref]
            })
        
        return {
            "CabinType": cabin_types
        }
    
    def _build_fare_preferences(self, fare_types: List[str]) -> Dict[str, Any]:
        """Build fare preferences."""
        return {
            "Types": {
                "Type": [{"Code": fare_type} for fare_type in fare_types]
            }
        }
    
    def _build_sort_order(self, sort_by: str) -> List[Dict[str, str]]:
        """Build sort order."""
        # Primary sort
        sort_order = [
            {"Order": "ASCENDING", "Parameter": sort_by}
        ]
        
        # Add secondary sorts
        if sort_by != "PRICE":
            sort_order.append({"Order": "ASCENDING", "Parameter": "PRICE"})
        if sort_by != "STOP":
            sort_order.append({"Order": "ASCENDING", "Parameter": "STOP"})
        
        return sort_order
