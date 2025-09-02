#!/usr/bin/env python3
"""
Test file to verify seat selection functionality in OrderCreate request builder.
Tests both seat positions (like "17H") and pricing ObjectKeys (like "PRICE4-SEG2").
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

def create_mock_seatavailability_response():
    """Create a mock seat availability response with seat 17H mapped to PRICE4-SEG2."""
    return {
        "DataLists": {
            "SeatList": {
                "Seats": [
                    {
                        "Location": {
                            "Row": {"Number": {"value": "17"}},
                            "Column": "H"
                        },
                        "refs": ["PRICE4-SEG2"],
                        "Characteristics": {
                            "Characteristic": [
                                {"value": "Window"},
                                {"value": "Exit"}
                            ]
                        }
                    },
                    {
                        "Location": {
                            "Row": {"Number": {"value": "17"}},
                            "Column": "A"
                        },
                        "refs": ["PRICE4-SEG2"],
                        "Characteristics": {
                            "Characteristic": [
                                {"value": "Window"}
                            ]
                        }
                    },
                    {
                        "Location": {
                            "Row": {"Number": {"value": "18"}},
                            "Column": "H"
                        },
                        "refs": ["PRICE1-SEG2"],
                        "Characteristics": {
                            "Characteristic": [
                                {"value": "Aisle"}
                            ]
                        }
                    }
                ]
            }
        },
        "Services": {
            "Service": [
                {
                    "ObjectKey": "PRICE4-SEG2",
                    "Name": {"value": "Premium Seat"},
                    "Price": [{
                        "Total": {"value": 25.00, "Code": "USD"},
                        "Base": {"value": 20.00, "Code": "USD"},
                        "Taxes": {"value": 5.00, "Code": "USD"}
                    }],
                    "Descriptions": {
                        "Description": [
                            {"value": "Premium seat with extra legroom"}
                        ]
                    },
                    "Associations": [
                        {"PassengerRef": "PAX1"}
                    ]
                },
                {
                    "ObjectKey": "PRICE1-SEG2",
                    "Name": {"value": "Standard Seat"},
                    "Price": [{
                        "Total": {"value": 15.00, "Code": "USD"},
                        "Base": {"value": 12.00, "Code": "USD"},
                        "Taxes": {"value": 3.00, "Code": "USD"}
                    }],
                    "Descriptions": {
                        "Description": [
                            {"value": "Standard economy seat"}
                        ]
                    },
                    "Associations": [
                        {"PassengerRef": "PAX1"}
                    ]
                }
            ]
        },
        "ShoppingResponseID": {
            "Owner": "KQ",
            "ResponseID": {"value": "test-response-123"}
        }
    }

def create_mock_flight_price_response():
    """Create a mock flight price response."""
    return {
        "ShoppingResponseID": {
            "ResponseID": {"value": "test-shopping-response-123"}
        },
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": {
                        "value": "test-offer-123",
                        "Owner": "KQ",
                        "Channel": "NDC"
                    },
                    "OfferPrice": [
                        {
                            "OfferItemID": "test-offer-item-1"
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "FareList": {
                "FareGroup": [
                    {
                        "ListKey": "test-fare-group-1",
                        "Fare": {"FareCode": "TEST"},
                        "FareBasisCode": "TEST123"
                    }
                ]
            },
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {"ObjectKey": "PAX1"}
                ]
            }
        }
    }

def create_mock_passengers_data():
    """Create mock passenger data."""
    return [
        {
            "PTC": "ADT",
            "Name": {"Surname": "Test", "Given": "User"},
            "Gender": "M",
            "BirthDate": "1990-01-01",
            "Documents": [],
            "Contacts": [],
            "ObjectKey": "PAX1"
        }
    ]

def create_mock_payment_info():
    """Create mock payment information."""
    return {
        "MethodType": "CASH",
        "currency": "USD",
        "Details": {},
        "CashInd": True
    }

def test_seat_position_selection():
    """Test seat selection using actual seat positions (like '17H')."""
    logger.info("=== Testing Seat Position Selection ===")
    
    # Test data
    selected_seats = ["17H"]  # Actual seat position
    seatavailability_response = create_mock_seatavailability_response()
    flight_price_response = create_mock_flight_price_response()
    passengers_data = create_mock_passengers_data()
    payment_info = create_mock_payment_info()
    
    try:
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        assert "OfferItem" in result["Query"]["OrderItems"], "Result should have OfferItem array"
        
        # Check if seat service was added
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) > 0, "Should have at least one seat item"
        
        # Check if the seat has location information
        seat_item = seat_items[0]
        seat_details = seat_item["OfferItemType"]["SeatItem"][0]
        
        assert "Location" in seat_details, "Seat should have location information"
        location = seat_details["Location"]
        assert location.get("Row", {}).get("Number", {}).get("value") == "17", "Row should be 17"
        assert location.get("Column") == "H", "Column should be H"
        
        logger.info("✅ Seat position selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Seat position selection test FAILED: {e}")
        return False

def test_pricing_objectkey_selection():
    """Test seat selection using pricing ObjectKeys (like 'PRICE4-SEG2')."""
    logger.info("=== Testing Pricing ObjectKey Selection ===")
    
    # Test data
    selected_seats = ["PRICE4-SEG2"]  # Pricing ObjectKey
    seatavailability_response = create_mock_seatavailability_response()
    flight_price_response = create_mock_flight_price_response()
    passengers_data = create_mock_passengers_data()
    payment_info = create_mock_payment_info()
    
    try:
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        assert "OfferItem" in result["Query"]["OrderItems"], "Result should have OfferItem array"
        
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
        assert location.get("Row", {}).get("Number", {}).get("value") == "17", "Row should be 17"
        assert location.get("Column") == "H", "Column should be H"
        
        logger.info("✅ Pricing ObjectKey selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pricing ObjectKey selection test FAILED: {e}")
        return False

def test_mixed_seat_selection():
    """Test seat selection using both seat positions and pricing ObjectKeys."""
    logger.info("=== Testing Mixed Seat Selection ===")
    
    # Test data - mix of both types
    selected_seats = ["17H", "PRICE1-SEG2"]  # Seat position + Pricing ObjectKey
    seatavailability_response = create_mock_seatavailability_response()
    flight_price_response = create_mock_flight_price_response()
    passengers_data = create_mock_passengers_data()
    payment_info = create_mock_payment_info()
    
    try:
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        assert "OfferItem" in result["Query"]["OrderItems"], "Result should have OfferItem array"
        
        # Check if seat services were added
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) >= 2, "Should have at least two seat items"
        
        # Check if both types of seats are handled
        seat_ids = [item["OfferItemID"]["value"] for item in seat_items]
        
        # For seat position "17H", it gets converted to "PRICE4-SEG2" (its pricing ref)
        # For pricing ObjectKey "PRICE1-SEG2", it gets used directly
        assert "PRICE4-SEG2" in seat_ids, "Should have PRICE4-SEG2 (from seat 17H)"
        assert "PRICE1-SEG2" in seat_ids, "Should have PRICE1-SEG2 (direct pricing ObjectKey)"
        
        logger.info("✅ Mixed seat selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Mixed seat selection test FAILED: {e}")
        return False

def test_no_seat_selection():
    """Test the case where no seats are selected."""
    logger.info("=== Testing No Seat Selection ===")
    
    # Test data
    selected_seats = []  # No seats selected
    seatavailability_response = create_mock_seatavailability_response()
    flight_price_response = create_mock_flight_price_response()
    passengers_data = create_mock_passengers_data()
    payment_info = create_mock_payment_info()
    
    try:
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        assert "OfferItem" in result["Query"]["OrderItems"], "Result should have OfferItem array"
        
        # Check that no seat items were added
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        assert len(seat_items) == 0, "Should have no seat items when no seats selected"
        
        logger.info("✅ No seat selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ No seat selection test FAILED: {e}")
        return False

def test_invalid_seat_selection():
    """Test the case where invalid seats are selected."""
    logger.info("=== Testing Invalid Seat Selection ===")
    
    # Test data
    selected_seats = ["INVALID-SEAT", "NONEXISTENT-PRICE"]  # Invalid seats
    seatavailability_response = create_mock_seatavailability_response()
    flight_price_response = create_mock_flight_price_response()
    passengers_data = create_mock_passengers_data()
    payment_info = create_mock_payment_info()
    
    try:
        # Call the function
        result = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            seatavailability_response=seatavailability_response,
            selected_seats=selected_seats
        )
        
        # Verify the result
        assert result is not None, "Result should not be None"
        assert "Query" in result, "Result should have Query section"
        assert "OrderItems" in result["Query"], "Result should have OrderItems"
        assert "OfferItem" in result["Query"]["OrderItems"], "Result should have OfferItem array"
        
        # Check that no seat items were added for invalid seats
        offer_items = result["Query"]["OrderItems"]["OfferItem"]
        seat_items = [item for item in offer_items if "SeatItem" in item.get("OfferItemType", {})]
        
        # Should have no seat items for invalid seats
        assert len(seat_items) == 0, "Should have no seat items for invalid seats"
        
        # Should still have the basic flight offer items (from flight_price_response)
        # These are created in the main function before seat processing
        assert len(offer_items) > 0, "Should have basic offer items from flight price response"
        
        logger.info("✅ Invalid seat selection test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Invalid seat selection test FAILED: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    logger.info("🚀 Starting seat selection integration tests...")
    
    tests = [
        test_seat_position_selection,
        test_pricing_objectkey_selection,
        test_mixed_seat_selection,
        test_no_seat_selection,
        test_invalid_seat_selection
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
    
    logger.info(f"\n📊 Test Results:")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Seat selection functionality is working correctly.")
    else:
        logger.error("💥 Some tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
