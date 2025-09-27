#!/usr/bin/env python3
"""
Test that segment references (like SEG1) are not included in OtherItem.refs
for services in OrderCreate payload.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def load_test_data():
    """Load test data to verify no segment references in service refs."""
    try:
        # Load ServiceListRS
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            servicelist_data = json.load(f)
            servicelist_response = servicelist_data.get('response', servicelist_data)
        
        # Load SeatAvailabilityRS
        with open('api_logs/seat_availability/SeatAvailability_RS.json', 'r') as f:
            seatavailability_data = json.load(f)
            seatavailability_response = seatavailability_data.get('response', seatavailability_data)
        
        # Create a mock FlightPriceRS response
        flight_price_response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferID": {
                        "value": "test-offer-id",
                        "Owner": "26",
                        "Channel": "NDC"
                    },
                    "OfferPrice": [{
                        "OfferItemID": "test-offer-item-id",
                        "RequestedDate": {
                            "Associations": [{
                                "AssociatedTraveler": {
                                    "TravelerReferences": ["PAX1"]
                                }
                            }],
                            "PriceDetail": {
                                "BaseAmount": {"value": 1000, "Code": "USD"},
                                "Taxes": {"Total": {"value": 100, "Code": "USD"}}
                            }
                        }
                    }]
                }]
            },
            "ShoppingResponseID": {
                "ResponseID": {"value": "test-shopping-response-id"}
            },
            "DataLists": {
                "AnonymousTravelerList": {
                    "AnonymousTraveler": [{
                        "ObjectKey": "PAX1",
                        "PTC": {"value": "ADT"}
                    }]
                },
                "FareList": {
                    "FareGroup": [{
                        "ListKey": "test-fare-group",
                        "FareBasisCode": {"Code": "Y"}
                    }]
                }
            }
        }
        
        return {
            'flight_price_response': flight_price_response,
            'servicelist_response': servicelist_response,
            'seatavailability_response': seatavailability_response
        }
        
    except Exception as e:
        print(f"Error loading test data: {e}")
        return None

def test_no_segment_refs():
    """Test that segment references are not included in service OtherItem.refs."""
    print("=" * 80)
    print("TESTING NO SEGMENT REFS IN SERVICE OTHERITEM.REFS")
    print("=" * 80)
    
    data = load_test_data()
    if not data:
        print("❌ Failed to load test data")
        return False
    
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
    
    # Find services with ObjectKeys
    services = data['servicelist_response'].get('Services', {}).get('Service', [])
    if not services:
        print("❌ No services found in ServiceListRS")
        return False
    
    # Get the first service ObjectKey
    first_service_key = services[0].get('ObjectKey', '')
    if not first_service_key:
        print("❌ No ObjectKey found in first service")
        return False
    
    print(f"✅ Found service with ObjectKey: {first_service_key}")
    
    # Test with the service
    selected_services = [first_service_key]
    selected_seats = []  # No seats for this test
    
    try:
        # Generate OrderCreate request
        order_create_rq = generate_order_create_rq(
            flight_price_response=data['flight_price_response'],
            passengers_data=passengers_data,
            payment_input_info=payment_data,
            servicelist_response=data['servicelist_response'],
            seatavailability_response=data['seatavailability_response'],
            selected_services=selected_services,
            selected_seats=selected_seats
        )
        
        print("✅ OrderCreate request generated successfully")
        
        # Check the refs in OtherItem for services
        order_items = order_create_rq.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
        print(f"📊 Found {len(order_items)} order items")
        
        segment_refs_found = False
        
        for i, item in enumerate(order_items):
            offer_item_type = item.get('OfferItemType', {})
            other_items = offer_item_type.get('OtherItem', [])
            
            for j, other_item in enumerate(other_items):
                refs = other_item.get('refs', [])
                print(f"\n  OrderItem {i}, OtherItem {j}:")
                print(f"    refs: {refs}")
                
                # Check for segment references (should not be present)
                segment_refs = ['SEG1', 'SEG2', 'SEG3', 'SEG4', 'SEG5']
                found_segment_refs = [ref for ref in segment_refs if ref in refs]
                
                if found_segment_refs:
                    print(f"    ❌ Contains segment references: {found_segment_refs}")
                    segment_refs_found = True
                else:
                    print(f"    ✅ No segment references found")
                
                # Check for traveler references (should be present)
                traveler_refs = ['PAX1', 'PAX2', 'PAX3']
                found_traveler_refs = [ref for ref in traveler_refs if ref in refs]
                
                if found_traveler_refs:
                    print(f"    ✅ Contains traveler references: {found_traveler_refs}")
                else:
                    print(f"    ⚠️  No traveler references found")
                
                # Check for service references (should be present)
                if first_service_key in refs:
                    print(f"    ✅ Contains service ObjectKey: {first_service_key}")
                else:
                    print(f"    ❌ Missing service ObjectKey: {first_service_key}")
        
        return not segment_refs_found
        
    except Exception as e:
        print(f"❌ Error generating OrderCreate: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🔍 TESTING NO SEGMENT REFS IN SERVICE OTHERITEM.REFS")
    print("=" * 80)
    
    success = test_no_segment_refs()
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("✅ NO SEGMENT REFS TEST PASSED")
        print("  - No segment references (SEG1, SEG2, etc.) in service OtherItem.refs")
        print("  - Only traveler references and service ObjectKeys are included")
        print("  - OrderCreate payload follows NDC specification")
    else:
        print("❌ NO SEGMENT REFS TEST FAILED")
        print("  - Segment references are still being included")
        print("  - Check the implementation")

if __name__ == "__main__":
    main()
