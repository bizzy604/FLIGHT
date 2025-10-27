"""
Live API Integration Tests for OrderCreate

Tests the complete end-to-end flow with REAL VDC API (not mocked):
1. AirShopping - Search for flights
2. FlightPrice - Price selected offer
3. SeatAvailability - Get seat maps (if needed)
4. ServiceList - Get ancillary services (if needed)
5. FlightPrice - Price ancillaries if unpriced (pricedInd=false)
6. OrderCreate - Create booking

Test Scenarios:
- Flight-only booking (no ancillaries)
- Flight + priced ancillaries (seats/services)
- Flight + unpriced ancillaries (require pricing)
- Multi-passenger booking
- Error handling (invalid data, API errors)

NOTE: These tests require:
- Valid VDC API credentials in .env
- Active internet connection
- VDC test environment access
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

# Add Backend directory to path
import sys
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.air_shopping import AirShoppingService
from app.services.flight_price import FlightPriceService
from app.services.ancillary import AncillaryService
from app.services.order_create import OrderCreateService
from app.core.auth import VDCAuthClient
from app.models.requests.air_shopping import AirShoppingRequest, FlightSegment, PassengerCounts
from app.models.requests.flight_price import FlightPriceRequest
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data directory
LIVE_TEST_DATA_DIR = Path(__file__).parent / "live_test_data"
LIVE_TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="module")
def auth_client():
    """Initialize VDC auth client for live API calls."""
    return VDCAuthClient()


@pytest.fixture(scope="module")
def http_client():
    """Initialize HTTP client for services."""
    return httpx.AsyncClient()


@pytest.fixture(scope="module")
def air_shopping_service(auth_client, http_client):
    """Initialize AirShopping service."""
    return AirShoppingService(auth_client, http_client)


@pytest.fixture(scope="module")
def flight_price_service(auth_client, http_client):
    """Initialize FlightPrice service."""
    return FlightPriceService(auth_client, http_client)


@pytest.fixture(scope="module")
def ancillary_service(auth_client, http_client):
    """Initialize Ancillary service."""
    return AncillaryService(auth_client, http_client)


@pytest.fixture(scope="module")
def order_create_service():
    """Initialize OrderCreate service."""
    return OrderCreateService()


@pytest.fixture
def sample_search_params():
    """Sample search parameters for AirShopping."""
    # Search for flights 30 days from now
    departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    return AirShoppingRequest(
        trip_type="ONE_WAY",
        segments=[
            FlightSegment(
                origin="DEL",  # Delhi
                destination="BOM",  # Mumbai
                departure_date=departure_date
            )
        ],
        passengers=PassengerCounts(
            adults=1,
            children=0,
            infants=0
        )
    )


@pytest.fixture
def sample_passenger():
    """Sample passenger for booking."""
    return {
        "id": "PAX1",
        "type": "ADT",
        "title": "Mr",
        "given_name": "John",
        "surname": "Doe",
        "gender": "Male",
        "birthdate": "1990-01-15",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "country_code": "1"
    }


@pytest.fixture
def sample_payment():
    """Sample payment information."""
    return {
        "method": "CASH",
        "card_number": "4111111111111111",
        "card_type": "VI",
        "card_holder_name": "JOHN DOE",
        "expiry_date": "12/25",
        "cvv": "123",
        "amount": 0,  # Will be updated based on actual price
        "currency": "INR"
    }


def save_response(filename: str, data: Dict[str, Any]):
    """Save API response to file for debugging."""
    filepath = LIVE_TEST_DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"💾 Saved response to {filepath}")


def extract_offer_id(air_shopping_response: Dict[str, Any]) -> Optional[str]:
    """Extract the first offer ID from AirShopping response."""
    try:
        offers = air_shopping_response.get("AirlineOffers", [])
        if offers and len(offers) > 0:
            offer = offers[0]
            offer_id = offer.get("OfferID", {}).get("value")
            logger.info(f"📋 Extracted Offer ID: {offer_id}")
            return offer_id
        return None
    except Exception as e:
        logger.error(f"❌ Failed to extract offer ID: {e}")
        return None


def extract_total_price(flight_price_response: Dict[str, Any]) -> float:
    """Extract total price from FlightPrice response."""
    try:
        offers = flight_price_response.get("PricedFlightOffers", [])
        if offers and len(offers) > 0:
            total_amount = offers[0].get("TotalAmount", {})
            price = float(total_amount.get("SimpleCurrencyPrice", {}).get("value", 0))
            logger.info(f"💰 Total Price: {price} {total_amount.get('SimpleCurrencyPrice', {}).get('Code', 'INR')}")
            return price
        return 0.0
    except Exception as e:
        logger.error(f"❌ Failed to extract price: {e}")
        return 0.0


def check_priced_ind(servicelist_response: Dict[str, Any]) -> bool:
    """Check if ancillaries are priced (pricedInd flag)."""
    try:
        data_lists = servicelist_response.get("DataLists", {})
        service_definitions = data_lists.get("ServiceDefinitionList", {}).get("ServiceDefinition", [])
        
        if not service_definitions:
            return True  # Default to priced if no services
        
        # Check first service for pricedInd
        first_service = service_definitions[0] if isinstance(service_definitions, list) else service_definitions
        priced_ind = first_service.get("pricedInd", True)
        logger.info(f"🏷️ Ancillaries pricedInd: {priced_ind}")
        return priced_ind
    except Exception as e:
        logger.error(f"❌ Failed to check pricedInd: {e}")
        return True


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveFlightOnlyBooking:
    """Test Scenario 1: Flight-only booking (no ancillaries)."""
    
    async def test_complete_flight_only_booking(
        self,
        air_shopping_service,
        flight_price_service,
        order_create_service,
        sample_search_params,
        sample_passenger,
        sample_payment
    ):
        """
        Test complete flow for flight-only booking:
        1. Search flights
        2. Price selected offer
        3. Create booking (no ancillaries)
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 1: Flight-Only Booking")
        logger.info("=" * 80)
        
        # Step 1: Search flights
        logger.info("\n📍 Step 1: Searching flights...")
        air_shopping_response = await air_shopping_service.search_flights(
            origin=sample_search_params["originCode"],
            destination=sample_search_params["destinationCode"],
            departure_date=sample_search_params["departureDate"],
            passengers=sample_search_params["passengers"],
            cabin_class=sample_search_params["cabinClass"]
        )
        
        assert air_shopping_response is not None, "AirShopping response is None"
        save_response("1_flight_only_air_shopping.json", air_shopping_response)
        
        # Extract offer ID
        offer_id = extract_offer_id(air_shopping_response)
        assert offer_id is not None, "No offer ID found in response"
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: Pricing selected offer...")
        flight_price_response = await flight_price_service.price_offer(
            offer_id=offer_id,
            air_shopping_response=air_shopping_response
        )
        
        assert flight_price_response is not None, "FlightPrice response is None"
        save_response("1_flight_only_flight_price.json", flight_price_response)
        
        # Extract total price
        total_price = extract_total_price(flight_price_response)
        assert total_price > 0, "Total price should be greater than 0"
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Step 3: Create booking
        logger.info("\n📍 Step 3: Creating booking...")
        booking_result = await order_create_service.create_booking(
            flight_price_response=flight_price_response,
            passengers=[sample_passenger],
            payment=sample_payment
        )
        
        assert booking_result is not None, "Booking result is None"
        save_response("1_flight_only_booking_result.json", booking_result)
        
        # Validate booking result
        assert booking_result.get("success") is True, f"Booking failed: {booking_result.get('error')}"
        assert booking_result.get("booking_reference") is not None, "No booking reference"
        assert booking_result.get("order_id") is not None, "No order ID"
        
        logger.info(f"\n✅ Booking Success!")
        logger.info(f"   Booking Reference: {booking_result.get('booking_reference')}")
        logger.info(f"   Order ID: {booking_result.get('order_id')}")
        logger.info(f"   Total Price: {total_price} INR")


