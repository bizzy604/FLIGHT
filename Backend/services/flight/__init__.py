"""
Flight Service Package

This package contains modules for handling flight-related operations including
search, pricing, booking, services, and seat availability through the Verteil NDC API.
"""

# Import key components for easier access
from .core import FlightService
from .exceptions import FlightServiceError
from .search import process_air_shopping
from .pricing import get_flight_price, process_flight_price
from .booking import create_booking, process_order_create, get_booking_details
# Note: servicelist and seatavailability modules removed - now handled by dedicated route endpoints
from .airport_service import AirportService
from .airport_data_parser import parse_airport_data # If direct parsing is needed elsewhere

# For backward compatibility
__all__ = [
    'FlightService',
    'FlightServiceError',
    'get_flight_price',
    'create_booking',
    'get_booking_details',
    'process_air_shopping',
    'process_flight_price',
    'process_order_create',
# Removed: seat availability and service list items (now handled by dedicated endpoints)
    'AirportService',
    'parse_airport_data', # Optional: if direct access to parser is desired
]
