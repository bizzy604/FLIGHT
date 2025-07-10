"""
Shared airline data including IATA code to name mappings.

This module provides a centralized location for airline code mappings
that can be used across different parts of the application.
"""

# NOTE: This file now uses the centralized airline mapping service.
# The AIRLINE_NAMES dictionary has been moved to services/airline_mapping_service.py
# to serve as the single source of truth for all airline name mappings.

def get_airline_name(airline_code: str, log_missing: bool = True) -> str:
    """
    Get airline name from IATA code using centralized mapping service.

    Args:
        airline_code: 2-letter IATA airline code
        log_missing: Whether to log missing airline codes

    Returns:
        str: Airline name or generic name if not found
    """
    # Import here to avoid circular imports
    from services.airline_mapping_service import AirlineMappingService

    if not airline_code:
        if log_missing:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug("Empty airline code provided")
        return "Unknown Airline"

    # Use centralized airline mapping service
    return AirlineMappingService.get_airline_display_name(airline_code)

def get_airline_logo_url(airline_code: str) -> str:
    """
    Return a local URL to the airline's logo based on the IATA code, for use with the frontend's /public/airlines directory.
    """
    code = (airline_code or "").strip().upper()
    if not code:
        return "/airlines/unknown.png"
    return f"/airlines/{code}.svg"
