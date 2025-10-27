"""Custom exception hierarchy."""

from typing import Any, Optional


class FlightPortalError(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class VDCAPIError(FlightPortalError):
    """VDC API related errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        response: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class ValidationError(FlightPortalError):
    """Input validation errors."""
    pass


class AuthenticationError(FlightPortalError):
    """Authentication/authorization errors."""
    pass


class BusinessLogicError(FlightPortalError):
    """Business rule violations."""
    pass


class InvalidTripTypeError(ValidationError):
    """Invalid trip type specified."""
    pass


class InvalidPassengerCountError(ValidationError):
    """Invalid passenger count configuration."""
    pass


class InvalidDateError(ValidationError):
    """Invalid date provided."""
    pass
