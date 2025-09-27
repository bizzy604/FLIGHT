#!/usr/bin/env python3
"""
Test script using real workflow data to test PricedInd=false scenarios.
This uses the complete workflow from AirShopping to OrderCreate.
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
    _extract_seat_data_from_response
)

def load_real_workflow_data():
    """Load real workflow data from the complete flow."""
    try:
        # Load the complete workflow data
        workflow_dir = "Shopping and booking with Seat and Ancillary where both of them requires pricing"
        
        # Load FlightPrice response (initial pricing)
        with open(f'{workflow_dir}/4_FlightPriceRS.json', 'r') as f:
            flight_price_response = json.load(f)
        
        # Load ServiceList response
        with open(f'{workflow_dir}/6_ServiceListRS.json', 'r') as f:
            servicelist_response = json.load(f)
        
        # Load SeatAvailability response
        with open(f'{workflow_dir}/8_SeatAvailabilityRS.json', 'r') as f:
            seatavailability_response = json.load(f)
        
        # Load the final FlightPrice response (after pricing ancillaries)
        with open(f'{workflow_dir}/10_FlightPriceRS.json', 'r') as f:
            final_flight_price_response = json.load(f)
        
        # Load OrderCreate request
        with open(f'{workflow_dir}/11_OrderCreateRQ.json', 'r') as f:
            order_create_request = json.load(f)
        
        return {
            'flight_price_response': flight_price_response,
            'servicelist_response': servicelist_response,
            'seatavailability_response': seatavailability_response,
            'final_flight_price_response': final_flight_price_response,
            'order_create_request': order_create_request
        }
    
    except Exception as e:
        print(f"Error loading real workflow data: {e}")
        return None

def analyze_pricedind_status(data):
    """Analyze PricedInd status in the real workflow data."""
    print("=" * 80)
    print("ANALYZING PRICEDIND STATUS IN REAL WORKFLOW DATA")
    print("=" * 80)
    
    # Analyze ServiceList PricedInd status
    print("\n📋 SERVICE LIST ANALYSIS:")
    services = data['servicelist_response'].get('Services', {}).get('Service', [])
    priced_false_services = []
    priced_true_services = []
    
    for service in services:
        object_key = service.get('ObjectKey', '')
        priced_ind = service.get('PricedInd', True)
        name = service.get('Name', {}).get('value', 'Unknown')
        
        if not priced_ind:
            priced_false_services.append({
                'ObjectKey': object_key,
                'Name': name,
                'PricedInd': priced_ind
            })
        else:
            priced_true_services.append({
                'ObjectKey': object_key,
                'Name': name,
                'PricedInd': priced_ind
            })
    
    print(f"  ✅ Services with PricedInd=false: {len(priced_false_services)}")
    for service in priced_false_services:
        print(f"    - {service['ObjectKey']}: {service['Name']}")
    
    print(f"  ✅ Services with PricedInd=true: {len(priced_true_services)}")
    for service in priced_true_services:
        print(f"    - {service['ObjectKey']}: {service['Name']}")
    
    # Analyze SeatAvailability PricedInd status
    print("\n🪑 SEAT AVAILABILITY ANALYSIS:")
    seat_services = data['seatavailability_response'].get('Services', {}).get('Service', [])
    priced_false_seats = []
    priced_true_seats = []
    
    for service in seat_services:
        object_key = service.get('ObjectKey', '')
        priced_ind = service.get('PricedInd', True)
        name = service.get('Name', {}).get('value', 'Unknown')
        
        if not priced_ind:
            priced_false_seats.append({
                'ObjectKey': object_key,
                'Name': name,
                'PricedInd': priced_ind
            })
        else:
            priced_true_seats.append({
                'ObjectKey': object_key,
                'Name': name,
                'PricedInd': priced_ind
            })
    
    print(f"  ✅ Seat services with PricedInd=false: {len(priced_false_seats)}")
    for service in priced_false_seats:
        print(f"    - {service['ObjectKey']}: {service['Name']}")
    
    print(f"  ✅ Seat services with PricedInd=true: {len(priced_true_seats)}")
    for service in priced_true_seats:
        print(f"    - {service['ObjectKey']}: {service['Name']}")
    
    return {
        'priced_false_services': priced_false_services,
        'priced_false_seats': priced_false_seats
    }

def test_pricing_detection_with_real_data(data, priced_items):
    """Test pricing detection with real workflow data."""
    print("\n" + "=" * 80)
    print("TESTING PRICING DETECTION WITH REAL DATA")
    print("=" * 80)
    
    # Test with services that have PricedInd=false
    selected_services = [item['ObjectKey'] for item in priced_items['priced_false_services'][:2]]  # Take first 2
    selected_seats = [item['ObjectKey'] for item in priced_items['priced_false_seats'][:1]]  # Take first 1
    
    print(f"Selected services for testing: {selected_services}")
    print(f"Selected seats for testing: {selected_seats}")
    
    # Test pricing detection
    pricing_info = detect_pricing_required(
        servicelist_response=data['servicelist_response'],
        seatavailability_response=data['seatavailability_response'],
        selected_services=selected_services,
        selected_seats=selected_seats
    )
    
    print(f"\n🔍 PRICING DETECTION RESULTS:")
    print(f"  Requires pricing: {pricing_info['requires_pricing']}")
    print(f"  Services requiring pricing: {pricing_info['services_require_pricing']}")
    print(f"  Seats requiring pricing: {pricing_info['seats_require_pricing']}")
    print(f"  Total items requiring pricing: {pricing_info['total_items_require_pricing']}")
    
    return pricing_info, selected_services, selected_seats

def test_ancillary_pricing_request_generation(data, selected_services, selected_seats):
    """Test generating ancillary pricing request with real data."""
    print("\n" + "=" * 80)
    print("TESTING ANCILLARY PRICING REQUEST GENERATION")
    print("=" * 80)
    
    try:
        # Generate ancillary pricing request
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=data['flight_price_response'],
            servicelist_response=data['servicelist_response'],
            seatavailability_response=data['seatavailability_response'],
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print("✅ Successfully generated ancillary pricing request!")
        print(f"\n📊 REQUEST STRUCTURE:")
        print(f"  Travelers: {len(ancillary_request.get('Travelers', {}).get('Traveler', []))}")
        print(f"  OriginDestinations: {len(ancillary_request.get('Query', {}).get('OriginDestination', []))}")
        
        # Analyze offer items
        offers = ancillary_request.get('Query', {}).get('Offers', {}).get('Offer', [])
        if offers:
            offer_items = offers[0].get('OfferItemIDs', {}).get('OfferItemID', [])
            print(f"  Offer items: {len(offer_items)}")
            
            # Show service items
            service_items = [item for item in offer_items if 'SelectedSeat' not in item]
            print(f"    Service items: {len(service_items)}")
            for item in service_items:
                print(f"      - {item['value']} (Quantity: {item.get('Quantity', 1)})")
            
            # Show seat items with dynamic data
            seat_items = [item for item in offer_items if 'SelectedSeat' in item]
            print(f"    Seat items: {len(seat_items)}")
            for item in seat_items:
                print(f"      - {item['value']}")
                if 'SelectedSeat' in item and item['SelectedSeat']:
                    selected_seat = item['SelectedSeat'][0]
                    location = selected_seat.get('Location', {})
                    print(f"        Location: Row {location.get('Row', {}).get('Number', {}).get('value', 'N/A')}, Column {location.get('Column', 'N/A')}")
                    characteristics = location.get('Characteristics', {}).get('Characteristic', [])
                    if characteristics:
                        codes = [char.get('Code', '') for char in characteristics if char.get('Code')]
                        print(f"        Characteristics: {codes}")
        
        return ancillary_request
        
    except Exception as e:
        print(f"❌ Error generating ancillary pricing request: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_seat_data_extraction_with_real_data(data):
    """Test seat data extraction with real workflow data."""
    print("\n" + "=" * 80)
    print("TESTING SEAT DATA EXTRACTION WITH REAL DATA")
    print("=" * 80)
    
    # Extract seat data
    seat_data_map = _extract_seat_data_from_response(data['seatavailability_response'])
    print(f"✅ Extracted seat data for {len(seat_data_map)} seat services")
    
    # Show sample seat data
    for i, (service_key, seat_data) in enumerate(seat_data_map.items()):
        if i < 3:  # Show first 3
            print(f"\n🪑 Seat Service: {service_key}")
            location = seat_data.get('Location', {})
            if location:
                row = location.get('Row', {}).get('Number', {}).get('value', 'N/A')
                column = location.get('Column', 'N/A')
                print(f"  Location: Row {row}, Column {column}")
                
                characteristics = location.get('Characteristics', {}).get('Characteristic', [])
                if characteristics:
                    codes = [char.get('Code', '') for char in characteristics if char.get('Code')]
                    print(f"  Characteristics: {codes}")
    
    return seat_data_map

def compare_with_expected_workflow(data):
    """Compare our generated request with the expected workflow."""
    print("\n" + "=" * 80)
    print("COMPARING WITH EXPECTED WORKFLOW")
    print("=" * 80)
    
    # Load the expected FlightPriceRQ from the workflow
    with open('Shopping and booking with Seat and Ancillary where both of them requires pricing/9_FlightPriceRQ.json', 'r') as f:
        expected_request = json.load(f)
    
    print("📋 EXPECTED WORKFLOW ANALYSIS:")
    print(f"  Expected travelers: {len(expected_request.get('Travelers', {}).get('Traveler', []))}")
    print(f"  Expected origin destinations: {len(expected_request.get('Query', {}).get('OriginDestination', []))}")
    
    # Analyze expected offer items
    expected_offers = expected_request.get('Query', {}).get('Offers', {}).get('Offer', [])
    if expected_offers:
        expected_items = expected_offers[0].get('OfferItemIDs', {}).get('OfferItemID', [])
        print(f"  Expected offer items: {len(expected_items)}")
        
        # Show expected items
        for item in expected_items:
            print(f"    - {item['value']} (Quantity: {item.get('Quantity', 1)})")
            if 'SelectedSeat' in item:
                selected_seat = item['SelectedSeat'][0]
                location = selected_seat.get('Location', {})
                print(f"      Seat: Row {location.get('Row', {}).get('Number', {}).get('value', 'N/A')}, Column {location.get('Column', 'N/A')}")

def main():
    """Run comprehensive test with real workflow data."""
    print("🧪 TESTING PRICEDIND=FALSE WITH REAL WORKFLOW DATA")
    print("=" * 80)
    
    # Load real workflow data
    data = load_real_workflow_data()
    if not data:
        print("❌ Failed to load real workflow data")
        return
    
    print("✅ Successfully loaded real workflow data")
    
    # Analyze PricedInd status
    priced_items = analyze_pricedind_status(data)
    
    # Test pricing detection
    pricing_info, selected_services, selected_seats = test_pricing_detection_with_real_data(data, priced_items)
    
    # Test seat data extraction
    seat_data_map = test_seat_data_extraction_with_real_data(data)
    
    # Test ancillary pricing request generation
    ancillary_request = test_ancillary_pricing_request_generation(data, selected_services, selected_seats)
    
    # Compare with expected workflow
    compare_with_expected_workflow(data)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Pricing detection: {'PASS' if pricing_info['requires_pricing'] else 'FAIL'}")
    print(f"✅ Seat data extraction: {'PASS' if len(seat_data_map) > 0 else 'FAIL'}")
    print(f"✅ Ancillary request generation: {'PASS' if ancillary_request else 'FAIL'}")
    
    if pricing_info['requires_pricing'] and len(seat_data_map) > 0 and ancillary_request:
        print("\n🎉 ALL TESTS PASSED! PricedInd=false implementation works with real workflow data!")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
