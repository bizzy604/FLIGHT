"""
Type definitions for the Flight Service.

This module contains type aliases and data structures used throughout the flight service.
"""
from typing import Dict, List, Any, Optional, TypedDict, Literal, Union

# Type aliases
AirportCode = str
CurrencyCode = str
DateTimeStr = str  # ISO 8601 format

# Enums
class CabinClass:
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"

class TripType:
    ONE_WAY = "ONE_WAY"
    ROUND_TRIP = "ROUND_TRIP"
    MULTI_CITY = "MULTI_CITY"

# Request/Response Types
class ODSegment(TypedDict, total=False):
    """Origin-Destination segment for flight search."""
    origin: AirportCode
    destination: AirportCode
    departure_date: DateTimeStr
    return_date: Optional[DateTimeStr]

class PassengerCounts(TypedDict, total=False):
    """Passenger count information."""
    adults: int
    children: int
    infants: int

class SearchCriteria(TypedDict, total=False):
    """Flight search criteria."""
    trip_type: str  # TripType value
    od_segments: List[ODSegment]
    num_adults: int
    num_children: int
    num_infants: int
    cabin_preference: str  # CabinClass value
    request_id: Optional[str]

class FlightOffer(TypedDict):
    """Flight offer information."""
    offer_id: str
    shopping_response_id: str
    # Add other offer fields as needed

class PricingRequest(TypedDict, total=False):
    """Flight pricing request data."""
    air_shopping_response: Dict[str, Any]
    offer_id: str
    shopping_response_id: str
    currency: str
    request_id: Optional[str]

class BookingRequest(TypedDict, total=False):
    """Flight booking request data."""
    flight_price_response: Dict[str, Any]
    passengers: List[Dict[str, Any]]
    payment_info: Dict[str, Any]
    contact_info: Dict[str, str]
    request_id: Optional[str]

# Response Types
class FlightSearchResponse(TypedDict):
    """Flight search response data."""
    status: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    request_id: Optional[str]

class PricingResponse(TypedDict):
    """Flight pricing response data."""
    status: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    request_id: Optional[str]

class BookingResponse(TypedDict):
    """Booking response data."""
    status: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    request_id: Optional[str]
