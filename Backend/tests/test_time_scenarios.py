#!/usr/bin/env python3
"""
Comprehensive test to verify Time field priority logic works in different scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend
import json

def test_time_scenarios():
    """Test different time field scenarios."""
    
    print("=== Testing Time Field Priority Scenarios ===\n")
    
    # Test Case 1: Mock data with separate Time field (HH:MM format)
    mock_data_with_time = {
        "OffersGroup": {
            "AirlineOffers": [
                {
                    "Owner": {"value": "AA"},
                    "AirlineOffer": [
                        {
                            "PricedOffer": {
                                "OfferPrice": [
                                    {
                                        "RequestedDate": {
                                            "PriceClassRef": "flight1"
                                        }
                                    }
                                ],
                                "Associations": {
                                    "AssociatedTraveler": {
                                        "TravelerReferences": "traveler1"
                                    },
                                    "ApplicableFlight": {
                                        "FlightSegmentReference": {
                                            "ref": "flight1"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "flight1",
                        "Departure": {
                            "AirportCode": {"value": "JFK"},
                            "Date": "2025-06-15T00:00:00.000",
                            "Time": "14:30"  # Separate Time field
                        },
                        "Arrival": {
                            "AirportCode": {"value": "LAX"},
                            "Date": "2025-06-15T00:00:00.000",
                            "Time": "18:45"  # Separate Time field
                        },
                        "OperatingCarrier": {
                            "AirlineID": {"value": "AA"},
                            "Name": "American Airlines",
                            "FlightNumber": {"value": "100"}
                        }
                    }
                ]
            }
        }
    }
    
    # Test Case 2: Mock data without separate Time field (only Date with full datetime)
    mock_data_without_time = {
        "OffersGroup": {
            "AirlineOffers": [
                {
                    "Owner": {"value": "AA"},
                    "AirlineOffer": [
                        {
                            "PricedOffer": {
                                "OfferPrice": [
                                    {
                                        "RequestedDate": {
                                            "PriceClassRef": "flight2"
                                        }
                                    }
                                ],
                                "Associations": {
                                    "AssociatedTraveler": {
                                        "TravelerReferences": "traveler2"
                                    },
                                    "ApplicableFlight": {
                                        "FlightSegmentReference": {
                                            "ref": "flight2"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        },
        "DataLists": {
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "flight2",
                        "Departure": {
                            "AirportCode": {"value": "LAX"},
                            "Date": "2025-06-16T09:15:30.000"  # No separate Time field
                        },
                        "Arrival": {
                            "AirportCode": {"value": "JFK"},
                            "Date": "2025-06-16T17:45:15.000"  # No separate Time field
                        },
                        "OperatingCarrier": {
                            "AirlineID": {"value": "AA"},
                            "Name": "American Airlines",
                            "FlightNumber": {"value": "200"}
                        }
                    }
                ]
            }
        }
    }
    
    print("Test Case 1: With separate Time field")
    result1 = transform_verteil_to_frontend(mock_data_with_time, enable_roundtrip=False)
    if result1 and len(result1) > 0:
        segment1 = result1[0]['segments'][0]
        dep_time1 = segment1['departure']['time']
        arr_time1 = segment1['arrival']['time']
        print(f"  Departure time: {dep_time1} (should be 14:30:00 from Time field)")
        print(f"  Arrival time: {arr_time1} (should be 18:45:00 from Time field)")
        
        if dep_time1 == "14:30:00" and arr_time1 == "18:45:00":
            print("  ✅ Time field prioritized correctly\n")
        else:
            print("  ❌ Time field not prioritized correctly\n")
    
    print("Test Case 2: Without separate Time field (fallback to Date)")
    result2 = transform_verteil_to_frontend(mock_data_without_time, enable_roundtrip=False)
    if result2 and len(result2) > 0:
        segment2 = result2[0]['segments'][0]
        dep_time2 = segment2['departure']['time']
        arr_time2 = segment2['arrival']['time']
        print(f"  Departure time: {dep_time2} (should be 09:15:30 from Date field)")
        print(f"  Arrival time: {arr_time2} (should be 17:45:15 from Date field)")
        
        if dep_time2 == "09:15:30" and arr_time2 == "17:45:15":
            print("  ✅ Fallback to Date field works correctly\n")
        else:
            print("  ❌ Fallback to Date field not working correctly\n")
    
    print("=== Real Data Test ===\n")
    # Test with real data
    with open('tests/airshoping_response.json', 'r') as f:
        real_data = json.load(f)
    
    real_result = transform_verteil_to_frontend(real_data, enable_roundtrip=False)
    if real_result and len(real_result) > 0:
        real_segment = real_result[0]['segments'][0]
        real_dep_time = real_segment['departure']['time']
        real_arr_time = real_segment['arrival']['time']
        print(f"Real data - Departure time: {real_dep_time}")
        print(f"Real data - Arrival time: {real_arr_time}")
        
        # Check if it's using Time field (should end with :00 if converted from HH:MM)
        if real_dep_time.endswith(':00') and real_arr_time.endswith(':00'):
            print("✅ Real data is using Time field priority correctly")
        else:
            print("⚠️  Real data time format might be from Date field")

if __name__ == "__main__":
    test_time_scenarios()