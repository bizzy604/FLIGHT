"""
Flight Service Exceptions

This module contains custom exceptions for the flight service.
"""

class FlightServiceError(Exception):
    """Base exception for flight service errors."""
    pass


class RateLimitExceeded(FlightServiceError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(FlightServiceError):
    """Raised when there's an authentication error with the API."""
    pass


class ValidationError(FlightServiceError):
    """Raised when input validation fails."""
    pass


class APIError(FlightServiceError):
    """Raised when there's an error from the Verteil NDC API."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class BookingError(FlightServiceError):
    """Raised when there's an error during the booking process."""
    pass


class PricingError(FlightServiceError):
    """Raised when there's an error during the pricing process."""
    pass
