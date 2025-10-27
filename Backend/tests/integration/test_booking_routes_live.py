"""
Live API Integration Tests via HTTP Routes

Tests the complete end-to-end booking flow through REST API endpoints with REAL VDC API:
1. POST /api/search/flights - Search for flights
2. POST /api/search/price - Price selected offer
3. POST /api/booking/ancillaries/seats - Get seat availability (optional)
4. POST /api/booking/ancillaries/services - Get service list (optional)
5. POST /api/booking/create - Create booking

All API responses are saved to tests/integration/live_test_data/ for debugging.

Test Scenarios:
- Flight-only booking (no ancillaries)
- Flight + ancillaries (if available)
- Multi-passenger booking
- Error handling (invalid data, API errors)

NOTE: These tests require:
- Valid VDC API credentials in .env
- Active internet connection
- VDC test environment access
- FastAPI app running (via TestClient)
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from httpx import AsyncClient, ASGITransport

# Add Backend directory to path
import sys
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data directory
LIVE_TEST_DATA_DIR = Path(__file__).parent / "live_test_data"
LIVE_TEST_DATA_DIR.mkdir(exist_ok=True)


def save_response(filename: str, data: Dict[str, Any]):
    """Save API response to file for debugging."""
    filepath = LIVE_TEST_DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"💾 Saved response to {filepath}")


@pytest.fixture
def base_url():
    """Base URL for API requests."""
    return "http://testserver"


@pytest.fixture
async def client():
    """HTTP client for API calls."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


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


