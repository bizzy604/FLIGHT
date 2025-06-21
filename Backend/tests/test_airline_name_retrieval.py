"""Test script to verify airline name retrieval functionality in data_transformer.py"""

import sys
import os
import json
import logging
from typing import Dict, Any

# Add the Backend directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import _get_airline_name, _extract_reference_data

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_airline_name_fallback_mapping():
    """Test the fallback airline name mapping for known codes"""
    print("\n=== Testing Fallback Airline Name Mapping ===")
    
    test_cases = [
        ('EK', 'Emirates'),
        ('QR', 'Qatar Airways'),
        ('SQ', 'Singapore Airlines'),
        ('EY', 'Etihad Airways'),
        ('TK', 'Turkish Airlines'),
        ('LH', 'Lufthansa'),
        ('BA', 'British Airways'),
        ('AF', 'Air France'),
        ('KL', 'KLM'),
        ('AA', 'American Airlines'),
        ('DL', 'Delta Air Lines'),
        ('UA', 'United Airlines'),
        ('QF', 'Qantas'),
        ('CX', 'Cathay Pacific'),
        ('NH', 'ANA'),
        ('JL', 'Japan Airlines'),
        ('AC', 'Air Canada'),
        ('VS', 'Virgin Atlantic'),
        ('LX', 'Swiss International Air Lines')
    ]
    
    passed = 0
    failed = 0
    
    for code, expected_name in test_cases:
        result = _get_airline_name(code)
        if result == expected_name:
            print(f"✓ {code} -> {result}")
            passed += 1
        else:
            print(f"✗ {code} -> Expected: {expected_name}, Got: {result}")
            failed += 1
    
    print(f"\nFallback mapping test results: {passed} passed, {failed} failed")
    return failed == 0

def test_airline_name_with_reference_data():
    """Test airline name retrieval with mock reference data"""
    print("\n=== Testing Airline Name with Reference Data ===")
    
    # Mock reference data structure
    reference_data = {
        'airlines': {
            'EK': 'Emirates Airlines',
            'QR': 'Qatar Airways',
            'XX': 'Test Airline'
        },
        'segments': {
            'SEG1': {
                'MarketingCarrier': {
                    'AirlineID': {'value': 'TK'},
                    'Name': 'Turkish Airlines from Segment'
                }
            },
            'SEG2': {
                'OperatingCarrier': {
                    'AirlineID': {'value': 'LH'},
                    'Name': 'Lufthansa from Operating Carrier'
                }
            }
        },
        'flights': {
            'FLT1': {
                'MarketingCarrier': {
                    'AirlineID': {'value': 'AF'},
                    'Name': 'Air France from Flight'
                }
            }
        }
    }
    
    test_cases = [
        # Test airlines dictionary lookup
        ('EK', 'Emirates Airlines', 'from airlines dictionary'),
        ('QR', 'Qatar Airways', 'from airlines dictionary'),
        ('XX', 'Test Airline', 'from airlines dictionary'),
        
        # Test segment marketing carrier lookup - this should fall back to known codes since TK is not in airlines dict
        ('TK', 'Turkish Airlines', 'from fallback mapping (TK not in segments lookup)'),
        
        # Test segment operating carrier lookup - this should fall back to known codes since LH is not in airlines dict
        ('LH', 'Lufthansa', 'from fallback mapping (LH not in segments lookup)'),
        
        # Test flight marketing carrier lookup - this should fall back to known codes since AF is not in airlines dict
        ('AF', 'Air France', 'from fallback mapping (AF not in flights lookup)'),
        
        # Test fallback to known codes
        ('SQ', 'Singapore Airlines', 'from fallback mapping'),
        
        # Test unknown code
        ('ZZ', 'Airline ZZ', 'unknown code fallback')
    ]
    
    passed = 0
    failed = 0
    
    for code, expected_name, source in test_cases:
        result = _get_airline_name(code, reference_data)
        if result == expected_name:
            print(f"✓ {code} -> {result} ({source})")
            passed += 1
        else:
            print(f"✗ {code} -> Expected: {expected_name}, Got: {result} ({source})")
            print(f"  Debug: Airlines dict has {code}: {code in reference_data.get('airlines', {})}")
            failed += 1
    
    print(f"\nReference data test results: {passed} passed, {failed} failed")
    return failed == 0

