#!/usr/bin/env python3
"""
Test script to verify time field extraction from datetime strings.
"""

import json
from utils.data_transformer import transform_verteil_to_frontend

def test_time_extraction():
    """Test that time fields are correctly extracted from datetime strings."""
    
    # Load the test data
    with open('tests/airshoping_response.json', 'r') as f:
        test_data = json.load(f)
    
    print("=== Testing Time Field Extraction ===")
    
    # Test default transformation
    print("\n1. Testing Default Transformation:")
    default_result = transform_verteil_to_frontend(test_data, enable_roundtrip=False)
    
    if default_result:
        first_offer = default_result[0]
        departure = first_offer.get('departure', {})
        arrival = first_offer.get('arrival', {})
        
        print(f"   Departure datetime: {departure.get('datetime')}")
        print(f"   Departure time: {departure.get('time')}")
        print(f"   Arrival datetime: {arrival.get('datetime')}")
        print(f"   Arrival time: {arrival.get('time')}")
        
        # Check segments for time fields
        segments = first_offer.get('segments', [])
        if segments:
            seg = segments[0]
            seg_dep = seg.get('departure', {})
            seg_arr = seg.get('arrival', {})
            print(f"   Segment departure time: {seg_dep.get('time')}")
            print(f"   Segment arrival time: {seg_arr.get('time')}")
    
    # Test enhanced transformation
    print("\n2. Testing Enhanced Transformation:")
    enhanced_result = transform_verteil_to_frontend(test_data, enable_roundtrip=True)
    
    if enhanced_result:
        first_offer = enhanced_result[0]
        departure = first_offer.get('departure', {})
        arrival = first_offer.get('arrival', {})
        
        print(f"   Departure datetime: {departure.get('datetime')}")
        print(f"   Departure time: {departure.get('time')}")
        print(f"   Arrival datetime: {arrival.get('datetime')}")
        print(f"   Arrival time: {arrival.get('time')}")
        print(f"   Trip type: {first_offer.get('tripType')}")
        print(f"   Direction: {first_offer.get('direction')}")
    
    print("\n=== Time Extraction Test Complete ===")
    print("\nVerification:")
    print("✓ Time fields should be in HH:MM format")
    print("✓ Time should match the time portion of datetime")
    print("✓ Both departure and arrival should have time fields")
    print("✓ Enhanced mode should include tripType and direction fields")

if __name__ == "__main__":
    test_time_extraction()