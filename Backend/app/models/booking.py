"""
Booking/OrderCreate Request and Response Models

Pydantic models for OrderCreate API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import date


class PassengerInfo(BaseModel):
    """Passenger information for booking."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "PAX1",
                "type": "ADT",
                "title": "MR",
                "given_name": "John",
                "surname": "Doe",
                "gender": "Male",
                "birthdate": "1990-01-15",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "country_code": "1"
            }
        }
    )
    
    id: str = Field(..., description="Passenger ID (e.g., PAX1, PAX2)")
    type: str = Field(..., description="Passenger type: ADT, CHD, INF")
    title: Optional[str] = Field(None, description="Title: Mr, Ms, Mrs, Miss, Mstr")
    given_name: str = Field(..., min_length=1, description="Given/First name")
    surname: str = Field(..., min_length=1, description="Surname/Last name")
    gender: str = Field(..., description="Gender: Male or Female")
    birthdate: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number with country code")
    country_code: Optional[str] = Field("1", description="Phone country code")
    
    @field_validator('type')
    @classmethod
    def validate_passenger_type(cls, v):
        allowed = ['ADT', 'CHD', 'INF']
        if v not in allowed:
            raise ValueError(f"Passenger type must be one of {allowed}")
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        allowed = ['Male', 'Female', 'M', 'F']
        if v not in allowed:
            raise ValueError(f"Gender must be one of {allowed}")
        return v


class PaymentInfo(BaseModel):
    """Payment information for booking."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "method": "CASH",
                "card_number": "4111111111111111",
                "card_type": "VI",
                "card_holder_name": "JOHN DOE",
                "expiry_date": "12/25",
                "amount": 500.00,
                "currency": "USD"
            }
        }
    )
    
    method: str = Field(..., description="Payment method: CASH, CARD")
    card_number: str = Field(..., description="Card number (required even for CASH)")
    card_type: str = Field(..., description="Card type: VI, CA, AX, DC")
    card_holder_name: str = Field(..., description="Cardholder name")
    expiry_date: str = Field(..., description="Card expiry (MM/YY)")
    cvv: Optional[str] = Field(None, description="Card CVV/CVC")
    amount: float = Field(..., ge=0, description="Total payment amount")
    currency: str = Field(default="USD", description="Payment currency (ISO 4217)")
    
    @field_validator('method')
    @classmethod
    def validate_payment_method(cls, v):
        allowed = ['CASH', 'CARD', 'CREDIT_CARD']
        if v not in allowed:
            raise ValueError(f"Payment method must be one of {allowed}")
        return v.upper()
    
    @field_validator('card_type')
    @classmethod
    def validate_card_type(cls, v):
        allowed = ['VI', 'CA', 'AX', 'DC', 'MC']
        if v not in allowed:
            raise ValueError(f"Card type must be one of {allowed}")
        return v.upper()


class OrderCreateRequest(BaseModel):
    """OrderCreate API request model."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flight_price_response": {"PricedFlightOffers": {}},
                "passengers": [{
                    "id": "PAX1",
                    "type": "ADT",
                    "given_name": "John",
                    "surname": "Doe",
                    "gender": "Male",
                    "birthdate": "1990-01-15",
                    "email": "john@example.com",
                    "phone": "+1234567890"
                }],
                "payment": {
                    "method": "CASH",
                    "card_number": "4111111111111111",
                    "card_type": "VI",
                    "card_holder_name": "JOHN DOE",
                    "expiry_date": "12/25",
                    "amount": 500.00,
                    "currency": "USD"
                },
                "selected_seats": ["30F"],
                "selected_services": ["SRV1"],
                "seatavailability_response": None,
                "servicelist_response": None,
                "ancillary_pricing_response": None
            }
        }
    )
    
    flight_price_response: Dict[str, Any] = Field(
        ..., 
        description="FlightPrice response containing offer details"
    )
    passengers: List[PassengerInfo] = Field(
        ..., 
        min_length=1,
        description="List of passengers (at least 1 required)"
    )
    payment: PaymentInfo = Field(..., description="Payment information")
    
    # Optional ancillary data
    selected_seats: Optional[List[str]] = Field(
        None, 
        description="List of selected seat ObjectKeys"
    )
    selected_services: Optional[List[str]] = Field(
        None, 
        description="List of selected service ObjectKeys"
    )
    seatavailability_response: Optional[Dict[str, Any]] = Field(
        None, 
        description="SeatAvailability response (if seats selected)"
    )
    servicelist_response: Optional[Dict[str, Any]] = Field(
        None, 
        description="ServiceList response (if services selected)"
    )
    ancillary_pricing_response: Optional[Dict[str, Any]] = Field(
        None, 
        description="FlightPrice response for unpriced ancillaries (pricedInd=false)"
    )


class BookingDetails(BaseModel):
    """Booking details in response."""
    
    booking_reference: str = Field(..., description="Airline booking reference (PNR)")
    order_id: str = Field(..., description="VDC Order ID")
    total_price: Dict[str, Any] = Field(..., description="Total price breakdown")
    passengers: List[Dict[str, Any]] = Field(..., description="Passenger details")
    flights: List[Dict[str, Any]] = Field(..., description="Flight details")
    ancillaries: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Ancillaries (seats, services)"
    )


class OrderCreateResponse(BaseModel):
    """OrderCreate API response model."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "booking": {
                    "booking_reference": "ABC123",
                    "order_id": "ORD456",
                    "total_price": {
                        "amount": 500.00,
                        "currency": "USD"
                    },
                    "passengers": [],
                    "flights": [],
                    "ancillaries": {}
                }
            }
        }
    )
    
    status: str = Field(..., description="Response status: success or error")
    booking: Optional[BookingDetails] = Field(None, description="Booking details (if successful)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    error_type: Optional[str] = Field(None, description="Error type: validation_error, http_error, etc.")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    status: str = Field(default="error", description="Status: error")
    error: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
