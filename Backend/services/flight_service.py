"""
Flight Service Module (Legacy)

This module provides backward compatibility for the old flight service interface.
New code should import from the modular flight package directly.

Example:
    from Backend.services.flight import (
        search_flights,
        get_flight_price,
        create_booking,
        get_booking_details,
        process_air_shopping,
        process_flight_price,
        process_order_create,
        FlightServiceError,
        FlightService
    )
"""
import warnings
from typing import Dict, Any, Optional, List, Union, TypeVar, Type, Callable, AnyStr, IO, Tuple

# Show deprecation warning
warnings.warn(
    "The flight_service module is deprecated and will be removed in a future version. "
    "Please update imports to use the modular flight package directly.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new modular package
try:
    # Import all the main functions and classes
    from .flight import (
        search_flights_sync as search_flights,
        get_flight_price,
        create_booking,
        get_booking_details,
        process_air_shopping,
        process_flight_price,
        process_order_create,
        FlightServiceError,
        FlightService
    )
    
    # Import any additional types that might be needed for type hints
    # from .types import (
    #     FlightSearchRequest,
    #     FlightPricingRequest,
    #     BookingRequest,
    #     Passenger,
    #     PaymentInfo,
    #     ContactInfo
    # )
    
except ImportError as e:
    # Provide helpful error if the new package is not installed
    class FlightServiceError(Exception):
        """Legacy exception for flight service errors."""
        def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
            self.message = message
            self.status_code = status_code
            self.details = details or {}
            super().__init__(message)
    
    def _not_implemented(*args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "The new flight service package is not installed. "
            "Please install the required dependencies or update your imports."
        )
    
    # Create stubs that raise NotImplementedError for missing functions only
    get_flight_price = create_booking = get_booking_details = _not_implemented
    process_flight_price = process_order_create = _not_implemented
    
    class FlightService:
        """Legacy FlightService class for backward compatibility."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            _not_implemented()

# Re-export for backward compatibility
__all__ = [
    'search_flights',
    'get_flight_price',
    'create_booking',
    'get_booking_details',
    'process_air_shopping',
    'process_flight_price',
    'process_order_create',
    'FlightServiceError',
    'FlightService',
    'get_flight_offers',
    'DEFAULT_CURRENCY',
    'DEFAULT_LANGUAGE',
    'DEFAULT_FARE_TYPE'
]

# Add aliases for backward compatibility
get_flight_offers = search_flights

# Constants for backward compatibility
DEFAULT_CURRENCY: str = "USD"
DEFAULT_LANGUAGE: str = "en"
DEFAULT_FARE_TYPE: str = "PUBL"

# Documentation for developers
# ---------------------------
# This file serves as a backward compatibility layer for the old flight service interface.
# All functionality has been moved to the Backend.services.flight package.
#
# The following functions are now implemented in the new modular structure:
# - search_flights (in flight/search.py)
# - get_flight_price (in flight/pricing.py)
# - create_booking (in flight/booking.py)
# - get_booking_details (in flight/booking.py)
# - process_air_shopping (in flight/search.py)
# - process_flight_price (in flight/pricing.py)
# - process_order_create (in flight/booking.py)
#
# New code should import directly from Backend.services.flight instead of this module.