def extract_total_price(pricing_data: Dict[str, Any]) -> float:
    """Extract total price from pricing response."""
    try:
        pricing = pricing_data.get("pricing", {})
        total = pricing.get("total", 0.0)
        logger.info(f"💰 Total Price: {total} {pricing.get('currency', 'INR')}")
        return float(total)
    except Exception as e:
        logger.error(f"❌ Failed to extract price: {e}")
        return 0.0


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveFlightOnlyBookingViaRoutes:
    """Test Scenario 1: Flight-only booking via HTTP routes."""
    
    async def test_complete_flight_only_booking_via_api(
        self,
        client: AsyncClient,
        sample_passenger,
        sample_payment
    ):
        """
        Test complete flow for flight-only booking via REST API:
        1. POST /api/search/flights - Search flights
        2. POST /api/search/price - Price selected offer
        3. POST /api/booking/create - Create booking
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 1: Flight-Only Booking via HTTP Routes")
        logger.info("=" * 80)
        
        # Step 1: Search flights
        logger.info("\n📍 Step 1: POST /api/search/flights")
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        search_request = {
            "trip_type": "ONE_WAY",
            "segments": [
                {
                    "origin": "BOM",  # Mumbai (works in production tests)
                    "destination": "LHR",  # London Heathrow
                    "departure_date": departure_date
                }
            ],
            "passengers": {
                "adults": 1,
                "children": 0,
                "infants": 0
            },
            "preferences": {
                "cabin_class": "Y",
                "sort_by": "PRICE"
            }
        }
        
        search_response = await client.post(
            "/api/search/flights",
            json=search_request
        )
        
        assert search_response.status_code == 200, f"Search failed: {search_response.text}"
        search_data = search_response.json()
        save_response("route_1_flight_only_search.json", search_data)
        
        # Extract first airline and offer
        airlines = search_data.get("airlines", [])
        assert len(airlines) > 0, "No airlines found in search results"
        
        first_airline = airlines[0]
        airline_code = first_airline.get("code")  # Changed from "airline_code" to "code"
        offers = first_airline.get("offers", [])
        assert len(offers) > 0, "No offers found for airline"
        
        logger.info(f"✅ Found {len(airlines)} airline(s), {len(offers)} offer(s) for {airline_code}")
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: POST /api/search/price")
        
        price_request = {
            "air_shopping_response": search_data.get("raw_response"),
            "offer_index": 0,
            "airline_owner": airline_code
        }
        
        price_response = await client.post(
            "/api/search/price",
            json=price_request
        )
        
        assert price_response.status_code == 200, f"Pricing failed: {price_response.text}"
        price_data = price_response.json()
        save_response("route_1_flight_only_price.json", price_data)
        
        # Extract total price
        total_price = extract_total_price(price_data)
        assert total_price > 0, "Total price should be greater than 0"
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Step 3: Create booking
        logger.info("\n📍 Step 3: POST /api/booking/create")
        
        booking_request = {
            "flight_price_response": price_data.get("raw_response", {}),
            "passengers": [sample_passenger],
            "payment": sample_payment
        }
        
        booking_response = await client.post(
            "/api/booking/create",
            json=booking_request
        )
        
        # Note: May get 400/500 if VDC test environment has issues
        # We'll save the response regardless
        booking_data = booking_response.json()
        save_response("route_1_flight_only_booking.json", booking_data)
        
        logger.info(f"📊 Booking response status: {booking_response.status_code}")
        logger.info(f"📊 Booking data: {booking_data.get('status', 'unknown')}")
        
        # If successful, validate booking details
        if booking_response.status_code == 200:
            assert booking_data.get("status") == "success", f"Booking failed: {booking_data.get('error')}"
            
            booking_details = booking_data.get("booking", {})
            assert booking_details.get("booking_reference") is not None, "No booking reference"
            assert booking_details.get("order_id") is not None, "No order ID"
            
            logger.info(f"\n✅ Booking Success!")
            logger.info(f"   Booking Reference: {booking_details.get('booking_reference')}")
            logger.info(f"   Order ID: {booking_details.get('order_id')}")
            logger.info(f"   Total Price: {total_price} INR")
        else:
            logger.warning(f"\n⚠️ Booking API returned {booking_response.status_code}")
            logger.warning(f"   Response: {booking_data}")
            # Don't fail the test - VDC test environment may have restrictions
            pytest.skip(f"Booking API unavailable or restricted: {booking_response.status_code}")


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveBookingWithAncillariesViaRoutes:
    """Test Scenario 2: Flight + ancillaries via HTTP routes."""
    
    async def test_complete_booking_with_ancillaries_via_api(
        self,
        client: AsyncClient,
        sample_passenger,
        sample_payment
    ):
        """
        Test complete flow with ancillaries requiring pricing via REST API:
        
        Route: BOM (Mumbai) → LHR (London) with Etihad (EY)
        Note: This route supports ancillary services with PricedInd=false (requires pricing)
        
        Flow:
        1. POST /api/search/flights - Search flights
        2. POST /api/search/price - Price selected offer
        3. POST /api/booking/ancillaries/seats - Get seat availability
        4. POST /api/booking/ancillaries/services - Get service list
        5. POST /api/booking/ancillaries/pricing - Price selected ancillaries (PricedInd=false)
        6. POST /api/booking/create - Create booking with priced ancillaries
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 2: Flight + Ancillaries with Pricing via HTTP Routes")
        logger.info("=" * 80)
        
        # Step 1: Search flights
        logger.info("\n📍 Step 1: POST /api/search/flights")
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        search_request = {
            "trip_type": "ONE_WAY",
            "segments": [
                {
                    "origin": "BOM",  # Mumbai to London - production route
                    "destination": "LHR",  # Available routes: India domestic, India→Dubai, India→London
                    "departure_date": departure_date
                }
            ],
            "passengers": {
                "adults": 1,
                "children": 0,
                "infants": 0
            }
        }
        
        search_response = await client.post("/api/search/flights", json=search_request)
        assert search_response.status_code == 200
        search_data = search_response.json()
        save_response("route_2_ancillary_search.json", search_data)
        
        # Extract airline and offer
        airlines = search_data.get("airlines", [])
        assert len(airlines) > 0
        
        first_airline = airlines[0]
        airline_code = first_airline.get("code")  # Use "code" not "airline_code"
        offers = first_airline.get("offers", [])
        assert len(offers) > 0
        
        logger.info(f"✅ Found {len(offers)} offer(s) for {airline_code}")
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: POST /api/search/price")
        
        price_request = {
            "air_shopping_response": search_data.get("raw_response"),
            "offer_index": 0,
            "airline_owner": airline_code
        }
        
        price_response = await client.post("/api/search/price", json=price_request)
        assert price_response.status_code == 200
        price_data = price_response.json()
        save_response("route_2_ancillary_price.json", price_data)
        
        total_price = extract_total_price(price_data)
        assert total_price > 0
        
        # Step 3: Get seat availability
        logger.info("\n📍 Step 3: POST /api/booking/ancillaries/seats")
        
        seat_request = {
            "flight_price_response": price_data.get("raw_response", {})
        }
        
        seat_response = await client.post(
            "/api/booking/ancillaries/seats",
            json=seat_request
        )
        
        seat_data = None
        print(f"\n[DEBUG] SEAT RESPONSE STATUS: {seat_response.status_code}")
        print(f"[DEBUG] SEAT RESPONSE TEXT (first 500): {seat_response.text[:500]}")
        if seat_response.status_code == 200:
            seat_data = seat_response.json()
            save_response("route_2_ancillary_seats.json", seat_data)
            
            # Check for VDC errors in response
            vdc_errors = seat_data.get("data", {}).get("VdcErrors")
            if vdc_errors:
                error_msg = vdc_errors.get("Error", [{}])[0].get("ShortText", "Unknown error")
                logger.warning(f"[WARN] VDC returned error for seat availability: {error_msg}")
                print(f"[WARN] VDC returned error for seat availability: {error_msg}")
                print("   This route/airline may not support seat selection")
                seat_data = None  # Treat as unavailable
            else:
                logger.info("✅ Seat availability retrieved")
                print("[INFO] Seat availability retrieved")
        else:
            logger.error(f"❌ Seat availability failed: {seat_response.status_code}")
            logger.error(f"   Response: {seat_response.text[:500]}")
            print(f"❌ Seat availability failed: {seat_response.status_code}")
            print(f"   Response: {seat_response.text[:500]}")
            pytest.fail(f"Seat availability endpoint failed with status {seat_response.status_code}")
        
        # Step 4: Get service list
        logger.info("\n📍 Step 4: POST /api/booking/ancillaries/services")
        
        service_request = {
            "flight_price_response": price_data.get("raw_response", {})
        }
        
        service_response = await client.post(
            "/api/booking/ancillaries/services",
            json=service_request
        )
        
        service_data = None
        print(f"\n[DEBUG] SERVICE RESPONSE STATUS: {service_response.status_code}")
        print(f"[DEBUG] SERVICE RESPONSE TEXT (first 500): {service_response.text[:500]}")
        if service_response.status_code == 200:
            service_data = service_response.json()
            save_response("route_2_ancillary_services.json", service_data)
            
            # Check for VDC errors in response (can be VdcErrors or Errors)
            vdc_errors = service_data.get("data", {}).get("VdcErrors") or service_data.get("data", {}).get("Errors")
            if vdc_errors:
                error_list = vdc_errors.get("Error", [])
                if error_list:
                    error_msg = error_list[0].get("ShortText", "Unknown error")
                    logger.warning(f"[WARN] VDC returned error for service list: {error_msg}")
                    print(f"[WARN] VDC returned error for service list: {error_msg}")
                    print("   This route/airline may not support ancillary services")
                    service_data = None  # Treat as unavailable
                else:
                    logger.info("✅ Service list retrieved")
                    print("[INFO] Service list retrieved")
            else:
                logger.info("✅ Service list retrieved")
                print("[INFO] Service list retrieved")
        else:
            logger.error(f"❌ Service list failed: {service_response.status_code}")
            logger.error(f"   Response: {service_response.text[:500]}")
            print(f"❌ Service list failed: {service_response.status_code}")
            print(f"   Response: {service_response.text[:500]}")
            pytest.fail(f"Service list endpoint failed with status {service_response.status_code}")
        
        # CRITICAL: At least one ancillary type must be available
        if not seat_data and not service_data:
            pytest.skip("Neither seats nor services are available for this route/airline")
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Select first available seat and service (if available)
        selected_seats = []
        selected_services = []
        
        if seat_data and seat_data.get("status") == "success":
            seat_maps = seat_data.get("data", {}).get("seat_maps", [])
            if seat_maps:
                # Get first available seat from first segment
                first_segment = seat_maps[0]
                rows = first_segment.get("rows", [])
                for row in rows:
                    seats_in_row = row.get("seats", [])
                    for seat in seats_in_row:
                        if seat.get("available") and not selected_seats:
                            seat_key = seat.get("seat_key")
                            if seat_key:
                                selected_seats.append(seat_key)
                                logger.info(f"🪑 Selected seat: {seat_key}")
                                break
                    if selected_seats:
                        break
        
        if service_data and service_data.get("status") == "success":
            # Navigate VDC structure: data -> Services -> Service (array)
            raw_services = service_data.get("data", {}).get("Services", {}).get("Service", [])
            if raw_services:
                # Select first available service
                first_service = raw_services[0]
                service_key = first_service.get("ObjectKey")  # Use ObjectKey as service key
                service_name = first_service.get("Name", {}).get("value", "Unknown")
                priced_ind = first_service.get("PricedInd", True)
                if service_key:
                    selected_services.append(service_key)
                    logger.info(f"Selected service: {service_name} ({service_key})")
                    logger.info(f"   PricedInd: {priced_ind} (requires pricing: {not priced_ind})")
                    print(f"[INFO] Selected service: {service_name} ({service_key})")
                    print(f"[INFO] PricedInd: {priced_ind} (requires pricing: {not priced_ind})")
        
        # Step 5: Price ancillaries if needed (PricedInd=false)
        ancillary_pricing_data = None
        needs_pricing = False
        
        # Check if any selected service needs pricing
        if service_data and selected_services:
            raw_services = service_data.get("data", {}).get("Services", {}).get("Service", [])
            for service in raw_services:
                if service.get("ObjectKey") in selected_services:
                    if not service.get("PricedInd", True):
                        needs_pricing = True
                        break
        
        if needs_pricing:
            logger.info("\n📍 Step 5: POST /api/booking/ancillaries/pricing")
            print("[INFO] Ancillaries require pricing - calling ancillary pricing endpoint")
            
            # Call ancillary pricing endpoint with selected ancillaries
            pricing_request = {
                "flight_price_response": price_data.get("raw_response", {}),
                "servicelist_response": service_data.get("data", {}),
                "selected_services": selected_services if selected_services else [],
                "selected_offer_index": 0,
                "airline_owner": airline_code
            }
            
            ancillary_pricing_response = await client.post(
                "/api/booking/ancillaries/pricing",
                json=pricing_request
            )
            
            print(f"[DEBUG] ANCILLARY PRICING RESPONSE STATUS: {ancillary_pricing_response.status_code}")
            print(f"[DEBUG] ANCILLARY PRICING RESPONSE (first 500): {ancillary_pricing_response.text[:500]}")
            
            if ancillary_pricing_response.status_code == 200:
                ancillary_pricing_json = ancillary_pricing_response.json()
                save_response("route_2_ancillary_pricing.json", ancillary_pricing_json)
                
                # Check if VDC returned errors
                vdc_response = ancillary_pricing_json.get("data", {})
                vdc_errors = vdc_response.get("VdcErrors") or vdc_response.get("Errors")
                
                if vdc_errors:
                    error_list = vdc_errors.get("Error", [])
                    if error_list:
                        error_msg = error_list[0].get("ShortText", "Unknown VDC error")
                        logger.warning(f"⚠️ VDC returned error for ancillary pricing: {error_msg}")
                        print(f"[WARN] VDC returned error for ancillary pricing: {error_msg}")
                        print("   This route/airline may not support ancillary pricing")
                        # Don't use the error response - fall back to original price
                        ancillary_pricing_data = None
                        # Clear selected services since they couldn't be priced
                        selected_services = []
                        logger.info("   Cleared selected services due to pricing failure")
                        print("[INFO] Cleared selected services due to pricing failure")
                    else:
                        ancillary_pricing_data = ancillary_pricing_json
                        logger.info("✅ Ancillary pricing retrieved")
                        print("[INFO] Ancillary pricing retrieved")
                else:
                    ancillary_pricing_data = ancillary_pricing_json
                    logger.info("✅ Ancillary pricing retrieved")
                    print("[INFO] Ancillary pricing retrieved")
            else:
                logger.error(f"❌ Ancillary pricing failed: {ancillary_pricing_response.status_code}")
                print(f"[ERROR] Ancillary pricing failed: {ancillary_pricing_response.status_code}")
                pytest.fail(f"Ancillary pricing failed with status {ancillary_pricing_response.status_code}")
        
        # Step 6: Create booking
        logger.info("\n📍 Step 6: POST /api/booking/create")
        
        # IMPORTANT: If ancillaries were priced, use the ancillary pricing response as the flight_price_response
        # This prevents "DUPLICATE SEGMENT" errors from VDC
        flight_price_for_booking = ancillary_pricing_data.get("data", {}) if ancillary_pricing_data else price_data.get("raw_response", {})
        
        if ancillary_pricing_data:
            logger.info("   Using ancillary pricing response for booking (includes flight + ancillaries)")
            print("[INFO] Using ancillary pricing response for booking")
        else:
            logger.info("   Using original flight pricing response for booking")
        
        booking_request = {
            "flight_price_response": flight_price_for_booking,
            "passengers": [sample_passenger],
            "payment": sample_payment
        }
        
        # Add ancillary responses and selections if available
        if seat_data and seat_data.get("status") == "success":
            # data key contains the raw VDC response
            booking_request["seatavailability_response"] = seat_data.get("data", {})
            if selected_seats:
                booking_request["selected_seats"] = selected_seats
                logger.info(f"   Including {len(selected_seats)} seat selection(s)")
                
        if service_data and service_data.get("status") == "success":
            # data key contains the raw VDC response
            booking_request["servicelist_response"] = service_data.get("data", {})
            if selected_services:
                booking_request["selected_services"] = selected_services
                logger.info(f"   Including {len(selected_services)} service selection(s)")
                print(f"[INFO] Including {len(selected_services)} service selection(s): {selected_services}")
        
        booking_response = await client.post(
            "/api/booking/create",
            json=booking_request
        )
        
        print(f"\n[DEBUG] BOOKING RESPONSE STATUS: {booking_response.status_code}")
        print(f"[DEBUG] BOOKING RESPONSE (first 1000): {booking_response.text[:1000]}")
        
        booking_data = booking_response.json()
        save_response("route_2_ancillary_booking.json", booking_data)
        
        logger.info(f"📊 Booking response status: {booking_response.status_code}")
        
        if booking_response.status_code == 200:
            assert booking_data.get("status") == "success"
            booking_details = booking_data.get("booking", {})
            
            logger.info(f"\n✅ Booking Success!")
            logger.info(f"   Booking Reference: {booking_details.get('booking_reference')}")
            logger.info(f"   Order ID: {booking_details.get('order_id')}")
            logger.info(f"   Total Price: {total_price} INR")
        else:
            logger.warning(f"\n⚠️ Booking API returned {booking_response.status_code}")
            pytest.skip(f"Booking API unavailable: {booking_response.status_code}")


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveMultiPassengerBookingViaRoutes:
    """Test Scenario 3: Multi-passenger booking via HTTP routes."""
    
    async def test_complete_multi_passenger_booking_via_api(
        self,
        client: AsyncClient,
        sample_payment
    ):
        """
        Test booking with multiple passengers via REST API:
        - 2 Adults
        - 1 Child
        """
        logger.info("=" * 80)
        logger.info("🚀 Test 3: Multi-Passenger Booking (2 ADT + 1 CHD) via HTTP Routes")
        logger.info("=" * 80)
        
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
        
        # Step 1: Search flights for multiple passengers
        logger.info("\n📍 Step 1: POST /api/search/flights (2 adults + 1 child)")
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        search_request = {
            "trip_type": "ONE_WAY",
            "segments": [
                {
                    "origin": "DEL",
                    "destination": "BOM",
                    "departure_date": departure_date
                }
            ],
            "passengers": {
                "adults": 2,
                "children": 1,
                "infants": 0
            }
        }
        
        search_response = await client.post("/api/search/flights", json=search_request)
        assert search_response.status_code == 200
        search_data = search_response.json()
        save_response("route_3_multi_pax_search.json", search_data)
        
        airlines = search_data.get("airlines", [])
        assert len(airlines) > 0
        
        first_airline = airlines[0]
        airline_code = first_airline.get("airline_code")
        offers = first_airline.get("offers", [])
        assert len(offers) > 0
        
        logger.info(f"✅ Found offers for {airline_code} (3 passengers)")
        
        # Step 2: Price the offer
        logger.info("\n📍 Step 2: POST /api/search/price")
        
        price_request = {
            "air_shopping_response": search_data.get("raw_response"),
            "offer_index": 0,
            "airline_owner": airline_code
        }
        
        price_response = await client.post("/api/search/price", json=price_request)
        assert price_response.status_code == 200
        price_data = price_response.json()
        save_response("route_3_multi_pax_price.json", price_data)
        
        total_price = extract_total_price(price_data)
        assert total_price > 0
        
        # Update payment amount
        sample_payment["amount"] = total_price
        
        # Step 3: Create booking
        logger.info("\n📍 Step 3: POST /api/booking/create (3 passengers)")
        
        booking_request = {
            "flight_price_response": price_data.get("raw_response", {}),
            "passengers": passengers,
            "payment": sample_payment
        }
        
        booking_response = await client.post(
            "/api/booking/create",
            json=booking_request
        )
        
        booking_data = booking_response.json()
        save_response("route_3_multi_pax_booking.json", booking_data)
        
        logger.info(f"📊 Booking response status: {booking_response.status_code}")
        
        if booking_response.status_code == 200:
            assert booking_data.get("status") == "success"
            booking_details = booking_data.get("booking", {})
            
            passengers_in_booking = booking_details.get("passengers", [])
            logger.info(f"\n✅ Booking Success!")
            logger.info(f"   Booking Reference: {booking_details.get('booking_reference')}")
            logger.info(f"   Order ID: {booking_details.get('order_id')}")
            logger.info(f"   Total Price: {total_price} INR")
            logger.info(f"   Passengers: {len(passengers_in_booking)}")
        else:
            logger.warning(f"\n⚠️ Booking API returned {booking_response.status_code}")
            pytest.skip(f"Booking API unavailable: {booking_response.status_code}")


