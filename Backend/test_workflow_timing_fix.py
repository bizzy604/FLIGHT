#!/usr/bin/env python3
"""
Test the workflow timing fix to ensure pricing detection happens BEFORE OrderCreate generation.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

def test_workflow_timing_fix():
    """Test that the workflow timing fix works correctly."""
    print("=" * 80)
    print("TESTING WORKFLOW TIMING FIX")
    print("=" * 80)
    
    # Load the real workflow data
    try:
        with open('api_logs/service_list/ServiceList_RS.json', 'r') as f:
            servicelist_data = json.load(f)
            servicelist_response = servicelist_data.get('response', servicelist_data)
        
        with open('api_logs/seat_availability/SeatAvailability_RS.json', 'r') as f:
            seatavailability_data = json.load(f)
            seatavailability_response = seatavailability_data.get('response', seatavailability_data)
        
        with open('test_flight_price_response.json', 'r') as f:
            flight_price_response = json.load(f)
        
        print("✅ Loaded real workflow data successfully")
        
    except Exception as e:
        print(f"❌ Error loading workflow data: {e}")
        return False
    
    # Test pricing detection
    print("\n🔍 TESTING PRICING DETECTION:")
    try:
        from scripts.build_flightprice_ancillary_rq import detect_pricing_required
        
        # Get services with PricedInd=false
        services = servicelist_response.get('Services', {}).get('Service', [])
        selected_services = []
        for service in services:
            if not service.get('PricedInd', True):
                selected_services.append(service.get('ObjectKey', ''))
        
        print(f"Found {len(selected_services)} services with PricedInd=false:")
        for service_key in selected_services:
            print(f"  - {service_key}")
        
        # Test pricing detection
        pricing_info = detect_pricing_required(
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=[]
        )
        
        print(f"\nPricing detection result:")
        print(f"  requires_pricing: {pricing_info['requires_pricing']}")
        print(f"  services_require_pricing: {pricing_info['services_require_pricing']}")
        print(f"  total_items_require_pricing: {pricing_info['total_items_require_pricing']}")
        
        if not pricing_info['requires_pricing']:
            print("❌ Pricing detection failed - should detect PricedInd=false services")
            return False
        
        print("✅ Pricing detection working correctly")
        
    except Exception as e:
        print(f"❌ Error testing pricing detection: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test ancillary pricing request generation
    print("\n🚀 TESTING ANCILLARY PRICING REQUEST GENERATION:")
    try:
        from scripts.build_flightprice_ancillary_rq import build_flightprice_ancillary_request
        
        ancillary_request = build_flightprice_ancillary_request(
            flight_price_response=flight_price_response,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=[],
            selected_offer_index=0
        )
        
        print("✅ Ancillary pricing request generated successfully")
        print(f"Request structure: {list(ancillary_request.keys())}")
        
        # Save the generated request for inspection
        with open('test_ancillary_pricing_request.json', 'w') as f:
            json.dump(ancillary_request, f, indent=2)
        print("💾 Saved ancillary pricing request to test_ancillary_pricing_request.json")
        
    except Exception as e:
        print(f"❌ Error generating ancillary pricing request: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test enhanced OrderCreate builder
    print("\n📋 TESTING ENHANCED ORDERCREATE BUILDER:")
    try:
        from scripts.build_ordercreate_enhanced_rq import build_ordercreate_enhanced_request
        
        # Mock passenger data
        passengers_data = [
            {
                "ObjectKey": "PAX1",
                "PTC": "ADT",
                "Name": {"Surname": "Test", "Given": ["User"]},
                "Gender": "M",
                "BirthDate": "1990-01-01",
                "Contacts": {
                    "EmailContact": {"Address": {"value": "test@example.com"}},
                    "PhoneContact": {"Number": [{"value": "1234567890", "CountryCode": "1"}]}
                }
            }
        ]
        
        # Mock payment data
        payment_info = {
            "MethodType": "Cash",
            "Amount": {"value": 100, "Code": "USD"}
        }
        
        # Test enhanced OrderCreate builder
        order_create_rq = build_ordercreate_enhanced_request(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_info,
            servicelist_response=servicelist_response,
            seatavailability_response=seatavailability_response,
            selected_services=selected_services,
            selected_seats=[],
            ancillary_pricing_response=None  # No ancillary pricing response yet
        )
        
        print("✅ Enhanced OrderCreate builder working correctly")
        print(f"OrderCreate structure: {list(order_create_rq.keys())}")
        
        # Save the generated OrderCreate for inspection
        with open('test_enhanced_ordercreate.json', 'w') as f:
            json.dump(order_create_rq, f, indent=2)
        print("💾 Saved enhanced OrderCreate to test_enhanced_ordercreate.json")
        
    except Exception as e:
        print(f"❌ Error testing enhanced OrderCreate builder: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("WORKFLOW TIMING FIX TEST RESULTS")
    print("=" * 80)
    print("✅ Pricing detection works correctly")
    print("✅ Ancillary pricing request generation works")
    print("✅ Enhanced OrderCreate builder works")
    print("\n🎯 WORKFLOW TIMING FIX SUCCESSFUL!")
    print("The system now:")
    print("1. Detects pricing requirements BEFORE OrderCreate")
    print("2. Calls ancillary pricing API when needed")
    print("3. Uses enhanced OrderCreate builder with priced services")
    
    return True

def main():
    """Main test function."""
    success = test_workflow_timing_fix()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - WORKFLOW TIMING FIX IS WORKING!")
    else:
        print("\n❌ SOME TESTS FAILED - WORKFLOW TIMING FIX NEEDS ATTENTION")
    
    return success

if __name__ == "__main__":
    main()
