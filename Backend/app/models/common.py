"""Common data models shared across requests and responses."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date


class PassengerCount(BaseModel):
    """Passenger count by type."""
    
    adults: int = Field(ge=1, le=9, description="Number of adult passengers (12+ years)")
    children: int = Field(ge=0, le=9, default=0, description="Number of child passengers (2-11 years)")
    infants: int = Field(ge=0, le=9, default=0, description="Number of infant passengers (0-2 years)")
    
    def total(self) -> int:
        """Get total passenger count."""
        return self.adults + self.children + self.infants


class FlightSegment(BaseModel):
    """Flight segment for search."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": "LHR",
                "destination": "DXB",
                "departure_date": "2025-12-01"
            }
        }
    )
    
    origin: str = Field(..., min_length=3, max_length=3, description="Origin airport code (IATA)")
    destination: str = Field(..., min_length=3, max_length=3, description="Destination airport code (IATA)")
    departure_date: date = Field(..., description="Departure date (YYYY-MM-DD)")


class ContactInfo(BaseModel):
    """Contact information."""
    
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number with country code")
    country_code: Optional[str] = Field(None, description="ISO country code")


class PassengerDetails(BaseModel):
    """Passenger personal details."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "passenger_type": "ADT",
                "title": "MR",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-15",
                "gender": "M"
            }
        }
    )
    
    passenger_type: str = Field(..., description="Passenger type: ADT, CHD, INF")
    title: str = Field(..., description="Title: MR, MS, MRS, MISS, MSTR")
    first_name: str = Field(..., min_length=1, description="First/Given name")
    last_name: str = Field(..., min_length=1, description="Last/Surname")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender: M or F")


class Price(BaseModel):
    """Price information."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 450.00,
                "currency": "USD"
            }
        }
    )
    
    amount: float = Field(..., description="Price amount")
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")


class Metadata(BaseModel):
    """Generic metadata container."""
    
    key: str
    value: str
