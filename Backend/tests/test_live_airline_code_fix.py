#!/usr/bin/env python3
"""
Test file to verify the airline code extraction fix works with live data.
This uses the actual API response from airshoping_response.json.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_transformer import transform_verteil_to_frontend, _extract_airline_code_robust
from utils.data_transformer_roundtrip import transform_verteil_to_frontend_with_roundtrip

def load_actual_api_response():
    """Load the actual API response from airshoping_response.json."""
    current_dir = Path(__file__).parent
    api_response_file = current_dir / 'api_response.json'
    
    try:
        with open(api_response_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading API response: {e}")
        return None

def test_airline_code_extraction_with_actual_data():
    """Test airline code extraction with the actual API response."""
    print("=== Testing Airline Code Extraction with Actual API Response ===")
    
    # Load actual API response
    api_response = load_actual_api_response()
    if not api_response:
        print("Failed to load API response")
        return
    
    print(f"Loaded API response with keys: {list(api_response.keys())}")
    
    # Test with standard data transformer
    print("\n--- Testing with standard data_transformer.py ---")
    try:
        result = transform_verteil_to_frontend(api_response)
        flight_offers = result.get('offers', [])
        print(f"Standard transformer created {len(flight_offers)} flight offers")
        
        if flight_offers:
            for i, offer in enumerate(flight_offers[:3]):  # Show first 3 offers
                print(f"Offer {i+1}: ID={offer.get('id', 'N/A')}, Airline={offer.get('airline', {}).get('code', 'N/A')}")
        else:
            print("No flight offers created by standard transformer")
    except Exception as e:
        print(f"Error with standard transformer: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with roundtrip data transformer
    print("\n--- Testing with data_transformer_roundtrip.py ---")
    try:
        roundtrip_result = transform_verteil_to_frontend_with_roundtrip(api_response)
        roundtrip_offers = roundtrip_result.get('offers', []) if isinstance(roundtrip_result, dict) else roundtrip_result
        print(f"Roundtrip transformer created {len(roundtrip_offers)} flight offers")
        
        if roundtrip_offers:
            for i, offer in enumerate(roundtrip_offers[:3]):  # Show first 3 offers
                print(f"Offer {i+1}: ID={offer.get('id', 'N/A')}, Airline={offer.get('airline', {}).get('code', 'N/A')}, Direction={offer.get('direction', 'N/A')}")
        else:
            print("No flight offers created by roundtrip transformer")
    except Exception as e:
        print(f"Error with roundtrip transformer: {e}")
        import traceback
        traceback.print_exc()
    
    # Test airline code extraction directly
    print("\n--- Testing Direct Airline Code Extraction ---")
    try:
        offers_group = api_response.get('OffersGroup', {})
        airline_offers = offers_group.get('AirlineOffers', [])
        
        print(f"Found {len(airline_offers)} airline offer groups")
        
        for i, airline_offer_group in enumerate(airline_offers[:3]):  # Test first 3 groups
            print(f"\nGroup {i+1}:")
            print(f"  Keys: {list(airline_offer_group.keys())}")
            
            # Test robust extraction
            airline_code = _extract_airline_code_robust(airline_offer_group)
            print(f"  Extracted airline code: {airline_code}")
            
            # Show Owner structure
            owner = airline_offer_group.get('Owner')
            print(f"  Owner: {owner} (type: {type(owner)})")
            
    except Exception as e:
        print(f"Error in direct extraction test: {e}")
        import traceback
        traceback.print_exc()

def test_error_scenarios():
    """Test specific error scenarios that might occur."""
    print("\n=== Testing Error Scenarios ===")
    
    # Test with empty response
    print("\n--- Testing with empty response ---")
    try:
        empty_offers = transform_verteil_to_frontend({})
        print(f"Empty response result: {len(empty_offers)} offers")
    except Exception as e:
        print(f"Error with empty response: {e}")
    
    # Test with malformed response
    print("\n--- Testing with malformed response ---")
    try:
        malformed_response = {'OffersGroup': {'AirlineOffers': 'not_a_list'}}
        malformed_offers = transform_verteil_to_frontend(malformed_response)
        print(f"Malformed response result: {len(malformed_offers)} offers")
    except Exception as e:
        print(f"Error with malformed response: {e}")

if __name__ == "__main__":
    test_airline_code_extraction_with_actual_data()
    test_error_scenarios()
    print("\n=== Test Complete ===")