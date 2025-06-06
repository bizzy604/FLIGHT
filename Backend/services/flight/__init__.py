"""
Flight Service Package

This package contains modules for handling flight-related operations including
search, pricing, and booking through the Verteil NDC API.
"""

# Import key components for easier access
from .core import FlightService
from .exceptions import FlightServiceError
from .search import search_flights, search_flights_sync, process_air_shopping
from .pricing import get_flight_price, process_flight_price
from .booking import create_booking, process_order_create, get_booking_details

# For backward compatibility
__all__ = [
    'FlightService',
    'FlightServiceError',
    'search_flights',
    'get_flight_price',
    'create_booking',
    'get_booking_details',
    'process_air_shopping',
    'process_flight_price',
    'process_order_create'
]
