#!/usr/bin/env python3
"""
Test script to verify time extraction from actual API response.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from utils.data_transformer import transform_verteil_to_frontend

def test_actual_transformation():
    """Test the actual transformation with real API data."""
    
    # Load the test data
    with open('tests/airshoping_response.json', 'r') as f:
        test_data = json.load(f)
    
    print("=== Testing Actual API Response Transformation ===")
    
    # Test transformation
    result = transform_verteil_to_frontend(test_data, enable_roundtrip=False)
    
    if result and len(result) > 0:
        first_offer = result[0]
        print(f"\nFirst offer structure:")
        print(f"  Departure: {first_offer.get('departure', {})}")
        print(f"  Arrival: {first_offer.get('arrival', {})}")
        
        # Check if segments exist
        segments = first_offer.get('segments', [])
        if segments:
            print(f"\nFirst segment:")
            first_segment = segments[0]
            print(f"  Departure: {first_segment.get('departure', {})}")
            print(f"  Arrival: {first_segment.get('arrival', {})}")
            
            # Check if time field exists
            dep_time = first_segment.get('departure', {}).get('time')
            arr_time = first_segment.get('arrival', {}).get('time')
            
            print(f"\nTime fields:")
            print(f"  Departure time: {dep_time}")
            print(f"  Arrival time: {arr_time}")
            
            if dep_time is None or arr_time is None:
                print("\n❌ TIME FIELDS ARE MISSING!")
            else:
                print(f"\n✅ Time fields are present")
        else:
            print("\n❌ No segments found in the offer")
    else:
        print("\n❌ No offers returned from transformation")

if __name__ == '__main__':
    test_actual_transformation()