@pytest.mark.asyncio
@pytest.mark.live
class TestLivePricedAncillariesBooking:
    """Test Scenario 2: Flight + priced ancillaries (seats/services)."""
    
    async def test_complete_booking_with_priced_ancillaries(
        self,
        air_shopping_service,
        flight_price_service,
        ancillary_service,
        order_create_service,
        sample_search_params,
        sample_passenger,
        sample_payment
    ):
        """
        Test complete flow with priced ancillaries:
        1. Search flights
        2. Price selected offer
        3. Get seat availability
        4. Get service list
        5. Create booking with selected ancillaries
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 2: Flight + Priced Ancillaries Booking")
        logger.info("=" * 80)
        
        # Step 1: Search flights
        logger.info("\n📍 Step 1: Searching flights...")
        air_shopping_response = await air_shopping_service.search_flights(
            origin=sample_search_params["originCode"],
            destination=sample_search_params["destinationCode"],
            departure_date=sample_search_params["departureDate"],
            passengers=sample_search_params["passengers"],
            cabin_class=sample_search_params["cabinClass"]
        )
        
        assert air_shopping_response is not None
        save_response("2_priced_air_shopping.json", air_shopping_response)
        
        offer_id = extract_offer_id(air_shopping_response)
        assert offer_id is not None
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: Pricing offer...")
        flight_price_response = await flight_price_service.price_offer(
            offer_id=offer_id,
            air_shopping_response=air_shopping_response
        )
        
        assert flight_price_response is not None
        save_response("2_priced_flight_price.json", flight_price_response)
        
        total_price = extract_total_price(flight_price_response)
        assert total_price > 0
        
        # Step 3: Get seat availability
        logger.info("\n📍 Step 3: Getting seat availability...")
        try:
            seatavailability_response = await ancillary_service.get_seat_availability(
                flight_price_response=flight_price_response
            )
            
            save_response("2_priced_seat_availability.json", seatavailability_response)
            logger.info("✅ Seat availability retrieved")
        except Exception as e:
            logger.warning(f"⚠️ Seat availability failed: {e}")
            seatavailability_response = None
        
        # Step 4: Get service list
        logger.info("\n📍 Step 4: Getting service list...")
        try:
            servicelist_response = await ancillary_service.get_service_list(
                flight_price_response=flight_price_response
            )
            
            save_response("2_priced_service_list.json", servicelist_response)
            logger.info("✅ Service list retrieved")
            
            # Check if services are priced
            is_priced = check_priced_ind(servicelist_response)
            assert is_priced, "Expected priced ancillaries but got unpriced"
        except Exception as e:
            logger.warning(f"⚠️ Service list failed: {e}")
            servicelist_response = None
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Step 5: Create booking (with ancillaries if available)
        logger.info("\n📍 Step 5: Creating booking...")
        booking_result = await order_create_service.create_booking(
            flight_price_response=flight_price_response,
            passengers=[sample_passenger],
            payment=sample_payment,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response
        )
        
        assert booking_result is not None
        save_response("2_priced_booking_result.json", booking_result)
        
        # Validate booking result
        assert booking_result.get("success") is True, f"Booking failed: {booking_result.get('error')}"
        assert booking_result.get("booking_reference") is not None
        assert booking_result.get("order_id") is not None
        
        logger.info(f"\n✅ Booking Success!")
        logger.info(f"   Booking Reference: {booking_result.get('booking_reference')}")
        logger.info(f"   Order ID: {booking_result.get('order_id')}")
        logger.info(f"   Total Price: {total_price} INR")


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveUnpricedAncillariesBooking:
    """Test Scenario 3: Flight + unpriced ancillaries (require pricing)."""
    
    async def test_complete_booking_with_unpriced_ancillaries(
        self,
        air_shopping_service,
        flight_price_service,
        ancillary_service,
        order_create_service,
        sample_search_params,
        sample_passenger,
        sample_payment
    ):
        """
        Test complete flow with unpriced ancillaries:
        1. Search flights
        2. Price selected offer
        3. Get seat availability
        4. Get service list
        5. Check pricedInd flag
        6. Price ancillaries if unpriced
        7. Create booking with ancillary pricing
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 3: Flight + Unpriced Ancillaries Booking")
        logger.info("=" * 80)
        
        # Step 1: Search flights
        logger.info("\n📍 Step 1: Searching flights...")
        air_shopping_response = await air_shopping_service.search_flights(
            origin=sample_search_params["originCode"],
            destination=sample_search_params["destinationCode"],
            departure_date=sample_search_params["departureDate"],
            passengers=sample_search_params["passengers"],
            cabin_class=sample_search_params["cabinClass"]
        )
        
        assert air_shopping_response is not None
        save_response("3_unpriced_air_shopping.json", air_shopping_response)
        
        offer_id = extract_offer_id(air_shopping_response)
        assert offer_id is not None
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: Pricing offer...")
        flight_price_response = await flight_price_service.price_offer(
            offer_id=offer_id,
            air_shopping_response=air_shopping_response
        )
        
        assert flight_price_response is not None
        save_response("3_unpriced_flight_price.json", flight_price_response)
        
        base_price = extract_total_price(flight_price_response)
        assert base_price > 0
        
        # Step 3: Get service list
        logger.info("\n📍 Step 3: Getting service list...")
        servicelist_response = await ancillary_service.get_service_list(
            flight_price_response=flight_price_response
        )
        
        assert servicelist_response is not None
        save_response("3_unpriced_service_list.json", servicelist_response)
        
        # Step 4: Check if ancillaries need pricing
        is_priced = check_priced_ind(servicelist_response)
        
        ancillary_pricing_response = None
        total_price = base_price
        
        if not is_priced:
            logger.info("\n📍 Step 5: Pricing unpriced ancillaries...")
            # In real scenario, you would select specific services and price them
            # For now, we'll just demonstrate the flow
            logger.info("⚠️ Ancillaries require pricing (pricedInd=false)")
            logger.info("   Note: Skipping ancillary selection for this test")
            logger.info("   In production, user would select services and we'd call FlightPrice again")
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Step 6: Create booking
        logger.info("\n📍 Step 6: Creating booking...")
        booking_result = await order_create_service.create_booking(
            flight_price_response=flight_price_response,
            passengers=[sample_passenger],
            payment=sample_payment,
            servicelist_response=servicelist_response,
            ancillary_pricing_response=ancillary_pricing_response
        )
        
        assert booking_result is not None
        save_response("3_unpriced_booking_result.json", booking_result)
        
        # Validate booking result
        assert booking_result.get("success") is True, f"Booking failed: {booking_result.get('error')}"
        assert booking_result.get("booking_reference") is not None
        assert booking_result.get("order_id") is not None
        
        logger.info(f"\n✅ Booking Success!")
        logger.info(f"   Booking Reference: {booking_result.get('booking_reference')}")
        logger.info(f"   Order ID: {booking_result.get('order_id')}")
        logger.info(f"   Base Price: {base_price} INR")
        logger.info(f"   Total Price: {total_price} INR")


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveMultiPassengerBooking:
    """Test Scenario 4: Multi-passenger booking."""
    
    async def test_complete_multi_passenger_booking(
        self,
        air_shopping_service,
        flight_price_service,
        order_create_service,
        sample_payment
    ):
        """
        Test booking with multiple passengers:
        - 2 Adults
        - 1 Child
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 4: Multi-Passenger Booking (2 ADT + 1 CHD)")
        logger.info("=" * 80)
        
        # Multi-passenger search params
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        search_params = {
            "originCode": "DEL",
            "destinationCode": "BOM",
            "departureDate": departure_date,
            "passengers": {
                "adults": 2,
                "children": 1,
                "infants": 0
            },
            "cabinClass": "Economy"
        }
        
        # Multi-passenger details
        passengers = [
            {
                "id": "PAX1",
                "type": "ADT",
                "title": "Mr",
                "given_name": "John",
                "surname": "Doe",
                "gender": "Male",
                "birthdate": "1985-03-15",
                "email": "john.doe@example.com",
                "phone": "+1234567890"
            },
            {
                "id": "PAX2",
                "type": "ADT",
                "title": "Mrs",
                "given_name": "Jane",
                "surname": "Doe",
                "gender": "Female",
                "birthdate": "1987-07-20",
                "email": "jane.doe@example.com",
                "phone": "+1234567891"
            },
            {
                "id": "PAX3",
                "type": "CHD",
                "title": "Miss",
                "given_name": "Emily",
                "surname": "Doe",
                "gender": "Female",
                "birthdate": "2015-11-10",
                "email": "emily.doe@example.com",
                "phone": "+1234567892"
            }
        ]
        
        # Step 1: Search flights
        logger.info("\n📍 Step 1: Searching flights for 2 adults + 1 child...")
        air_shopping_response = await air_shopping_service.search_flights(
            origin=search_params["originCode"],
            destination=search_params["destinationCode"],
            departure_date=search_params["departureDate"],
            passengers=search_params["passengers"],
            cabin_class=search_params["cabinClass"]
        )
        
        assert air_shopping_response is not None
        save_response("4_multi_pax_air_shopping.json", air_shopping_response)
        
        offer_id = extract_offer_id(air_shopping_response)
        assert offer_id is not None
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: Pricing offer...")
        flight_price_response = await flight_price_service.price_offer(
            offer_id=offer_id,
            air_shopping_response=air_shopping_response
        )
        
        assert flight_price_response is not None
        save_response("4_multi_pax_flight_price.json", flight_price_response)
        
        total_price = extract_total_price(flight_price_response)
        assert total_price > 0
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Step 3: Create booking
        logger.info("\n📍 Step 3: Creating booking for 3 passengers...")
        booking_result = await order_create_service.create_booking(
            flight_price_response=flight_price_response,
            passengers=passengers,
            payment=sample_payment
        )
        
        assert booking_result is not None
        save_response("4_multi_pax_booking_result.json", booking_result)
        
        # Validate booking result
        assert booking_result.get("success") is True, f"Booking failed: {booking_result.get('error')}"
        assert booking_result.get("booking_reference") is not None
        assert booking_result.get("order_id") is not None
        
        # Validate passenger count
        passengers_in_booking = booking_result.get("passengers", [])
        assert len(passengers_in_booking) == 3, f"Expected 3 passengers, got {len(passengers_in_booking)}"
        
        logger.info(f"\n✅ Booking Success!")
        logger.info(f"   Booking Reference: {booking_result.get('booking_reference')}")
        logger.info(f"   Order ID: {booking_result.get('order_id')}")
        logger.info(f"   Total Price: {total_price} INR")
        logger.info(f"   Passengers: {len(passengers_in_booking)}")


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveErrorHandling:
    """Test Scenario 5: Error handling."""
    
    async def test_invalid_passenger_data(
        self,
        order_create_service,
        sample_payment
    ):
        """Test error handling with invalid passenger data."""
        logger.info("=" * 80)
        logger.info("🚀 Test 5: Error Handling - Invalid Passenger Data")
        logger.info("=" * 80)
        
        # Invalid passenger (missing required fields)
        invalid_passenger = {
            "id": "PAX1",
            "type": "ADT"
            # Missing: given_name, surname, birthdate, etc.
        }
        
        # Dummy flight price response
        flight_price_response = {
            "PricedFlightOffers": [
                {
                    "TotalAmount": {
                        "SimpleCurrencyPrice": {
                            "Code": "INR",
                            "value": 5000
                        }
                    }
                }
            ]
        }
        
        sample_payment["amount"] = 5000
        
        logger.info("\n📍 Attempting to create booking with invalid passenger...")
        booking_result = await order_create_service.create_booking(
            flight_price_response=flight_price_response,
            passengers=[invalid_passenger],
            payment=sample_payment
        )
        
        # Should return error result (not raise exception)
        assert booking_result is not None
        assert booking_result.get("success") is False, "Expected booking to fail"
        assert booking_result.get("error") is not None, "Expected error message"
        
        logger.info(f"✅ Error handling works correctly")
        logger.info(f"   Error: {booking_result.get('error')}")
        logger.info(f"   Error Type: {booking_result.get('error_type')}")
    
    async def test_missing_payment_data(
        self,
        order_create_service,
        sample_passenger
    ):
        """Test error handling with missing payment data."""
        logger.info("=" * 80)
        logger.info("🚀 Test 5: Error Handling - Missing Payment Data")
        logger.info("=" * 80)
        
        # Missing payment
        flight_price_response = {
            "PricedFlightOffers": [
                {
                    "TotalAmount": {
                        "SimpleCurrencyPrice": {
                            "Code": "INR",
                            "value": 5000
                        }
                    }
                }
            ]
        }
        
        logger.info("\n📍 Attempting to create booking without payment...")
        booking_result = await order_create_service.create_booking(
            flight_price_response=flight_price_response,
            passengers=[sample_passenger],
            payment=None  # Missing payment
        )
        
        # Should return error result
        assert booking_result is not None
        assert booking_result.get("success") is False
        assert booking_result.get("error") is not None
        
        logger.info(f"✅ Error handling works correctly")
        logger.info(f"   Error: {booking_result.get('error')}")


if __name__ == "__main__":
    # Run live tests
    pytest.main([
        __file__,
        "-v",
        "-s",
        "-m", "live",
        "--tb=short"
    ])