def test_airline_name_edge_cases():
    """Test edge cases for airline name retrieval"""
    print("\n=== Testing Edge Cases ===")
    
    test_cases = [
        (None, 'Unknown Airline', 'None input'),
        ('', 'Unknown Airline', 'empty string'),
        ('  ', 'Unknown Airline', 'whitespace only'),
        ('ek', 'Emirates', 'lowercase code'),
        ('  EK  ', 'Emirates', 'code with whitespace'),
        (123, 'Unknown Airline', 'non-string input')
    ]
    
    passed = 0
    failed = 0
    
    for code, expected_name, description in test_cases:
        try:
            result = _get_airline_name(code)
            if result == expected_name:
                print(f"✓ {description}: {code} -> {result}")
                passed += 1
            else:
                print(f"✗ {description}: {code} -> Expected: {expected_name}, Got: {result}")
                failed += 1
        except Exception as e:
            print(f"✗ {description}: {code} -> Exception: {str(e)}")
            failed += 1
    
    print(f"\nEdge cases test results: {passed} passed, {failed} failed")
    return failed == 0

def test_extract_reference_data_airline_extraction():
    """Test airline extraction from a mock Verteil response"""
    print("\n=== Testing Airline Extraction from Mock Response ===")
    
    # Mock Verteil API response structure
    mock_response = {
        'DataLists': {
            'FlightSegmentList': {
                'FlightSegment': [
                    {
                        'SegmentKey': 'SEG1',
                        'MarketingCarrier': {
                            'AirlineID': {'value': 'EK'},
                            'Name': 'Emirates'
                        },
                        'OperatingCarrier': {
                            'AirlineID': {'value': 'EK'},
                            'Name': 'Emirates'
                        },
                        'Departure': {
                            'AirportCode': {'value': 'DXB'},
                            'AirportName': 'Dubai International'
                        },
                        'Arrival': {
                            'AirportCode': {'value': 'LHR'},
                            'AirportName': 'London Heathrow'
                        }
                    },
                    {
                        'SegmentKey': 'SEG2',
                        'MarketingCarrier': {
                            'AirlineID': {'value': 'QR'},
                            'Name': 'Qatar Airways'
                        },
                        'Departure': {
                            'AirportCode': {'value': 'DOH'},
                            'AirportName': 'Hamad International'
                        },
                        'Arrival': {
                            'AirportCode': {'value': 'JFK'},
                            'AirportName': 'John F Kennedy International'
                        }
                    }
                ]
            }
        }
    }
    
    # Extract reference data
    reference_data = _extract_reference_data(mock_response)
    
    # Test extracted airlines
    expected_airlines = {
        'EK': 'Emirates',
        'QR': 'Qatar Airways'
    }
    
    print(f"Extracted airlines: {reference_data.get('airlines', {})}")
    print(f"Default airline: {reference_data.get('default_airline', {})}")
    
    passed = 0
    failed = 0
    
    for code, expected_name in expected_airlines.items():
        if code in reference_data.get('airlines', {}):
            actual_name = reference_data['airlines'][code]
            if actual_name == expected_name:
                print(f"✓ Extracted {code}: {actual_name}")
                passed += 1
            else:
                print(f"✗ {code}: Expected {expected_name}, Got {actual_name}")
                failed += 1
        else:
            print(f"✗ {code}: Not found in extracted airlines")
            failed += 1
    
    # Test default airline
    default_airline = reference_data.get('default_airline')
    if default_airline and default_airline.get('code') == 'EK' and default_airline.get('name') == 'Emirates':
        print(f"✓ Default airline correctly set: {default_airline}")
        passed += 1
    else:
        print(f"✗ Default airline incorrect: {default_airline}")
        failed += 1
    
    print(f"\nReference data extraction test results: {passed} passed, {failed} failed")
    return failed == 0

def run_all_tests():
    """Run all airline name retrieval tests"""
    print("Starting Airline Name Retrieval Tests...")
    print("=" * 60)
    
    tests = [
        test_airline_name_fallback_mapping,
        test_airline_name_with_reference_data,
        test_airline_name_edge_cases,
        test_extract_reference_data_airline_extraction
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"\n✗ Test {test_func.__name__} failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Airline name retrieval is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the airline name retrieval logic.")
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)