"""Passenger validation."""

from app.models.common import PassengerCount
from app.core.exceptions import InvalidPassengerCountError


def validate_passenger_counts(passengers: PassengerCount) -> None:
    """
    Validate passenger counts.
    
    Rules:
    - At least 1 adult required
    - Infants cannot exceed adults (lap infant rule)
    - Maximum 9 total passengers
    
    Args:
        passengers: Passenger counts
        
    Raises:
        InvalidPassengerCountError: If counts are invalid
    """
    # Check minimum adults
    if passengers.adults < 1:
        raise InvalidPassengerCountError("At least 1 adult is required")
    
    # Check infant limit
    if passengers.infants > passengers.adults:
        raise InvalidPassengerCountError(
            f"Number of infants ({passengers.infants}) cannot exceed adults ({passengers.adults})"
        )
    
    # Check maximum total
    total = passengers.total()
    if total > 9:
        raise InvalidPassengerCountError(
            f"Total passengers ({total}) cannot exceed 9"
        )
    
    if total < 1:
        raise InvalidPassengerCountError("At least 1 passenger is required")


def validate_passenger_type(passenger_type: str) -> None:
    """
    Validate passenger type code.
    
    Args:
        passenger_type: Passenger type code
        
    Raises:
        InvalidPassengerCountError: If type is invalid
    """
    valid_types = ["ADT", "CHD", "INF"]
    if passenger_type not in valid_types:
        raise InvalidPassengerCountError(
            f"Invalid passenger type: {passenger_type}. Must be one of {valid_types}"
        )
