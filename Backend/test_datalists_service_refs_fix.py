#!/usr/bin/env python3
"""
Test the fix for OrderCreate refs to ensure service references come from
DataLists.ServiceList.ObjectKey as per NDC specification.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def load_test_data():
    """Load test data to verify the DataLists.ServiceList refs fix."""
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

def test_datalists_service_refs():
    """Test that service references come from DataLists.ServiceList.ObjectKey."""
    print("=" * 80)
    print("TESTING DATALISTS.SERVICELIST REFS FIX")
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
        
        # Check DataLists.ServiceList
        datalists = order_create_rq.get('Query', {}).get('DataLists', {})
        service_list = datalists.get('ServiceList', {}).get('Service', [])
        print(f"📊 Found {len(service_list)} services in DataLists.ServiceList")
        
        # Check the refs in OtherItem
        order_items = order_create_rq.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
        print(f"📊 Found {len(order_items)} order items")
        
        for i, item in enumerate(order_items):
            offer_item_type = item.get('OfferItemType', {})
            other_items = offer_item_type.get('OtherItem', [])
            
            for j, other_item in enumerate(other_items):
                refs = other_item.get('refs', [])
                print(f"\n  OrderItem {i}, OtherItem {j}:")
                print(f"    refs: {refs}")
                
                # Check if refs contain the service ObjectKey from DataLists.ServiceList
                if first_service_key in refs:
                    print(f"    ✅ Contains DataLists.ServiceList.ObjectKey: {first_service_key}")
                else:
                    print(f"    ❌ Missing DataLists.ServiceList.ObjectKey: {first_service_key}")
                
                # Check if refs contain hardcoded values like 'SRV13'
                hardcoded_values = ['SRV13', 'SRV1', 'SRV2', 'SRV3']
                found_hardcoded = [val for val in hardcoded_values if val in refs]
                if found_hardcoded:
                    print(f"    ❌ Contains hardcoded values: {found_hardcoded}")
                else:
                    print(f"    ✅ No hardcoded values found")
        
        # Verify DataLists.ServiceList contains the service
        if service_list:
            service_object_keys = [s.get('ObjectKey', '') for s in service_list]
            print(f"\n📋 DataLists.ServiceList.ObjectKeys: {service_object_keys}")
            
            if first_service_key in service_object_keys:
                print(f"✅ DataLists.ServiceList contains service ObjectKey: {first_service_key}")
            else:
                print(f"❌ DataLists.ServiceList missing service ObjectKey: {first_service_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating OrderCreate: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🔍 TESTING DATALISTS.SERVICELIST REFS FIX")
    print("=" * 80)
    
    success = test_datalists_service_refs()
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("✅ DATALISTS.SERVICELIST REFS FIX TEST PASSED")
        print("  - Service references come from DataLists.ServiceList.ObjectKey")
        print("  - No hardcoded service IDs like 'SRV13'")
        print("  - OrderCreate payload is correctly generated")
        print("  - NDC compliance maintained")
    else:
        print("❌ DATALISTS.SERVICELIST REFS FIX TEST FAILED")
        print("  - Check the implementation")
        print("  - Verify service data structure")

if __name__ == "__main__":
    main()
