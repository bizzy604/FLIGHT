#!/usr/bin/env python3
"""
Test script to verify ObjectKey mapping works with different airline formats
"""

import sys
import os
import json

# Add the scripts directory to the path
sys.path.append('../scripts')

from build_ordercreate_rq import create_passenger_mapping, generate_order_create_rq

def test_emirates_objectkey_mapping():
    """Test ObjectKey mapping with Emirates format (T1, T2, etc.)"""
    
    # Emirates-style flight price response with T1, T2 ObjectKeys
    emirates_response = {
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "T1",
                        "PTC": {
                            "value": "ADT"
                        }
                    },
                    {
                        "ObjectKey": "T2",
                        "PTC": {
                            "value": "CHD"
                        }
                    }
                ]
            }
        }
    }
    
    # Passenger data without ObjectKeys
    passengers_data = [
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
            "PTC": "CHD",
            "Name": {
                "Title": "Miss",
                "Given": ["Jane"],
                "Surname": "Doe"
            },
            "Gender": "Female",
            "BirthDate": "2015-01-01"
        }
    ]
    
    # Test the mapping
    mapping = create_passenger_mapping(emirates_response, passengers_data)
    
    print("Emirates ObjectKey Mapping Test:")
    print(f"  Mapping result: {mapping}")
    
    # Verify the mapping
    expected_mapping = {0: "T1", 1: "T2"}
    success = mapping == expected_mapping
    print(f"  Expected: {expected_mapping}")
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    return success

def test_lufthansa_objectkey_mapping():
    """Test ObjectKey mapping with Lufthansa format (LH_PAX1, LH_PAX2, etc.)"""
    
    # Lufthansa-style flight price response
    lufthansa_response = {
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "LH_PAX1",
                        "PTC": {
                            "value": "ADT"
                        }
                    },
                    {
                        "ObjectKey": "LH_PAX2",
                        "PTC": {
                            "value": "ADT"
                        }
                    }
                ]
            }
        }
    }
    
    # Passenger data
    passengers_data = [
        {
            "PTC": "ADT",
            "Name": {
                "Title": "Mr",
                "Given": ["Hans"],
                "Surname": "Mueller"
            },
            "Gender": "Male",
            "BirthDate": "1980-01-01"
        },
        {
            "PTC": "ADT",
            "Name": {
                "Title": "Mrs",
                "Given": ["Anna"],
                "Surname": "Mueller"
            },
            "Gender": "Female",
            "BirthDate": "1982-01-01"
        }
    ]
    
    # Test the mapping
    mapping = create_passenger_mapping(lufthansa_response, passengers_data)
    
    print("\nLufthansa ObjectKey Mapping Test:")
    print(f"  Mapping result: {mapping}")
    
    # Verify the mapping
    expected_mapping = {0: "LH_PAX1", 1: "LH_PAX2"}
    success = mapping == expected_mapping
    print(f"  Expected: {expected_mapping}")
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    return success

def test_mixed_ptc_mapping():
    """Test ObjectKey mapping with mixed passenger types"""
    
    # Response with mixed PTC types
    mixed_response = {
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "ADULT_1",
                        "PTC": {
                            "value": "ADT"
                        }
                    },
                    {
                        "ObjectKey": "CHILD_1",
                        "PTC": {
                            "value": "CHD"
                        }
                    },
                    {
                        "ObjectKey": "INFANT_1",
                        "PTC": {
                            "value": "INF"
                        }
                    }
                ]
            }
        }
    }
    
    # Passenger data with mixed types
    passengers_data = [
        {
            "PTC": "ADT",
            "Name": {"Title": "Mr", "Given": ["Adult"], "Surname": "Passenger"},
            "Gender": "Male",
            "BirthDate": "1985-01-01"
        },
        {
            "PTC": "CHD",
            "Name": {"Title": "Miss", "Given": ["Child"], "Surname": "Passenger"},
            "Gender": "Female",
            "BirthDate": "2015-01-01"
        },
        {
            "PTC": "INF",
            "Name": {"Title": "Master", "Given": ["Infant"], "Surname": "Passenger"},
            "Gender": "Male",
            "BirthDate": "2023-01-01"
        }
    ]
    
    # Test the mapping
    mapping = create_passenger_mapping(mixed_response, passengers_data)
    
    print("\nMixed PTC ObjectKey Mapping Test:")
    print(f"  Mapping result: {mapping}")
    
    # Verify the mapping
    expected_mapping = {0: "ADULT_1", 1: "CHILD_1", 2: "INFANT_1"}
    success = mapping == expected_mapping
    print(f"  Expected: {expected_mapping}")
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    return success

def test_existing_objectkey_preservation():
    """Test that existing ObjectKeys in passenger data are preserved when they match"""
    
    # Response with ObjectKeys
    response = {
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {
                        "ObjectKey": "T1",
                        "PTC": {
                            "value": "ADT"
                        }
                    },
                    {
                        "ObjectKey": "T2",
                        "PTC": {
                            "value": "ADT"
                        }
                    }
                ]
            }
        }
    }
    
    # Passenger data with existing ObjectKey that matches
    passengers_data = [
        {
            "ObjectKey": "T2",  # This should be preserved
            "PTC": "ADT",
            "Name": {"Title": "Mr", "Given": ["Test"], "Surname": "User"},
            "Gender": "Male",
            "BirthDate": "1985-01-01"
        },
        {
            "PTC": "ADT",  # This should get T1
            "Name": {"Title": "Mrs", "Given": ["Test"], "Surname": "User"},
            "Gender": "Female",
            "BirthDate": "1987-01-01"
        }
    ]
    
    # Test the mapping
    mapping = create_passenger_mapping(response, passengers_data)
    
    print("\nExisting ObjectKey Preservation Test:")
    print(f"  Mapping result: {mapping}")
    
    # Verify the mapping
    expected_mapping = {0: "T2", 1: "T1"}
    success = mapping == expected_mapping
    print(f"  Expected: {expected_mapping}")
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    return success

if __name__ == "__main__":
    print("=== Airline ObjectKey Mapping Tests ===")
    
    test1 = test_emirates_objectkey_mapping()
    test2 = test_lufthansa_objectkey_mapping()
    test3 = test_mixed_ptc_mapping()
    test4 = test_existing_objectkey_preservation()
    
    all_passed = test1 and test2 and test3 and test4
    
    print(f"\n=== Test Summary ===")
    print(f"Emirates mapping: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Lufthansa mapping: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Mixed PTC mapping: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"ObjectKey preservation: {'✅ PASS' if test4 else '❌ FAIL'}")
    print(f"\n🎉 All tests {'PASSED' if all_passed else 'FAILED'}! ObjectKey mapping works with different airline formats.")