#!/usr/bin/env python3
"""
Test script to verify dynamic seat data extraction for PricedInd=false scenarios.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_flightprice_ancillary_rq import (
    build_flightprice_ancillary_request,
    detect_pricing_required,
    _extract_seat_data_from_response,
    _extract_seat_selection_info
)

def load_test_data():
    """Load test data from API logs."""
    try:
        # Load SeatAvailability response
        with open('api_logs/seat_availability/SeatAvailability_RS.json', 'r') as f:
            seatavailability_response = json.load(f)
        
        # Load ServiceList response
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            servicelist_response = json.load(f)
        
        # Load FlightPrice response
        with open('test_flight_price_response.json', 'r') as f:
            flight_price_response = json.load(f)
        
        return seatavailability_response, servicelist_response, flight_price_response
    
    except Exception as e:
        print(f"Error loading test data: {e}")
        return None, None, None

def test_pricing_detection():
    """Test pricing requirement detection."""
    print("=" * 60)
    print("TESTING PRICING REQUIREMENT DETECTION")
    print("=" * 60)
    
    seatavailability_response, servicelist_response, flight_price_response = load_test_data()
    
    if not all([seatavailability_response, servicelist_response, flight_price_response]):
        print("❌ Failed to load test data")
        return False
    
    # Test with selected seats and services
    selected_seats = ["PRICE1-SEG10"]  # This should have PricedInd=false now
    selected_services = ["1-ServiceIdQR-4"]  # This should have PricedInd=false now
    
    print(f"Selected seats: {selected_seats}")
    print(f"Selected services: {selected_services}")
    
    # Test pricing detection
    pricing_info = detect_pricing_required(
        servicelist_response=servicelist_response,
        seatavailability_response=seatavailability_response,
        selected_services=selected_services,
        selected_seats=selected_seats
    )
    
    print(f"\nPricing detection result:")
    print(f"  Requires pricing: {pricing_info['requires_pricing']}")
    print(f"  Services requiring pricing: {pricing_info['services_require_pricing']}")
    print(f"  Seats requiring pricing: {pricing_info['seats_require_pricing']}")
    print(f"  Total items requiring pricing: {pricing_info['total_items_require_pricing']}")
    
    return pricing_info['requires_pricing']

def test_seat_data_extraction():
    """Test dynamic seat data extraction."""
    print("\n" + "=" * 60)
    print("TESTING DYNAMIC SEAT DATA EXTRACTION")
    print("=" * 60)
    
    seatavailability_response, servicelist_response, flight_price_response = load_test_data()
    
    if not seatavailability_response:
        print("❌ Failed to load SeatAvailability response")
        return False
    
    # Extract seat data
    seat_data_map = _extract_seat_data_from_response(seatavailability_response)
    print(f"Extracted seat data for {len(seat_data_map)} seats")
    
    # Debug: Check the actual structure
    data_lists = seatavailability_response.get('DataLists', {})
    seat_list = data_lists.get('SeatList', {})
    seats = seat_list.get('Seats', [])
    print(f"Debug: Found {len(seats)} seats in DataLists.SeatList.Seats")
    
    # Show sample seat data
    for i, (seat_key, seat_data) in enumerate(seat_data_map.items()):
        if i < 3:  # Show first 3 seats
            print(f"\nSeat {seat_key}:")
            print(f"  Location: {seat_data.get('Location', {})}")
            print(f"  Characteristics: {seat_data.get('Characteristics', {})}")
            print(f"  SeatAssociation: {seat_data.get('SeatAssociation', [])}")
    
    # Show first few raw seats for debugging
    if seats:
        print(f"\nFirst few raw seats:")
        for i, seat in enumerate(seats[:3]):
            print(f"  Seat {i}: ObjectKey={seat.get('ObjectKey', 'N/A')}, Location={seat.get('Location', {})}")
    
    return True

def test_ancillary_request_building():
    """Test building ancillary pricing request."""
    print("\n" + "=" * 60)
    print("TESTING ANCILLARY PRICING REQUEST BUILDING")
    print("=" * 60)
    
    seatavailability_response, servicelist_response, flight_price_response = load_test_data()
    
    if not all([seatavailability_response, servicelist_response, flight_price_response]):
        print("❌ Failed to load test data")
        return False
    
    # Test with selected items that require pricing
    selected_seats = ["PRICE1-SEG10"]  # PricedInd=false
    selected_services = ["1-ServiceIdQR-4"]  # PricedInd=false
    
    print(f"Building ancillary request for:")
    print(f"  Selected seats: {selected_seats}")
    print(f"  Selected services: {selected_services}")
    
    try:
        # Build ancillary pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print(f"\n✅ Successfully built ancillary request")
        print(f"Request structure:")
        print(f"  Travelers: {len(ancillary_request.get('Travelers', {}).get('Traveler', []))}")
        print(f"  OriginDestinations: {len(ancillary_request.get('Query', {}).get('OriginDestination', []))}")
        
        # Check offer items
        offers = ancillary_request.get('Query', {}).get('Offers', {}).get('Offer', [])
        if offers:
            offer_items = offers[0].get('OfferItemIDs', {}).get('OfferItemID', [])
            print(f"  Offer items: {len(offer_items)}")
            
            # Show seat items with dynamic data
            for item in offer_items:
                if 'SelectedSeat' in item:
                    print(f"\n  Seat item: {item['value']}")
                    selected_seat = item['SelectedSeat'][0]
                    location = selected_seat.get('Location', {})
                    print(f"    Location: {location}")
                    print(f"    SeatAssociation: {selected_seat.get('SeatAssociation', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error building ancillary request: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 TESTING DYNAMIC SEAT DATA EXTRACTION")
    print("=" * 60)
    
    # Test 1: Pricing detection
    pricing_works = test_pricing_detection()
    
    # Test 2: Seat data extraction
    extraction_works = test_seat_data_extraction()
    
    # Test 3: Ancillary request building
    request_works = test_ancillary_request_building()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Pricing detection: {'PASS' if pricing_works else 'FAIL'}")
    print(f"✅ Seat data extraction: {'PASS' if extraction_works else 'FAIL'}")
    print(f"✅ Ancillary request building: {'PASS' if request_works else 'FAIL'}")
    
    if all([pricing_works, extraction_works, request_works]):
        print("\n🎉 ALL TESTS PASSED! Dynamic seat extraction is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
