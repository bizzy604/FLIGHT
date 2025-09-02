#!/usr/bin/env python3
"""
Test file to verify build_ordercreate_rq.py functionality using REAL API data from logs.
This test uses actual responses from FlightPrice, SeatAvailability, and ServiceList APIs.
"""

import sys
import os
import json
import logging
from unittest.mock import Mock, patch

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the function to test
from build_ordercreate_rq import generate_order_create_rq

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_real_api_data():
    """Load real API data from the logs directory."""
    
    # Load FlightPrice response
    flight_price_path = "api_logs/flight_price/20250829_070544_b21ad204-21ec-446d-b221-8a78dd71e432_response.json"
    with open(flight_price_path, 'r') as f:
        flight_price_data = json.load(f)
    
    # Load SeatAvailability response
    seat_availability_path = "api_logs/seat_availability/20250829_070551_b2d81ab1-5d97-47c1-a619-ea29da52c12c_response.json"
    with open(seat_availability_path, 'r') as f:
        seat_availability_data = json.load(f)
    
    # Load ServiceList response
    service_list_path = "api_logs/service_list/20250829_070551_b8732f6b-a792-4190-b87b-5e399bc96e16_response.json"
    with open(service_list_path, 'r') as f:
        service_list_data = json.load(f)
    
    return flight_price_data, seat_availability_data, service_list_data

def create_real_passenger_data():
    """Create passenger data based on the real API response structure."""
    return [
        {
            "PTC": "ADT",
            "Name": {"Surname": "Test", "Given": "User"},
            "Gender": "M",
            "BirthDate": "1990-01-01",
            "Documents": [],
            "Contacts": [
                {
                    "PhoneContact": {
                        "Number": [{"CountryCode": "358", "value": "0796861525"}],
                        "Application": "Home"
                    },
                    "EmailContact": {
                        "Address": {"value": "kevinamoni20@gmail.com"}
                    },
                    "AddressContact": {
                        "Street": ["190"],
                        "PostalCode": "30500",
                        "CityName": "LODWAR",
                        "CountryCode": {"value": "FI"}
                    }
                }
            ],
            "ObjectKey": "PAX1"
        }
    ]

def create_real_payment_info():
    """Create payment information based on the real API response."""
    return {
        "MethodType": "CASH",
        "currency": "INR",
        "Details": {},
        "CashInd": True
    }

