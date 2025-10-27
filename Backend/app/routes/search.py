"""Search API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.models.requests.air_shopping import AirShoppingRequest
from app.models.requests.flight_price import FlightPriceRequest
from app.services.air_shopping import AirShoppingService
from app.services.flight_price import FlightPriceService
from app.core.dependencies import get_vdc_auth, get_http
from app.core.auth import VDCAuthClient
from app.core.exceptions import VDCAPIError, ValidationError, BusinessLogicError
from app.utils.logger import get_logger
import httpx

logger = get_logger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


def get_air_shopping_service(
    auth: VDCAuthClient = Depends(get_vdc_auth),
    http: httpx.AsyncClient = Depends(get_http)
) -> AirShoppingService:
    """Dependency for AirShopping service."""
    return AirShoppingService(auth_client=auth, http_client=http)


def get_flight_price_service(
    auth: VDCAuthClient = Depends(get_vdc_auth),
    http: httpx.AsyncClient = Depends(get_http)
) -> FlightPriceService:
    """Dependency for FlightPrice service."""
    return FlightPriceService(auth_client=auth, http_client=http)


@router.post("/flights")
async def search_flights(
    request: AirShoppingRequest,
    service: AirShoppingService = Depends(get_air_shopping_service)
) -> Dict[str, Any]:
    """
    Search for flights.
    
    **Request Body:**
    - `trip_type`: Trip type (ONE_WAY, ROUND_TRIP, MULTI_CITY)
    - `segments`: List of flight segments with origin, destination, and departure date
    - `passengers`: Passenger counts (adults, children, infants)
    - `preferences`: Optional search preferences (cabin class, fare types, etc.)
    
    **Returns:**
    - `offers`: List of flight offers with pricing
    - `metadata`: Search metadata and context
    - `raw_response`: Raw VDC response (for subsequent FlightPrice calls)
    
    **Example:**
    ```json
    {
        "trip_type": "ROUND_TRIP",
        "segments": [
            {"origin": "LHR", "destination": "DXB", "departure_date": "2025-12-01"},
            {"origin": "DXB", "destination": "LHR", "departure_date": "2025-12-15"}
        ],
        "passengers": {"adults": 2, "children": 0, "infants": 0},
        "preferences": {"cabin_class": "Y", "fare_types": ["PUBL", "PVT"]}
    }
    ```
    """
    try:
        logger.info(f"📥 Received flight search request: {request.trip_type}")
        result = await service.execute(request=request)
        
        # Count total offers across all airlines
        total_offers = sum(len(airline.get("offers", [])) for airline in result.get("airlines", []))
        logger.info(f"📤 Returning {total_offers} offers from {len(result.get('airlines', []))} airline(s)")
        return result
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except VDCAPIError as e:
        logger.error(f"🔴 VDC API error: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": str(e), "vdc_response": e.response}
        )
        
    except Exception as e:
        logger.error(f"🔴 Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Flight search failed. Please try again."
        )


@router.get("/test")
async def test_search():
    """Test endpoint to verify search route is working."""
    return {
        "message": "Search API is working",
        "endpoints": {
            "search_flights": "POST /api/search/flights",
            "price_offer": "POST /api/search/price"
        }
    }


@router.post("/price")
async def price_offer(
    request: FlightPriceRequest,
    service: FlightPriceService = Depends(get_flight_price_service)
) -> Dict[str, Any]:
    """
    Get detailed pricing for a selected flight offer.
    
    **Important:** This endpoint requires a specific airline's offer to be selected.
    FlightPrice operates in single-airline context only.
    
    **Request Body:**
    - `air_shopping_response`: Complete AirShopping response (from /flights endpoint)
    - `offer_index`: Index of the offer within the airline's offers (NOT global index)
    - `airline_owner`: Airline code (REQUIRED) - e.g., 'EK', 'BA', 'LH'
    
    **Returns:**
    - `offer_id`: Unique offer identifier
    - `pricing`: Total, base fare, taxes, and currency
    - `breakdown`: Per-passenger pricing breakdown
    - `fare_details`: Fare basis codes, cabin types, booking classes
    - `penalties`: Change and cancellation fees
    - `baggage`: Baggage allowances per passenger type
    - `segments`: Flight segment details with service references
    - `metadata`: Response metadata
    
    **Example:**
    ```json
    {
        "air_shopping_response": {"OffersGroup": {...}},
        "offer_index": 0,
        "airline_owner": "EK"
    }
    ```
    
    **Note:** The `offer_index` should be the index within the specific airline's
    offers, not a global index across all airlines. The frontend should track this
    when displaying multi-airline search results.
    """
    try:
        logger.info(
            f"📥 Received FlightPrice request for airline '{request.airline_owner}', "
            f"offer index {request.offer_index}"
        )
        
        result = await service.execute(
            offer_index=request.offer_index,
            airline_owner=request.airline_owner,
            air_shopping_response=request.air_shopping_response
        )
        
        logger.info(
            f"📤 Returning pricing: {result.get('pricing', {}).get('total', 'N/A')}"
        )
        return result
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except BusinessLogicError as e:
        logger.warning(f"⚠️ Business logic error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except VDCAPIError as e:
        logger.error(f"🔴 VDC API error: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": str(e), "vdc_response": e.response}
        )
        
    except Exception as e:
        logger.error(f"🔴 Unexpected error in FlightPrice: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Offer pricing failed. Please try again."
        )

