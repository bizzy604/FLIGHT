#!/usr/bin/env python3
"""
Test script to verify FareCode fix in OrderCreate payload generation
"""

import sys
import os
import json

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def test_farecode_fix():
    """Test that FareCode is properly handled (optional instead of null)"""
    
    # Load the flight price response
    flight_price_path = os.path.join(os.path.dirname(__file__), 'flightpriceresponse.json')
    
    try:
        with open(flight_price_path, 'r') as f:
            flight_price_response = json.load(f)
    except FileNotFoundError:
        print(f"❌ Flight price response file not found: {flight_price_path}")
        return False
    
    # Create test passengers
    passengers_data = [
        {
            "PTC": "ADT",
            "Name": {"Given": "John", "Surname": "Doe"},
            "Gender": "Male",
            "Age": 30,
            "Contacts": {"Contact": {"EmailContact": {"Address": "john.doe@example.com"}}}
        },
        {
            "PTC": "ADT",
            "Name": {"Given": "Jane", "Surname": "Doe"},
            "Gender": "Female",
            "Age": 28,
            "Contacts": {"Contact": {"EmailContact": {"Address": "jane.doe@example.com"}}}
        }
    ]
    
    # Create test payment
    payment_data = {
        "Amount": {"Value": 1000, "Code": "USD"},
        "Method": "Cash"
    }
    
    try:
        # Generate OrderCreate request
        order_create_rq = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )
        
        # Check FareList structure
        fare_list = order_create_rq.get('Query', {}).get('DataLists', {}).get('FareList', {})
        fare_groups = fare_list.get('FareGroup', [])
        
        print("\n🔍 TESTING FARECODE FIX")
        print("=" * 50)
        
        success = True
        for i, fare_group in enumerate(fare_groups):
            print(f"\nFareGroup {i + 1}:")
            print(f"  ListKey: {fare_group.get('ListKey')}")
            print(f"  FareBasisCode: {fare_group.get('FareBasisCode')}")
            
            # Check if Fare object exists
            if 'Fare' in fare_group:
                fare_code = fare_group['Fare'].get('FareCode')
                print(f"  FareCode: {fare_code}")
                if fare_code is None:
                    print(f"  ⚠️  FareCode is null - this should be optional instead")
                    success = False
                else:
                    print(f"  ✓ FareCode has value: {fare_code}")
            else:
                print(f"  ✓ Fare object omitted (good - FareCode is optional)")
        
        # Save the generated payload for inspection
        output_path = os.path.join(os.path.dirname(__file__), 'test_farecode_output.json')
        with open(output_path, 'w') as f:
            json.dump(order_create_rq, f, indent=2)
        
        print(f"\n📄 Generated payload saved to: {output_path}")
        
        if success:
            print("\n✅ FareCode fix test PASSED!")
            return True
        else:
            print("\n❌ FareCode fix test FAILED!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error generating OrderCreate request: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_farecode_fix()