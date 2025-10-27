"""
Integration tests for Ancillary Services (SeatAvailability and ServiceList).

Tests complete workflow with REAL VDC API calls:
- FlightPrice → SeatAvailability
- FlightPrice → ServiceList
- Combined workflow
"""

import pytest
from pathlib import Path
import json
from app.services.ancillary import AncillaryService
from app.services.flight_price import FlightPriceService
from app.services.air_shopping import AirShoppingService
from app.core.auth import VDCAuthClient
from app.core.http_client import get_http_client
from app.models.requests.air_shopping import AirShoppingRequest, SearchPreferences
from app.models.common import PassengerCount, FlightSegment
from datetime import datetime, timedelta


import pytest
import pytest_asyncio
from pathlib import Path
import json
import httpx
from app.services.ancillary import AncillaryService
from app.services.flight_price import FlightPriceService
from app.services.air_shopping import AirShoppingService
from app.core.auth import VDCAuthClient
from app.core.http_client import get_http_client
from app.models.requests.air_shopping import AirShoppingRequest, SearchPreferences
from app.models.common import PassengerCount, FlightSegment
from datetime import datetime, timedelta


# Mark as integration and asyncio
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


@pytest_asyncio.fixture
async def auth_client():
    """Get authenticated VDC client - fresh instance per test."""
    client = VDCAuthClient()
    # Test token fetch
    token = await client.get_token()
    assert token is not None
    assert len(token) > 0  # Just verify we got a token
    return client


@pytest_asyncio.fixture
async def http_client():
    """Get HTTP client - fresh instance per test."""
    client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        follow_redirects=False
    )
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def ancillary_service(auth_client, http_client):
    """Get ancillary service instance - fresh per test."""
    return AncillaryService(auth_client=auth_client, http_client=http_client)


@pytest_asyncio.fixture
async def air_shopping_service(auth_client, http_client):
    """Get air shopping service instance - fresh per test."""
    return AirShoppingService(auth_client=auth_client, http_client=http_client)


@pytest_asyncio.fixture
async def flight_price_service(auth_client, http_client):
    """Get flight price service instance - fresh per test."""
    return FlightPriceService(auth_client=auth_client, http_client=http_client)


@pytest.fixture
def real_flight_price_response():
    """Load real FlightPrice response for offline testing."""
    response_file = Path(__file__).parent.parent.parent / "Seats & Services" / "4_FlightPriceRS.json"
    with open(response_file, 'r') as f:
        return json.load(f)


class TestSeatAvailabilityIntegration:
    """Integration tests for SeatAvailability workflow."""
    
    @pytest.mark.asyncio
    async def test_get_seats_with_real_flight_price(
        self, 
        ancillary_service, 
        real_flight_price_response
    ):
        """Should fetch seat availability using real FlightPrice response."""
        # Get seats for first offer
        result = await ancillary_service.get_seats(
            flight_price_response=real_flight_price_response,
            selected_offer_index=0
        )
        
        # Validate response structure
        assert result is not None
        assert isinstance(result, dict)
        
        # Check for SeatAvailabilityRS structure
        # (Actual structure depends on VDC response)
        print(f"\n✅ Received SeatAvailability response")
        print(f"   Response keys: {list(result.keys())}")
    
    @pytest.mark.asyncio
    async def test_complete_search_to_seats_workflow(
        self,
        air_shopping_service,
        flight_price_service,
        ancillary_service
    ):
        """Should complete full workflow: Search → Price → Seats."""
        # Step 1: Search for flights
        search_date = (datetime.now() + timedelta(days=60)).date()
        search_request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date=search_date
                )
            ],
            passengers=PassengerCount(adults=1, children=0, infants=0),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"]
            )
        )
        
        search_result = await air_shopping_service.execute(request=search_request)
        assert search_result is not None
        assert "airlines" in search_result or "offers" in search_result
        
        # Extract offers and airline info from airlines
        airlines = search_result.get("airlines", [])
        all_offers = []
        for airline in airlines:
            all_offers.extend(airline.get("offers", []))
        
        assert len(all_offers) > 0
        assert len(airlines) > 0, "No airlines found"
        
        print(f"\n📊 Step 1: Search found {len(all_offers)} offer(s) across {len(airlines)} airlines")
        
        # Step 2: Price first offer from first airline
        raw_response = search_result.get("raw_response")
        assert raw_response is not None
        
        # Get first airline code from airlines array
        first_airline = airlines[0]
        airline_owner = first_airline.get("code")  # Key is "code" not "airline_code"
        assert airline_owner is not None, "Airline code not found in first airline"
        
        # Use first offer (index 0) from this airline
        offer_index = 0
        
        price_result = await flight_price_service.execute(
            offer_index=offer_index,
            airline_owner=airline_owner,
            air_shopping_response=raw_response
        )
        assert price_result is not None
        
        flight_price_response = price_result.get("raw_response")
        assert flight_price_response is not None
        print(f"💰 Step 2: Priced offer successfully for airline {airline_owner}")
        
        # Step 3: Get seat availability
        seat_result = await ancillary_service.get_seats(
            flight_price_response=flight_price_response,
            selected_offer_index=0
        )
        
        assert seat_result is not None
        print(f"💺 Step 3: Retrieved seat availability")
        print(f"   Response structure: {list(seat_result.keys())[:5]}")
    
    @pytest.mark.asyncio
    async def test_seats_with_airline_owner_header(
        self,
        ancillary_service,
        real_flight_price_response
    ):
        """Should include ThirdpartyId header when airline_owner provided."""
        # Extract airline owner from response
        priced_offers = real_flight_price_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [])
        if not isinstance(priced_offers, list):
            priced_offers = [priced_offers] if priced_offers else []
        
        airline_owner = priced_offers[0].get('OfferID', {}).get('Owner') if priced_offers else None
        
        if airline_owner:
            result = await ancillary_service.get_seats(
                flight_price_response=real_flight_price_response,
                selected_offer_index=0,
                airline_owner=airline_owner
            )
            
            assert result is not None
            print(f"\n✅ Retrieved seats with ThirdpartyId: {airline_owner}")


