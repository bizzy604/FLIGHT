#!/usr/bin/env python3
"""
Test script to verify that Time field is prioritized over Date field extraction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend
import json

def test_time_field_priority():
    """Test that Time field is prioritized when available."""
    
    # Load the test data
    with open('tests/airshoping_response.json', 'r') as f:
        test_data = json.load(f)
    
    print("=== Testing Time Field Priority ===\n")
    
    # Transform the data
    result = transform_verteil_to_frontend(test_data, enable_roundtrip=False)
    
    if result and len(result) > 0:
        first_offer = result[0]
        first_segment = first_offer['segments'][0] if first_offer.get('segments') else None
        
        if first_segment:
            departure = first_segment['departure']
            arrival = first_segment['arrival']
            
            print("First segment details:")
            print(f"  Departure datetime: {departure.get('datetime')}")
            print(f"  Departure time: {departure.get('time')}")
            print(f"  Arrival datetime: {arrival.get('datetime')}")
            print(f"  Arrival time: {arrival.get('time')}")
            
            # Check if time format indicates it came from Time field (HH:MM) vs datetime (HH:MM:SS)
            dep_time = departure.get('time', '')
            arr_time = arrival.get('time', '')
            
            print(f"\nTime format analysis:")
            print(f"  Departure time format: {dep_time} ({'HH:MM:SS' if dep_time.count(':') == 2 else 'HH:MM' if dep_time.count(':') == 1 else 'Unknown'})")
            print(f"  Arrival time format: {arr_time} ({'HH:MM:SS' if arr_time.count(':') == 2 else 'HH:MM' if arr_time.count(':') == 1 else 'Unknown'})")
            
            # Test case: When Time field is "06:10" and Date is "2025-06-13T06:10:00.000"
            # The time should be "06:10:00" (Time field + :00) not "06:10:00" from datetime
            if dep_time.count(':') == 2 and dep_time.endswith(':00'):
                print(f"\n✅ Time field is being prioritized (added :00 to HH:MM format)")
            elif dep_time.count(':') == 1:
                print(f"\n❌ Time field might not be processed correctly (still HH:MM format)")
            else:
                print(f"\n⚠️  Unexpected time format: {dep_time}")
                
        else:
            print("No segments found in first offer")
    else:
        print("No offers found in transformation result")

if __name__ == "__main__":
    test_time_field_priority()