"""Tests for input validators."""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError as PydanticValidationError
from app.validators.travel_dates import validate_travel_dates, validate_date_range
from app.validators.passengers import validate_passenger_counts, validate_passenger_type
from app.models.common import PassengerCount, FlightSegment
from app.core.exceptions import ValidationError, InvalidPassengerCountError, InvalidDateError


class TestTravelDateValidation:
    """Test travel date validation logic."""
    
    def test_validate_future_dates(self):
        """Should accept dates in the future."""
        tomorrow = date.today() + timedelta(days=1)
        segments = [FlightSegment(origin="LAX", destination="JFK", departure_date=tomorrow)]
        validate_travel_dates(segments)  # Should not raise
    
    def test_reject_past_dates(self):
        """Should reject dates in the past."""
        yesterday = date.today() - timedelta(days=1)
        segments = [FlightSegment(origin="LAX", destination="JFK", departure_date=yesterday)]
        
        with pytest.raises(InvalidDateError, match="at least tomorrow"):
            validate_travel_dates(segments)
    
    def test_reject_today_date(self):
        """Should reject today's date (must be at least tomorrow)."""
        today = date.today()
        segments = [FlightSegment(origin="LAX", destination="JFK", departure_date=today)]
        
        with pytest.raises(InvalidDateError, match="must be at least tomorrow"):
            validate_travel_dates(segments)
    
    def test_reject_dates_too_far_ahead(self):
        """Should reject dates more than 330 days in advance."""
        far_future = date.today() + timedelta(days=331)
        segments = [FlightSegment(origin="LAX", destination="JFK", departure_date=far_future)]
        
        with pytest.raises(InvalidDateError, match="cannot be more than 330 days"):
            validate_travel_dates(segments)
    
    def test_accept_max_advance_booking(self):
        """Should accept dates exactly 330 days ahead."""
        max_advance = date.today() + timedelta(days=330)
        segments = [FlightSegment(origin="LAX", destination="JFK", departure_date=max_advance)]
        validate_travel_dates(segments)  # Should not raise
    
    def test_validate_chronological_order(self):
        """Should enforce chronological order for multi-segment trips."""
        date1 = date.today() + timedelta(days=10)
        date2 = date.today() + timedelta(days=5)  # Earlier than date1
        segments = [
            FlightSegment(origin="LAX", destination="JFK", departure_date=date1),
            FlightSegment(origin="JFK", destination="LHR", departure_date=date2)
        ]
        
        with pytest.raises(InvalidDateError, match="must be after previous segment"):
            validate_travel_dates(segments)
    
    def test_accept_chronological_dates(self):
        """Should accept properly ordered dates."""
        date1 = date.today() + timedelta(days=10)
        date2 = date.today() + timedelta(days=15)
        date3 = date.today() + timedelta(days=20)
        segments = [
            FlightSegment(origin="LAX", destination="JFK", departure_date=date1),
            FlightSegment(origin="JFK", destination="LHR", departure_date=date2),
            FlightSegment(origin="LHR", destination="DXB", departure_date=date3)
        ]
        
        validate_travel_dates(segments)  # Should not raise
    
    def test_validate_date_range(self):
        """Should validate date range constraints."""
        start = date.today() + timedelta(days=10)
        end = date.today() + timedelta(days=5)  # Before start
        
        with pytest.raises(InvalidDateError, match="must be after"):
            validate_date_range(start, end, min_days=1, max_days=30)
    
    def test_reject_date_range_too_short(self):
        """Should reject date ranges shorter than minimum."""
        start = date.today() + timedelta(days=10)
        end = date.today() + timedelta(days=11)  # Only 1 day
        
        with pytest.raises(InvalidDateError, match="must be at least"):
            validate_date_range(start, end, min_days=3, max_days=30)
    
    def test_reject_date_range_too_long(self):
        """Should reject date ranges longer than maximum."""
        start = date.today() + timedelta(days=10)
        end = date.today() + timedelta(days=50)  # 40 days
        
        with pytest.raises(InvalidDateError, match="cannot exceed"):
            validate_date_range(start, end, min_days=1, max_days=30)


class TestPassengerValidation:
    """Test passenger count and type validation."""
    
    def test_validate_minimum_adults(self):
        """Should require at least one adult - validated by Pydantic model."""
        # PassengerCount model itself enforces adults >= 1
        with pytest.raises(PydanticValidationError, match="greater than or equal to 1"):
            PassengerCount(adults=0, children=2, infants=0)
    
    def test_accept_single_adult(self):
        """Should accept a single adult passenger."""
        passengers = PassengerCount(adults=1, children=0, infants=0)
        validate_passenger_counts(passengers)  # Should not raise
    
    def test_validate_infant_adult_ratio(self):
        """Should ensure infants don't exceed adults."""
        passengers = PassengerCount(adults=1, children=0, infants=2)
        
        with pytest.raises(InvalidPassengerCountError, match="cannot exceed"):
            validate_passenger_counts(passengers)
    
    def test_accept_equal_infants_and_adults(self):
        """Should accept equal number of infants and adults."""
        passengers = PassengerCount(adults=2, children=0, infants=2)
        validate_passenger_counts(passengers)  # Should not raise
    
    def test_validate_maximum_total_passengers(self):
        """Should enforce maximum of 9 total passengers."""
        passengers = PassengerCount(adults=5, children=3, infants=2)
        
        with pytest.raises(InvalidPassengerCountError, match="cannot exceed 9"):
            validate_passenger_counts(passengers)
    
    def test_accept_maximum_passengers(self):
        """Should accept exactly 9 passengers."""
        passengers = PassengerCount(adults=5, children=4, infants=0)
        validate_passenger_counts(passengers)  # Should not raise
    
    def test_validate_passenger_type_adt(self):
        """Should accept ADT passenger type."""
        validate_passenger_type("ADT")  # Should not raise
    
    def test_validate_passenger_type_chd(self):
        """Should accept CHD passenger type."""
        validate_passenger_type("CHD")  # Should not raise
    
    def test_validate_passenger_type_inf(self):
        """Should accept INF passenger type."""
        validate_passenger_type("INF")  # Should not raise
    
    def test_reject_invalid_passenger_type(self):
        """Should reject invalid passenger types."""
        with pytest.raises(InvalidPassengerCountError, match="Must be one of"):
            validate_passenger_type("SENIOR")
    
    def test_reject_lowercase_passenger_type(self):
        """Should reject lowercase passenger types (strict validation)."""
        with pytest.raises(InvalidPassengerCountError):
            validate_passenger_type("adt")
    
    def test_mixed_passenger_counts(self):
        """Should accept valid mixed passenger counts."""
        passengers = PassengerCount(adults=2, children=2, infants=1)
        validate_passenger_counts(passengers)  # Should not raise
    
    def test_zero_children_and_infants(self):
        """Should accept trips with only adults."""
        passengers = PassengerCount(adults=3, children=0, infants=0)
        validate_passenger_counts(passengers)  # Should not raise
