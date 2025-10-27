"""Travel date validation."""

from datetime import date, datetime, timedelta
from typing import List
from app.models.common import FlightSegment
from app.core.exceptions import InvalidDateError


def validate_travel_dates(segments: List[FlightSegment]) -> None:
    """
    Validate travel dates for flight segments.
    
    Rules:
    - Departure date must be in the future (at least tomorrow)
    - Dates must be in chronological order for multi-segment trips
    - Maximum 330 days in advance
    
    Args:
        segments: List of flight segments
        
    Raises:
        InvalidDateError: If dates are invalid
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    max_advance_days = 330
    max_date = today + timedelta(days=max_advance_days)
    
    for i, segment in enumerate(segments):
        departure = segment.departure_date
        
        # Check if date is in the past
        if departure < tomorrow:
            raise InvalidDateError(
                f"Segment {i+1}: Departure date must be at least tomorrow ({tomorrow})"
            )
        
        # Check if date is too far in the future
        if departure > max_date:
            raise InvalidDateError(
                f"Segment {i+1}: Departure date cannot be more than {max_advance_days} days in advance"
            )
        
        # For multi-segment, check chronological order
        if i > 0:
            previous_departure = segments[i-1].departure_date
            if departure < previous_departure:
                raise InvalidDateError(
                    f"Segment {i+1}: Departure date must be after previous segment ({previous_departure})"
                )


def validate_date_range(start_date: date, end_date: date, min_days: int = 0, max_days: int = 365) -> None:
    """
    Validate a date range.
    
    Args:
        start_date: Start date
        end_date: End date
        min_days: Minimum days between dates
        max_days: Maximum days between dates
        
    Raises:
        InvalidDateError: If date range is invalid
    """
    if end_date < start_date:
        raise InvalidDateError("End date must be after start date")
    
    days_diff = (end_date - start_date).days
    
    if days_diff < min_days:
        raise InvalidDateError(f"Date range must be at least {min_days} days")
    
    if days_diff > max_days:
        raise InvalidDateError(f"Date range cannot exceed {max_days} days")
