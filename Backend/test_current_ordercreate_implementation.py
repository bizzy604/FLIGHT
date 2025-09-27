#!/usr/bin/env python3
"""
Test to verify if our current OrderCreate implementation uses the priced FlightPriceRS response
when PricedInd=false scenarios are detected.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq
from build_flightprice_ancillary_rq import detect_pricing_required

def load_workflow_data():
    """Load the complete workflow data."""
    try:
        workflow_dir = "Shopping and booking with Seat and Ancillary where both of them requires pricing"
        
        # Load initial FlightPrice response (before ancillary pricing)
        with open(f'{workflow_dir}/4_FlightPriceRS.json', 'r') as f:
            initial_flight_price = json.load(f)
        
        # Load priced FlightPrice response (after ancillary pricing)
        with open(f'{workflow_dir}/10_FlightPriceRS.json', 'r') as f:
            priced_flight_price = json.load(f)
        
        # Load ServiceList and SeatAvailability responses
        with open(f'{workflow_dir}/6_ServiceListRS.json', 'r') as f:
            servicelist_response = json.load(f)
        
        with open(f'{workflow_dir}/8_SeatAvailabilityRS.json', 'r') as f:
            seatavailability_response = json.load(f)
        
        return {
            'initial_flight_price': initial_flight_price,
            'priced_flight_price': priced_flight_price,
            'servicelist_response': servicelist_response,
            'seatavailability_response': seatavailability_response
        }
    
    except Exception as e:
        print(f"Error loading workflow data: {e}")
        return None

def test_pricing_detection():
    """Test pricing detection with real data."""
    print("=" * 80)
    print("TESTING PRICING DETECTION")
    print("=" * 80)
    
    data = load_workflow_data()
    if not data:
        return False
    
    # Find services and seats with PricedInd=false
    services = data['servicelist_response'].get('Services', {}).get('Service', [])
    priced_false_services = [s.get('ObjectKey') for s in services if not s.get('PricedInd', True)]
    
    seat_services = data['seatavailability_response'].get('Services', {}).get('Service', [])
    priced_false_seats = [s.get('ObjectKey') for s in seat_services if not s.get('PricedInd', True)]
    
    print(f"Found {len(priced_false_services)} services with PricedInd=false")
    print(f"Found {len(priced_false_seats)} seats with PricedInd=false")
    
    # Test pricing detection
    selected_services = priced_false_services[:2]  # Take first 2
    selected_seats = priced_false_seats[:1]       # Take first 1
    
    pricing_info = detect_pricing_required(
        servicelist_response=data['servicelist_response'],
        seatavailability_response=data['seatavailability_response'],
        selected_services=selected_services,
        selected_seats=selected_seats
    )
    
    print(f"\nPricing Detection Results:")
    print(f"  Requires pricing: {pricing_info['requires_pricing']}")
    print(f"  Services requiring pricing: {pricing_info['services_require_pricing']}")
    print(f"  Seats requiring pricing: {pricing_info['seats_require_pricing']}")
    
    return pricing_info['requires_pricing'], selected_services, selected_seats

def test_ordercreate_with_initial_response(data, selected_services, selected_seats):
    """Test OrderCreate using initial FlightPriceRS response."""
    print("\n" + "=" * 80)
    print("TESTING ORDERCREATE WITH INITIAL FLIGHTPRICERS")
    print("=" * 80)
    
    # Create test passenger data
    passengers_data = [{
        "ObjectKey": "PAX1",
        "PTC": "ADT",
        "Name": {
            "Surname": "DOE",
            "Given": ["JON"],
            "Title": "Mr"
        },
        "Gender": "Male",
        "BirthDate": "1990-01-01",
        "Contacts": {
            "AddressContact": {
                "Street": ["123 Main St"],
                "CityName": "Test City",
                "CountrySubDivisionCode": "TS",
                "PostalCode": "12345",
                "CountryCode": {"value": "US"}
            },
            "EmailContact": {
                "Address": {"value": "test@example.com"}
            },
            "PhoneContact": {
                "Application": "Home",
                "Number": [{
                    "value": "1234567890",
                    "CountryCode": "1"
                }]
            }
        },
        "Documents": [{
            "Type": "P",
            "ID": "A1234567",
            "DateOfExpiration": "2030-01-01",
            "CountryOfIssuance": "US"
        }]
    }]
    
    payment_data = {"MethodType": "Cash"}
    
    try:
        # Test with INITIAL FlightPriceRS response
        order_create_rq = generate_order_create_rq(
            flight_price_response=data['initial_flight_price'],  # Use INITIAL response
            passengers_data=passengers_data,
            payment_input_info=payment_data,
            servicelist_response=data['servicelist_response'],
            seatavailability_response=data['seatavailability_response'],
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print("✅ Successfully generated OrderCreate with INITIAL FlightPriceRS!")
        
        # Analyze the generated OrderCreate
        query = order_create_rq.get('Query', {})
        order_items = query.get('OrderItems', {})
        shopping_response = order_items.get('ShoppingResponse', {})
        offers = shopping_response.get('Offers', {}).get('Offer', [])
        
        if offers:
            offer_items = offers[0].get('OfferItems', {}).get('OfferItem', [])
            print(f"\n📊 OrderCreate Structure (using INITIAL response):")
            print(f"  Shopping Response Offer Items: {len(offer_items)}")
            
            for item in offer_items:
                offer_item_id = item.get('OfferItemID', {})
                print(f"    - {offer_item_id.get('value', 'N/A')} (Owner: {offer_item_id.get('Owner', 'N/A')})")
        
        # Additional OfferItems
        additional_offer_items = order_items.get('OfferItem', [])
        print(f"  Additional Offer Items: {len(additional_offer_items)}")
        
        return order_create_rq
        
    except Exception as e:
        print(f"❌ Error generating OrderCreate with initial response: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_ordercreate_with_priced_response(data, selected_services, selected_seats):
    """Test OrderCreate using priced FlightPriceRS response."""
    print("\n" + "=" * 80)
    print("TESTING ORDERCREATE WITH PRICED FLIGHTPRICERS")
    print("=" * 80)
    
    # Create test passenger data
    passengers_data = [{
        "ObjectKey": "PAX1",
        "PTC": "ADT",
        "Name": {
            "Surname": "DOE",
            "Given": ["JON"],
            "Title": "Mr"
        },
        "Gender": "Male",
        "BirthDate": "1990-01-01",
        "Contacts": {
            "AddressContact": {
                "Street": ["123 Main St"],
                "CityName": "Test City",
                "CountrySubDivisionCode": "TS",
                "PostalCode": "12345",
                "CountryCode": {"value": "US"}
            },
            "EmailContact": {
                "Address": {"value": "test@example.com"}
            },
            "PhoneContact": {
                "Application": "Home",
                "Number": [{
                    "value": "1234567890",
                    "CountryCode": "1"
                }]
            }
        },
        "Documents": [{
            "Type": "P",
            "ID": "A1234567",
            "DateOfExpiration": "2030-01-01",
            "CountryOfIssuance": "US"
        }]
    }]
    
    payment_data = {"MethodType": "Cash"}
    
    try:
        # Test with PRICED FlightPriceRS response
        order_create_rq = generate_order_create_rq(
            flight_price_response=data['priced_flight_price'],  # Use PRICED response
            passengers_data=passengers_data,
            payment_input_info=payment_data,
            servicelist_response=data['servicelist_response'],
            seatavailability_response=data['seatavailability_response'],
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print("✅ Successfully generated OrderCreate with PRICED FlightPriceRS!")
        
        # Analyze the generated OrderCreate
        query = order_create_rq.get('Query', {})
        order_items = query.get('OrderItems', {})
        shopping_response = order_items.get('ShoppingResponse', {})
        offers = shopping_response.get('Offers', {}).get('Offer', [])
        
        if offers:
            offer_items = offers[0].get('OfferItems', {}).get('OfferItem', [])
            print(f"\n📊 OrderCreate Structure (using PRICED response):")
            print(f"  Shopping Response Offer Items: {len(offer_items)}")
            
            for item in offer_items:
                offer_item_id = item.get('OfferItemID', {})
                print(f"    - {offer_item_id.get('value', 'N/A')} (Owner: {offer_item_id.get('Owner', 'N/A')})")
        
        # Additional OfferItems
        additional_offer_items = order_items.get('OfferItem', [])
        print(f"  Additional Offer Items: {len(additional_offer_items)}")
        
        return order_create_rq
        
    except Exception as e:
        print(f"❌ Error generating OrderCreate with priced response: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_ordercreate_results(initial_result, priced_result):
    """Compare OrderCreate results from initial vs priced responses."""
    print("\n" + "=" * 80)
    print("COMPARING ORDERCREATE RESULTS")
    print("=" * 80)
    
    if not initial_result or not priced_result:
        print("❌ Cannot compare - one or both results failed")
        return
    
    # Compare shopping response offer items
    initial_offers = initial_result.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {}).get('Offers', {}).get('Offer', [])
    priced_offers = priced_result.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {}).get('Offers', {}).get('Offer', [])
    
    if initial_offers and priced_offers:
        initial_items = initial_offers[0].get('OfferItems', {}).get('OfferItem', [])
        priced_items = priced_offers[0].get('OfferItems', {}).get('OfferItem', [])
        
        print(f"Initial response offer items: {len(initial_items)}")
        print(f"Priced response offer items: {len(priced_items)}")
        
        if len(priced_items) > len(initial_items):
            print("✅ Priced response produces MORE offer items (includes ancillaries)")
        else:
            print("⚠️  Priced response doesn't produce more offer items")
    
    # Compare additional offer items
    initial_additional = initial_result.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
    priced_additional = priced_result.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
    
    print(f"Initial response additional items: {len(initial_additional)}")
    print(f"Priced response additional items: {len(priced_additional)}")

def main():
    """Test current OrderCreate implementation."""
    print("🔍 TESTING CURRENT ORDERCREATE IMPLEMENTATION")
    print("=" * 80)
    
    # Load data
    data = load_workflow_data()
    if not data:
        print("❌ Failed to load workflow data")
        return
    
    print("✅ Loaded workflow data")
    
    # Test pricing detection
    requires_pricing, selected_services, selected_seats = test_pricing_detection()
    
    if not requires_pricing:
        print("❌ No pricing required - cannot test PricedInd=false scenario")
        return
    
    # Test OrderCreate with initial response
    initial_result = test_ordercreate_with_initial_response(data, selected_services, selected_seats)
    
    # Test OrderCreate with priced response
    priced_result = test_ordercreate_with_priced_response(data, selected_services, selected_seats)
    
    # Compare results
    compare_ordercreate_results(initial_result, priced_result)
    
    # Final analysis
    print("\n" + "=" * 80)
    print("FINAL ANALYSIS")
    print("=" * 80)
    
    if initial_result and priced_result:
        print("✅ Both OrderCreate generations succeeded")
        print("✅ Current implementation can use both initial and priced responses")
        print("\n🎯 RECOMMENDATION: For PricedInd=false scenarios, use the PRICED FlightPriceRS response!")
    else:
        print("❌ OrderCreate generation failed")

if __name__ == "__main__":
    main()
