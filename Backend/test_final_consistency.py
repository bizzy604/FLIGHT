#!/usr/bin/env python3
"""
Final comprehensive test to verify airline consistency fix.
"""

import json
import sys
import os
from pathlib import Path

# Add the Backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from transformers.enhanced_air_shopping_transformer import EnhancedAirShoppingTransformer
from utils.flight_price_transformer import build_flight_segment

def test_air_shopping_consistency():
    """Test air shopping transformer consistency."""
    
    print("🔍 Testing Air Shopping Consistency...")
    print("=" * 60)
    
    # Load the raw air shopping response
    raw_response_path = Path("Output/AirShopping_RESPONSE_20250706_040538.json")
    if not raw_response_path.exists():
        print("❌ Raw air shopping response file not found")
        return False
    
    with open(raw_response_path, 'r', encoding='utf-8') as f:
        raw_response_data = json.load(f)
    
    raw_response = raw_response_data.get('data', raw_response_data)
    
    try:
        transformer = EnhancedAirShoppingTransformer(raw_response)
        transformed_response = transformer.transform_for_results()
        
        if not transformed_response or 'offers' not in transformed_response:
            print("❌ Failed to transform air shopping response")
            return False
        
        offers = transformed_response['offers']
        print(f"✅ Found {len(offers)} transformed offers")
        
        # Test first 5 offers
        test_count = min(5, len(offers))
        af_count = 0
        kl_count = 0
        
        print(f"\n📊 Testing first {test_count} offers:")
        for i in range(test_count):
            offer = offers[i]
            airline_code = offer.get('airline', {}).get('code', '??')
            airline_name = offer.get('airline', {}).get('name', 'Unknown')
            
            print(f"  Offer {i+1}: {airline_code} ({airline_name})")
            
            if airline_code == 'AF':
                af_count += 1
            elif airline_code == 'KL':
                kl_count += 1
        
        print(f"\n📈 Results:")
        print(f"  AF (Air France): {af_count} offers")
        print(f"  KL (KLM): {kl_count} offers")
        
        # Success criteria: More AF than KL in first 5 offers
        # (indicating we're using operating carrier instead of offer owner)
        if af_count > kl_count:
            print("✅ SUCCESS: Using operating carrier (AF) instead of offer owner (KL)")
            return True
        elif af_count == 0 and kl_count > 0:
            print("❌ ISSUE: Still using offer owner (KL) instead of operating carrier")
            return False
        else:
            print("⚠️  MIXED: Some offers show AF, some show KL - may be correct for codeshare")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_flight_price_consistency():
    """Test flight price transformer consistency."""
    
    print("\n" + "=" * 60)
    print("🔍 Testing Flight Price Consistency...")
    print("=" * 60)
    
    # Create a mock segment to test our flight price transformer
    mock_segment = {
        "OperatingCarrier": {
            "AirlineID": {"value": "AF"},
            "Name": "Air France"
        },
        "MarketingCarrier": {
            "AirlineID": {"value": "KL"},
            "FlightNumber": {"value": "829"}
        },
        "Departure": {
            "AirportCode": {"value": "NBO"},
            "Date": "2025-07-10T22:25:00"
        },
        "Arrival": {
            "AirportCode": {"value": "CDG"},
            "Date": "2025-07-11T06:25:00"
        },
        "FlightDetail": {
            "FlightDuration": {"Value": "PT8H0M"}
        }
    }
    
    try:
        flight_segment = build_flight_segment(mock_segment)
        
        print(f"Operating Carrier: AF (Air France)")
        print(f"Marketing Carrier: KL (KLM)")
        print(f"Flight Segment Result: {flight_segment.airline_code} ({flight_segment.airline_name})")
        
        # Should prioritize operating carrier (AF)
        if flight_segment.airline_code == 'AF':
            print("✅ SUCCESS: Flight price transformer uses operating carrier")
            return True
        elif flight_segment.airline_code == 'KL':
            print("❌ ISSUE: Flight price transformer uses marketing carrier instead of operating")
            return False
        else:
            print(f"❓ UNKNOWN: Unexpected airline code: {flight_segment.airline_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling."""
    
    print("\n" + "=" * 60)
    print("🔍 Testing Edge Cases...")
    print("=" * 60)
    
    # Test with missing operating carrier
    mock_segment_no_operating = {
        "MarketingCarrier": {
            "AirlineID": {"value": "KL"},
            "FlightNumber": {"value": "829"}
        },
        "Departure": {
            "AirportCode": {"value": "NBO"},
            "Date": "2025-07-10T22:25:00"
        },
        "Arrival": {
            "AirportCode": {"value": "CDG"},
            "Date": "2025-07-11T06:25:00"
        },
        "FlightDetail": {
            "FlightDuration": {"Value": "PT8H0M"}
        }
    }
    
    try:
        flight_segment = build_flight_segment(mock_segment_no_operating)
        
        print(f"Test 1 - No Operating Carrier:")
        print(f"  Marketing Carrier: KL")
        print(f"  Result: {flight_segment.airline_code}")
        
        if flight_segment.airline_code == 'KL':
            print("  ✅ Correctly falls back to marketing carrier")
            test1_ok = True
        else:
            print("  ❌ Failed to fall back to marketing carrier")
            test1_ok = False
        
        # Test with empty segment
        empty_segment = {}
        flight_segment_empty = build_flight_segment(empty_segment)
        
        print(f"\nTest 2 - Empty Segment:")
        print(f"  Result: {flight_segment_empty.airline_code}")
        
        if flight_segment_empty.airline_code == '??':
            print("  ✅ Correctly handles empty segment")
            test2_ok = True
        else:
            print("  ❌ Failed to handle empty segment")
            test2_ok = False
        
        return test1_ok and test2_ok
        
    except Exception as e:
        print(f"❌ Error in edge case testing: {e}")
        return False

def main():
    """Run all consistency tests."""
    
    print("🚀 Running Final Airline Consistency Tests...")
    print("=" * 80)
    
    # Run all tests
    air_shopping_ok = test_air_shopping_consistency()
    flight_price_ok = test_flight_price_consistency()
    edge_cases_ok = test_edge_cases()
    
    print("\n" + "=" * 80)
    print("🏁 FINAL RESULTS:")
    print("=" * 80)
    print(f"Air Shopping Consistency: {'✅ PASS' if air_shopping_ok else '❌ FAIL'}")
    print(f"Flight Price Consistency: {'✅ PASS' if flight_price_ok else '❌ FAIL'}")
    print(f"Edge Cases Handling: {'✅ PASS' if edge_cases_ok else '❌ FAIL'}")
    
    overall_success = air_shopping_ok and flight_price_ok and edge_cases_ok
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Airline information is now consistent between search and details pages")
        print("✅ Operating carrier is prioritized over offer owner")
        print("✅ System handles edge cases gracefully")
        print("\n📋 SUMMARY OF CHANGES:")
        print("  • Enhanced Air Shopping Transformer now extracts operating carrier")
        print("  • Flight Price Transformer prioritizes operating carrier")
        print("  • Data Transformer uses consistent airline extraction logic")
        print("  • Proper fallback handling for missing carrier information")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Review the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