class TestServiceListIntegration:
    """Integration tests for ServiceList workflow."""
    
    @pytest.mark.asyncio
    async def test_get_services_with_real_flight_price(
        self,
        ancillary_service,
        real_flight_price_response
    ):
        """Should fetch ancillary services using real FlightPrice response."""
        # Get services for first offer
        result = await ancillary_service.get_services(
            flight_price_response=real_flight_price_response,
            selected_offer_index=0
        )
        
        # Validate response structure
        assert result is not None
        assert isinstance(result, dict)
        
        # Check for ServiceListRS structure
        print(f"\n✅ Received ServiceList response")
        print(f"   Response keys: {list(result.keys())}")
    
    @pytest.mark.asyncio
    async def test_complete_search_to_services_workflow(
        self,
        air_shopping_service,
        flight_price_service,
        ancillary_service
    ):
        """Should complete full workflow: Search → Price → Services."""
        # Step 1: Search for flights
        search_date = (datetime.now() + timedelta(days=60)).date()
        search_request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="LHR",
                    departure_date=search_date
                )
            ],
            passengers=PassengerCount(adults=2, children=0, infants=0),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"]
            )
        )
        
        search_result = await air_shopping_service.execute(request=search_request)
        assert search_result is not None
        assert "airlines" in search_result or "offers" in search_result
        
        # Extract offers and airline info from airlines
        airlines = search_result.get("airlines", [])
        all_offers = []
        for airline in airlines:
            all_offers.extend(airline.get("offers", []))
        
        assert len(all_offers) > 0
        assert len(airlines) > 0, "No airlines found"
        
        print(f"\n📊 Step 1: Search found {len(all_offers)} offer(s) across {len(airlines)} airlines")
        
        # Step 2: Price first offer from first airline
        raw_response = search_result.get("raw_response")
        assert raw_response is not None
        
        # Get first airline code from airlines array
        first_airline = airlines[0]
        airline_owner = first_airline.get("code")  # Key is "code" not "airline_code"
        assert airline_owner is not None, "Airline code not found in first airline"
        
        # Use first offer (index 0) from this airline
        offer_index = 0
        
        price_result = await flight_price_service.execute(
            offer_index=offer_index,
            airline_owner=airline_owner,
            air_shopping_response=raw_response
        )
        assert price_result is not None
        
        flight_price_response = price_result.get("raw_response")
        assert flight_price_response is not None
        print(f"💰 Step 2: Priced offer successfully for airline {airline_owner}")
        
        # Step 3: Get ancillary services
        service_result = await ancillary_service.get_services(
            flight_price_response=flight_price_response,
            selected_offer_index=0
        )
        
        assert service_result is not None
        print(f"🍽️  Step 3: Retrieved ancillary services")
        print(f"   Response structure: {list(service_result.keys())[:5]}")


