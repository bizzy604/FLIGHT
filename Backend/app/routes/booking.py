"""
Booking API Routes

Provides endpoints for:
- Ancillary services (seats and services)
- Booking creation (OrderCreate)
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, Optional
import logging

from app.services.ancillary import AncillaryService
from app.services.order_create import OrderCreateService
from app.models.booking import OrderCreateRequest, OrderCreateResponse, ErrorResponse
from app.core.dependencies import get_ancillary_service, get_order_create_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/booking", tags=["booking"])


@router.post("/ancillaries/seats")
async def get_seat_availability(
    request: Dict[str, Any] = Body(...),
    service: AncillaryService = Depends(get_ancillary_service)
) -> Dict[str, Any]:
    """
    Get seat availability map.
    
    Request body:
    - flight_price_response: FlightPrice response (raw VDC response)
    - selected_offer_index: Index of selected offer (default: 0)
    - airline_owner: Optional airline code for ThirdpartyId header
    
    Returns:
    - Seat availability response with seat maps per segment
    - Seat pricing information
    - Seat characteristics (extra legroom, window/aisle, etc.)
    
    Example:
    ```json
    {
      "flight_price_response": { ... },
      "selected_offer_index": 0,
      "airline_owner": "EK"
    }
    ```
    """
    try:
        # Extract parameters from request body
        flight_price_response = request.get("flight_price_response", {})
        selected_offer_index = request.get("selected_offer_index", 0)
        airline_owner = request.get("airline_owner")
        
        logger.info(f"Received seat availability request for offer {selected_offer_index}")
        
        result = await service.get_seats(
            flight_price_response=flight_price_response,
            selected_offer_index=selected_offer_index,
            airline_owner=airline_owner
        )
        
        return {
            "status": "success",
            "data": result
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching seat availability: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch seat availability: {str(e)}"
        )


@router.post("/ancillaries/services")
async def get_ancillary_services(
    request: Dict[str, Any] = Body(...),
    service: AncillaryService = Depends(get_ancillary_service)
) -> Dict[str, Any]:
    """
    Get available ancillary services.
    
    Request body:
    - flight_price_response: FlightPrice response (raw VDC response)
    - selected_offer_index: Index of selected offer (default: 0)
    - airline_owner: Optional airline code for ThirdpartyId header
    
    Returns:
    - Available services (meals, baggage, lounge access, etc.)
    - Service pricing
    - Service applicability per passenger/segment
    
    Example:
    ```json
    {
      "flight_price_response": { ... },
      "selected_offer_index": 0,
      "airline_owner": "BA"
    }
    ```
    """
    try:
        # Extract parameters from request body
        flight_price_response = request.get("flight_price_response", {})
        selected_offer_index = request.get("selected_offer_index", 0)
        airline_owner = request.get("airline_owner")
        
        logger.info(f"Received ancillary services request for offer {selected_offer_index}")
        
        result = await service.get_services(
            flight_price_response=flight_price_response,
            selected_offer_index=selected_offer_index,
            airline_owner=airline_owner
        )
        
        return {
            "status": "success",
            "data": result
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching ancillary services: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch ancillary services: {str(e)}"
        )


@router.post("/ancillaries/pricing")
async def price_ancillaries(
    request: Dict[str, Any] = Body(...),
    service: AncillaryService = Depends(get_ancillary_service)
) -> Dict[str, Any]:
    """
    Price selected ancillaries (seats and/or services) by calling FlightPrice with selections.
    
    For ancillaries with PricedInd=false, this endpoint must be called to get their prices
    before booking. It calls FlightPrice again with the selected ancillaries included.
    
    Request body:
    - flight_price_response: Original FlightPrice response (raw VDC response)
    - seatavailability_response: SeatAvailability response (raw VDC response) - optional
    - servicelist_response: ServiceList response (raw VDC response) - optional
    - selected_seats: List of selected seat keys/ObjectKeys - optional
    - selected_services: List of selected service keys/ObjectKeys - optional
    - selected_offer_index: Index of selected offer (default: 0)
    - airline_owner: Optional airline code for ThirdpartyId header
    
    Returns:
    - FlightPrice response with ancillaries priced
    - Updated total price including flight + ancillaries
    
    Example:
    ```json
    {
      "flight_price_response": { ... },
      "servicelist_response": { ... },
      "selected_services": ["SER1-ServiceIdEY-1"],
      "selected_offer_index": 0,
      "airline_owner": "EY"
    }
    ```
    """
    try:
        # Extract parameters from request body
        flight_price_response = request.get("flight_price_response", {})
        seatavailability_response = request.get("seatavailability_response")
        servicelist_response = request.get("servicelist_response")
        selected_seats = request.get("selected_seats", [])
        selected_services = request.get("selected_services", [])
        selected_offer_index = request.get("selected_offer_index", 0)
        airline_owner = request.get("airline_owner")
        
        logger.info(f"Received ancillary pricing request")
        logger.info(f"  Selected seats: {len(selected_seats)}")
        logger.info(f"  Selected services: {len(selected_services)}")
        
        result = await service.price_ancillaries(
            flight_price_response=flight_price_response,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response,
            selected_seats=selected_seats,
            selected_services=selected_services,
            selected_offer_index=selected_offer_index,
            airline_owner=airline_owner
        )
        
        return {
            "status": "success",
            "data": result
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error pricing ancillaries: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to price ancillaries: {str(e)}"
        )


@router.post("/create", response_model=OrderCreateResponse)
async def create_booking(
    request: OrderCreateRequest,
    service: OrderCreateService = Depends(get_order_create_service)
) -> Dict[str, Any]:
    """
    Create a flight booking using VDC OrderCreate API.
    
    This endpoint orchestrates the complete booking creation process:
    1. Validates flight price response and passenger details
    2. Builds OrderCreate request with ancillaries (seats/services)
    3. Calls VDC OrderCreate API
    4. Transforms and returns booking details
    
    **Request Body:**
    - `flight_price_response`: FlightPrice response (required) - Contains offer pricing
    - `passengers`: List of passenger details (required) - At least 1 passenger
    - `payment`: Payment information (required) - Card details for booking
    - `selected_seats`: List of seat ObjectKeys (optional) - From SeatAvailability
    - `selected_services`: List of service ObjectKeys (optional) - From ServiceList
    - `seatavailability_response`: SeatAvailability response (optional) - If seats selected
    - `servicelist_response`: ServiceList response (optional) - If services selected
    - `ancillary_pricing_response`: FlightPrice for unpriced ancillaries (optional)
    
    **Ancillary Pricing Scenarios:**
    - **pricedInd=true**: Ancillaries are priced in ServiceList/SeatAvailability
      - Include responses in request, no additional pricing call needed
    - **pricedInd=false**: Ancillaries require pricing via FlightPrice
      - Must provide `ancillary_pricing_response` from FlightPrice call
    
    **Response:**
    - `status`: "success" or "error"
    - `booking`: Booking details (if successful)
      - `booking_reference`: Airline PNR
      - `order_id`: VDC Order ID
      - `total_price`: Price breakdown
      - `passengers`: Passenger assignments
      - `flights`: Flight details
      - `ancillaries`: Selected seats and services
    - `error`: Error message (if failed)
    
    **Example Request:**
    ```json
    {
      "flight_price_response": { "PricedFlightOffers": {...} },
      "passengers": [
        {
          "id": "PAX1",
          "type": "ADT",
          "given_name": "John",
          "surname": "Doe",
          "gender": "Male",
          "birthdate": "1990-01-15",
          "email": "john@example.com",
          "phone": "+1234567890"
        }
      ],
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
      "selected_services": ["SRV1"]
    }
    ```
    
    **HTTP Status Codes:**
    - 200: Booking created successfully
    - 400: Validation error (invalid input data)
    - 500: Server error (VDC API failure, unexpected error)
    """
    try:
        logger.info(f"📥 Received OrderCreate request for {len(request.passengers)} passenger(s)")
        
        # Convert Pydantic models to dicts for service
        passengers_dict = [p.model_dump() for p in request.passengers]
        payment_dict = request.payment.model_dump()
        
        # Call OrderCreate service
        result = await service.create_booking(
            flight_price_response=request.flight_price_response,
            passengers=passengers_dict,
            payment=payment_dict,
            seatavailability_response=request.seatavailability_response,
            servicelist_response=request.servicelist_response,
            selected_seats=request.selected_seats,
            selected_services=request.selected_services,
            ancillary_pricing_response=request.ancillary_pricing_response
        )
        
        # Check if booking was successful
        if result.get("success"):
            logger.info(f"✅ Booking created - Reference: {result.get('booking_reference')}")
            return {
                "status": "success",
                "booking": {
                    "booking_reference": result.get("booking_reference"),
                    "order_id": result.get("order_id"),
                    "total_price": result.get("total_price", {}),
                    "passengers": result.get("passengers", []),
                    "flights": result.get("flights", []),
                    "ancillaries": result.get("ancillaries", {})
                }
            }
        else:
            # Service returned error
            error_msg = result.get("error", "Unknown error occurred")
            error_type = result.get("error_type", "unknown")
            logger.error(f"❌ Booking failed: {error_msg}")
            
            # Determine appropriate HTTP status code
            if error_type == "validation_error":
                raise HTTPException(status_code=400, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Validation errors from Pydantic or service
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ Unexpected error in create_booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create booking: {str(e)}"
        )


# Legacy TODO comment removed - OrderCreate endpoint now implemented above
