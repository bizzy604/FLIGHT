#!/usr/bin/env python3
"""
Test script to verify ObjectKey generation fix for passengers
"""

import sys
import os
import json

# Add the scripts directory to the path
sys.path.append('../scripts')

from build_ordercreate_rq import process_passengers_for_order_create

def test_objectkey_generation():
    """Test that ObjectKey is generated when missing from passenger data"""
    
    # Test data with missing ObjectKey
    passengers_without_objectkey = [
        {
            "PTC": "ADT",
            "Name": {
                "Title": "Mr",
                "Given": ["John"],
                "Surname": "Doe"
            },
            "Gender": "Male",
            "BirthDate": "1985-03-15"
        },
        {
            "PTC": "ADT", 
            "Name": {
                "Title": "Mrs",
                "Given": ["Jane"],
                "Surname": "Doe"
            },
            "Gender": "Female",
            "BirthDate": "1987-07-22"
        }
    ]
    
    # Test data with existing ObjectKey
    passengers_with_objectkey = [
        {
            "ObjectKey": "CUSTOM1",
            "PTC": "ADT",
            "Name": {
                "Title": "Mr",
                "Given": ["Bob"],
                "Surname": "Smith"
            },
            "Gender": "Male",
            "BirthDate": "1980-01-01"
        }
    ]
    
    # Test 1: Missing ObjectKey should be generated
    result_list_1 = []
    process_passengers_for_order_create(passengers_without_objectkey, result_list_1)
    
    print("Test 1 - Missing ObjectKey generation:")
    for i, passenger in enumerate(result_list_1):
        expected_key = f"PAX{i+1}"
        actual_key = passenger.get("ObjectKey")
        print(f"  Passenger {i+1}: Expected '{expected_key}', Got '{actual_key}' - {'✅ PASS' if actual_key == expected_key else '❌ FAIL'}")
    
    # Test 2: Existing ObjectKey should be preserved
    result_list_2 = []
    process_passengers_for_order_create(passengers_with_objectkey, result_list_2)
    
    print("\nTest 2 - Existing ObjectKey preservation:")
    for i, passenger in enumerate(result_list_2):
        expected_key = "CUSTOM1"
        actual_key = passenger.get("ObjectKey")
        print(f"  Passenger {i+1}: Expected '{expected_key}', Got '{actual_key}' - {'✅ PASS' if actual_key == expected_key else '❌ FAIL'}")
    
    # Test 3: Mixed scenario
    mixed_passengers = [
        {
            "ObjectKey": "EXISTING1",
            "PTC": "ADT",
            "Name": {"Title": "Mr", "Given": ["Test1"], "Surname": "User1"},
            "Gender": "Male",
            "BirthDate": "1990-01-01"
        },
        {
            # Missing ObjectKey
            "PTC": "CHD",
            "Name": {"Title": "Miss", "Given": ["Test2"], "Surname": "User2"},
            "Gender": "Female",
            "BirthDate": "2015-01-01"
        }
    ]
    
    result_list_3 = []
    process_passengers_for_order_create(mixed_passengers, result_list_3)
    
    print("\nTest 3 - Mixed scenario:")
    expected_keys = ["EXISTING1", "PAX2"]
    for i, passenger in enumerate(result_list_3):
        expected_key = expected_keys[i]
        actual_key = passenger.get("ObjectKey")
        print(f"  Passenger {i+1}: Expected '{expected_key}', Got '{actual_key}' - {'✅ PASS' if actual_key == expected_key else '❌ FAIL'}")
    
    print("\n=== ObjectKey Fix Test Complete ===")

if __name__ == "__main__":
    test_objectkey_generation()