def test_real_flight_price_response():
    """Test with real FlightPrice response data."""
    logger.info("=== Testing Real FlightPrice Response ===")
    
    try:
        # Load real data
        flight_price_data, seat_availability_data, service_list_data = load_real_api_data()
        
        # Extract the actual response from the wrapper
        flight_price_response = flight_price_data["response"]
        seatavailability_response = seat_availability_data["response"]
        servicelist_response = service_list_data["response"]
        
        # Test data
        passengers_data = create_real_passenger_data()
        payment_info = create_real_payment_info()
        selected_seats = []  # No seats for this test
        selected_services = []  # No services for this test
        
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response,
            selected_seats=selected_seats,
            selected_services=selected_services
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        assert "Passengers" in result["Query"], "Result should have Passengers"
        assert "Payments" in result["Query"], "Result should have Payments"
        
        # Check passenger data
        passengers = result["Query"]["Passengers"]["Passenger"]
        assert len(passengers) == 1, "Should have 1 passenger"
        assert passengers[0]["ObjectKey"] == "PAX1", "Passenger should have ObjectKey PAX1"
        assert passengers[0]["PTC"]["value"] == "ADT", "Passenger should have PTC ADT"
        
        # Check payment data
        payments = result["Query"]["Payments"]["Payment"]
        assert len(payments) == 1, "Should have 1 payment"
        assert "Cash" in payments[0]["Method"], "Payment should be Cash"
        
        # Check flight offer items
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        assert len(offer_items) > 0, "Should have flight offer items"
        
        logger.info("✅ Real FlightPrice response test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real FlightPrice response test FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_real_seat_selection():
    """Test seat selection using real SeatAvailability data."""
    logger.info("=== Testing Real Seat Selection ===")
    
    try:
        # Load real data
        flight_price_data, seat_availability_data, service_list_data = load_real_api_data()
        
        # Extract the actual response from the wrapper
        flight_price_response = flight_price_data["response"]
        seatavailability_response = seat_availability_data["response"]
        servicelist_response = service_list_data["response"]
        
        # Test data - select a real seat from the response
        passengers_data = create_real_passenger_data()
        payment_info = create_real_payment_info()
        selected_seats = ["PRICE4-SEG2"]  # This is a real pricing ObjectKey from the response
        selected_services = []
        
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response,
            selected_seats=selected_seats,
            selected_services=selected_services
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        
        # Check if seat service was added
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) > 0, "Should have at least one seat item"
        
        # Check if the seat service uses the pricing ObjectKey
        seat_item = seat_items[0]
        assert seat_item["OfferItemID"]["value"] == "PRICE4-SEG2", "OfferItemID should be PRICE4-SEG2"
        
        # Check if the seat has pricing information
        seat_details = seat_item["OfferItemType"]["SeatItem"][0]
        assert "Price" in seat_details, "Seat should have price information"
        
        # Check if the seat has location information (should be found from reverse mapping)
        assert "Location" in seat_details, "Seat should have location information"
        location = seat_details["Location"]
        # PRICE4-SEG2 maps to multiple seats including row 17, so expect row 17 (first match)
        assert location.get("Row", {}).get("Number", {}).get("value") == "17", "Row should be 17 (first match for PRICE4-SEG2)"
        assert location.get("Column") in ["A", "B", "G", "H"], "Column should be A, B, G, or H (from row 17)"
        
        logger.info("✅ Real seat selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real seat selection test FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_real_seat_position_selection():
    """Test seat selection using actual seat positions from real data."""
    logger.info("=== Testing Real Seat Position Selection ===")
    
    try:
        # Load real data
        flight_price_data, seat_availability_data, service_list_data = load_real_api_data()
        
        # Extract the actual response from the wrapper
        flight_price_response = flight_price_data["response"]
        seatavailability_response = seat_availability_data["response"]
        servicelist_response = service_list_data["response"]
        
        # Test data - select a real seat position from the response
        passengers_data = create_real_passenger_data()
        payment_info = create_real_payment_info()
        selected_seats = ["33H"]  # This is a real seat position from the response
        selected_services = []
        
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response,
            selected_seats=selected_seats,
            selected_services=selected_services
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        
        # Check if seat service was added
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) > 0, "Should have at least one seat item"
        
        # Check if the seat has location information
        seat_item = seat_items[0]
        seat_details = seat_item["OfferItemType"]["SeatItem"][0]
        
        assert "Location" in seat_details, "Seat should have location information"
        location = seat_details["Location"]
        assert location.get("Row", {}).get("Number", {}).get("value") == "33", "Row should be 33"
        assert location.get("Column") == "H", "Column should be H"
        
        logger.info("✅ Real seat position selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real seat position selection test FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_real_mixed_seat_selection():
    """Test mixed seat selection using both seat positions and pricing ObjectKeys from real data."""
    logger.info("=== Testing Real Mixed Seat Selection ===")
    
    try:
        # Load real data
        flight_price_data, seat_availability_data, service_list_data = load_real_api_data()
        
        # Extract the actual response from the wrapper
        flight_price_response = flight_price_data["response"]
        seatavailability_response = seat_availability_data["response"]
        servicelist_response = service_list_data["response"]
        
        # Test data - mix of both types from real data
        passengers_data = create_real_passenger_data()
        payment_info = create_real_payment_info()
        selected_seats = ["33H", "PRICE1-SEG2"]  # Seat position + Pricing ObjectKey from real data
        selected_services = []
        
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response,
            selected_seats=selected_seats,
            selected_services=selected_services
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        
        # Check if seat services were added
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) >= 2, "Should have at least two seat items"
        
        # Check if both types of seats are handled
        seat_ids = [item["OfferItemID"]["value"] for item in seat_items]
        
        # For seat position "33H", it gets converted to "PRICE4-SEG2" (its pricing ref)
        # For pricing ObjectKey "PRICE1-SEG2", it gets used directly
        assert "PRICE4-SEG2" in seat_ids, "Should have PRICE4-SEG2 (from seat 33H)"
        assert "PRICE1-SEG2" in seat_ids, "Should have PRICE1-SEG2 (direct pricing ObjectKey)"
        
        logger.info("✅ Real mixed seat selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real mixed seat selection test FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_real_data_structure_validation():
    """Test that the generated OrderCreate structure matches expected format."""
    logger.info("=== Testing Real Data Structure Validation ===")
    
    try:
        # Load real data
        flight_price_data, seat_availability_data, service_list_data = load_real_api_data()
        
        # Extract the actual response from the wrapper
        flight_price_response = flight_price_data["response"]
        seatavailability_response = seat_availability_data["response"]
        servicelist_response = service_list_data["response"]
        
        # Test data
        passengers_data = create_real_passenger_data()
        payment_info = create_real_payment_info()
        selected_seats = ["PRICE4-SEG2"]
        selected_services = []
        
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            servicelist_response=servicelist_response,
            selected_seats=selected_seats,
            selected_services=selected_services
        )
        
        # Verify the complete structure
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        
        # Check all required sections exist
        required_sections = ["Passengers", "OrderItems", "DataLists", "Metadata", "Payments"]
        for section in required_sections:
            assert section in result["Query"], f"Result should have {section} section"
        
        # Check DataLists structure
        data_lists = result["Query"]["DataLists"]
        assert "FareList" in data_lists, "DataLists should have FareList"
        assert "ServiceList" in data_lists, "DataLists should have ServiceList"
        
        # Check OrderItems structure
        order_items = result["Query"]["OrderItems"]
        assert "ShoppingResponse" in order_items, "OrderItems should have ShoppingResponse"
        assert "OfferItem" in order_items, "OrderItems should have OfferItem array"
        
        # Check ShoppingResponse structure
        shopping_response = order_items["ShoppingResponse"]
        assert "Owner" in shopping_response, "ShoppingResponse should have Owner"
        assert "ResponseID" in shopping_response, "ShoppingResponse should have ResponseID"
        assert "Offers" in shopping_response, "ShoppingResponse should have Offers"
        
        # Check that Owner is extracted from response (should be "KQ")
        assert shopping_response["Owner"] == "KQ", "Owner should be extracted from response (KQ)"
        
        logger.info("✅ Real data structure validation test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real data structure validation test FAILED: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def run_all_real_data_tests():
    """Run all tests using real API data and report results."""
    logger.info("🚀 Starting build_ordercreate_rq.py tests with REAL API data...")
    
    tests = [
        test_real_flight_price_response,
        test_real_seat_selection,
        test_real_seat_position_selection,
        test_real_mixed_seat_selection,
        test_real_data_structure_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    logger.info(f"\n📊 Real Data Test Results:")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        logger.info("🎉 All real data tests passed! build_ordercreate_rq.py is working correctly with real API data.")
    else:
        logger.error("💥 Some real data tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_real_data_tests()
    sys.exit(0 if success else 1)