class TestCombinedAncillaryWorkflow:
    """Integration tests for combined seats + services workflow."""
    
    @pytest.mark.asyncio
    async def test_get_both_seats_and_services(
        self,
        ancillary_service,
        real_flight_price_response
    ):
        """Should fetch both seats and services for same offer."""
        # Get seats
        seats = await ancillary_service.get_seats(
            flight_price_response=real_flight_price_response,
            selected_offer_index=0
        )
        
        # Get services
        services = await ancillary_service.get_services(
            flight_price_response=real_flight_price_response,
            selected_offer_index=0
        )
        
        assert seats is not None
        assert services is not None
        
        print(f"\n✅ Retrieved both seats and services")
        print(f"   Seats response: {list(seats.keys())[:5]}")
        print(f"   Services response: {list(services.keys())[:5]}")
    
    @pytest.mark.asyncio
    async def test_complete_booking_preparation_workflow(
        self,
        air_shopping_service,
        flight_price_service,
        ancillary_service
    ):
        """Should complete full workflow: Search → Price → Seats + Services (ready for booking)."""
        # Step 1: Search
        search_date = (datetime.now() + timedelta(days=60)).date()
        search_request = AirShoppingRequest(
            trip_type="ONE_WAY",
            segments=[
                FlightSegment(
                    origin="BOM",
                    destination="DXB",
                    departure_date=search_date
                )
            ],
            passengers=PassengerCount(adults=1, children=1, infants=0),
            preferences=SearchPreferences(
                cabin_class="Y",
                fare_types=["PUBL"]
            )
        )
        
        search_result = await air_shopping_service.execute(request=search_request)
        assert search_result is not None
        assert "airlines" in search_result or "offers" in search_result
        
        # Extract offers and airline info from airlines
        airlines = search_result.get("airlines", [])
        all_offers = []
        for airline in airlines:
            all_offers.extend(airline.get("offers", []))
        
        assert len(all_offers) > 0
        assert len(airlines) > 0, "No airlines found"
        
        print(f"\n📊 Search: {len(all_offers)} offer(s) found across {len(airlines)} airlines")
        
        # Step 2: Price first offer from first airline
        raw_response = search_result.get("raw_response")
        assert raw_response is not None
        
        # Get first airline code from airlines array
        first_airline = airlines[0]
        airline_owner = first_airline.get("code")  # Key is "code" not "airline_code"
        assert airline_owner is not None, "Airline code not found in first airline"
        
        # Use first offer (index 0) from this airline
        offer_index = 0
        
        price_result = await flight_price_service.execute(
            offer_index=offer_index,
            airline_owner=airline_owner,
            air_shopping_response=raw_response
        )
        assert price_result is not None
        flight_price_response = price_result.get("raw_response")
        assert flight_price_response is not None
        
        print(f"💰 Price: Offer priced successfully for airline {airline_owner}")
        
        # Step 3: Get ancillaries (parallel)
        seats = await ancillary_service.get_seats(
            flight_price_response=flight_price_response,
            selected_offer_index=0
        )
        
        services = await ancillary_service.get_services(
            flight_price_response=flight_price_response,
            selected_offer_index=0
        )
        
        assert seats is not None
        assert services is not None
        
        print(f"💺 Seats: Retrieved seat availability")
        print(f"🍽️  Services: Retrieved ancillary services")
        print(f"\n✅ Complete workflow ready for booking!")
        print(f"   Next step: OrderCreate with FlightPrice + Seats + Services")


class TestAncillaryErrorHandling:
    """Test error handling in ancillary services."""
    
    @pytest.mark.asyncio
    async def test_invalid_flight_price_response_seats(self, ancillary_service):
        """Should handle invalid FlightPrice response for seats."""
        invalid_response = {
            "PricedFlightOffers": {},  # No offers
            "ShoppingResponseID": {},
            "DataLists": {}
        }
        
        with pytest.raises(Exception):  # Should raise ValueError or VDCAPIError
            await ancillary_service.get_seats(
                flight_price_response=invalid_response,
                selected_offer_index=0
            )
    
    @pytest.mark.asyncio
    async def test_invalid_flight_price_response_services(self, ancillary_service):
        """Should handle invalid FlightPrice response for services."""
        invalid_response = {
            "PricedFlightOffers": {},  # No offers
            "ShoppingResponseID": {},
            "DataLists": {}
        }
        
        with pytest.raises(Exception):  # Should raise ValueError or VDCAPIError
            await ancillary_service.get_services(
                flight_price_response=invalid_response,
                selected_offer_index=0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