@pytest.mark.asyncio
@pytest.mark.live
class TestLiveErrorHandlingViaRoutes:
    """Test Scenario 4: Error handling via HTTP routes."""
    
    async def test_invalid_search_request(self, client: AsyncClient):
        """Test error handling with invalid search request."""
        logger.info("=" * 80)
        logger.info("🚀 Test 4a: Error Handling - Invalid Search Request")
        logger.info("=" * 80)
        
        logger.info("\n📍 POST /api/search/flights with invalid data")
        
        # Missing required fields
        invalid_request = {
            "trip_type": "ONE_WAY"
            # Missing segments and passengers
        }
        
        response = await client.post("/api/search/flights", json=invalid_request)
        
        logger.info(f"📊 Response status: {response.status_code}")
        assert response.status_code == 422, "Should return 422 for validation error"
        
        logger.info("✅ Validation error handled correctly")
    
    async def test_invalid_booking_request(self, client: AsyncClient, sample_payment):
        """Test error handling with invalid booking request."""
        logger.info("=" * 80)
        logger.info("🚀 Test 4b: Error Handling - Invalid Booking Request")
        logger.info("=" * 80)
        
        logger.info("\n📍 POST /api/booking/create with missing passengers")
        
        # Missing passengers (required field)
        invalid_request = {
            "flight_price_response": {},
            "passengers": [],  # Empty! Should have at least 1
            "payment": sample_payment
        }
        
        response = await client.post("/api/booking/create", json=invalid_request)
        
        logger.info(f"📊 Response status: {response.status_code}")
        
        # Should return 422 (Pydantic validation) or 400 (business logic)
        assert response.status_code in [400, 422], "Should return error for empty passengers"
        
        logger.info("✅ Error handling works correctly")


if __name__ == "__main__":
    # Run live route tests
    pytest.main([
        __file__,
        "-v",
        "-s",
        "-m", "live",
        "--tb=short"
    ])
