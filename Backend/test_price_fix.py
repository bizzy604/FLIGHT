#!/usr/bin/env python3
"""
Test script to verify price and datetime extraction fixes
using the actual API response data.
"""

import json
import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_transformer import transform_verteil_to_frontend

def test_price_extraction():
    """Test price extraction with actual API response"""
    
    # Load the actual API response
    with open('debug/api_response_20250607_132944.json', 'r') as f:
        api_response = json.load(f)
    
    print("=== Testing Price and Datetime Extraction ===")
    print(f"Original API response has {len(api_response.get('OffersGroup', {}).get('AirlineOffers', []))} airline offers")
    
    # Transform the data
    try:
        transformed_data = transform_verteil_to_frontend(api_response)
        
        print(f"\nTransformed data has {len(transformed_data)} flight offers")
        
        # Check each offer for price and datetime
        for i, offer in enumerate(transformed_data):
            print(f"\n--- Offer {i+1} ---")
            print(f"ID: {offer.get('id', 'N/A')}")
            print(f"Price: {offer.get('price', 'N/A')} {offer.get('currency', 'N/A')}")
            
            # Check price breakdown
            price_breakdown = offer.get('priceBreakdown', {})
            print(f"Price Breakdown:")
            print(f"  Total: {price_breakdown.get('totalPrice', 'N/A')} {price_breakdown.get('currency', 'N/A')}")
            print(f"  Base Fare: {price_breakdown.get('baseFare', 'N/A')}")
            print(f"  Taxes: {price_breakdown.get('taxes', 'N/A')}")
            
            # Check segments for datetime
            segments = offer.get('segments', [])
            print(f"Segments: {len(segments)}")
            for j, segment in enumerate(segments):
                print(f"  Segment {j+1}:")
                print(f"    Departure: {segment.get('departure', {}).get('airport', 'N/A')} at {segment.get('departure', {}).get('datetime', 'N/A')}")
                print(f"    Arrival: {segment.get('arrival', {}).get('airport', 'N/A')} at {segment.get('arrival', {}).get('datetime', 'N/A')}")
                print(f"    Airline: {segment.get('airlineName', 'N/A')}")
                print(f"    Duration: {segment.get('duration', 'N/A')}")
            
            # Check baggage info
            baggage = offer.get('baggage', {})
            print(f"Baggage:")
            print(f"  Carry-on: {baggage.get('carryOn', 'N/A')}")
            print(f"  Checked: {baggage.get('checked', 'N/A')}")
            
            # Only show first 2 offers to avoid too much output
            if i >= 1:
                print(f"\n... and {len(transformed_data) - 2} more offers")
                break
                
    except Exception as e:
        print(f"Error during transformation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_price_extraction()
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)