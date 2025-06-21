#!/usr/bin/env python3
"""
Test file to debug airline code extraction from API responses.
This helps understand the structure before fixing the live environment.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_transformer import transform_verteil_to_frontend, _extract_reference_data

def load_sample_api_response():
    """Load a sample API response for testing."""
    # Try to load from debug directory
    debug_file = Path(__file__).parent.parent / "debug" / "api_response_20250607_132944.json"
    
    if debug_file.exists():
        with open(debug_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"Debug file not found: {debug_file}")
        return None

def test_airline_code_extraction():
    """Test airline code extraction from API response."""
    print("=== Testing Airline Code Extraction ===")
    
    # Load sample data
    api_response = load_sample_api_response()
    if not api_response:
        print("No sample API response found. Cannot proceed with test.")
        return
    
    print(f"Loaded API response with keys: {list(api_response.keys())}")
    
    # Check if AirShoppingRS exists in the response
    if 'AirShoppingRS' in api_response:
        api_response = api_response['AirShoppingRS']
        print(f"Using AirShoppingRS with keys: {list(api_response.keys())}")
    
    # Navigate to the offers in the response - matching the actual implementation
    offers_group = api_response.get('OffersGroup', {})
    print(f"OffersGroup found: {offers_group is not None}, keys: {list(offers_group.keys()) if offers_group else 'None'}")
    
    airline_offers = offers_group.get('AirlineOffers', [])
    print(f"AirlineOffers found: {len(airline_offers) if isinstance(airline_offers, list) else 'Not a list' if airline_offers else 'None'}")
    
    # Extract reference data for lookups
    reference_data = _extract_reference_data(api_response)
    print(f"Reference data extracted: flights={len(reference_data['flights'])}, segments={len(reference_data['segments'])}")
    
    # Iterate through airline offer groups - matching the actual implementation
    for i, airline_offer_group in enumerate(airline_offers):
        # Debug the Owner structure
        owner_data = airline_offer_group.get('Owner', {})
        print(f"\n--- Airline Offer Group {i} ---")
        print(f"Owner data structure: {owner_data}")
        print(f"Owner data type: {type(owner_data)}")
        
        if isinstance(owner_data, dict):
            print(f"Owner keys: {list(owner_data.keys())}")
            value = owner_data.get('value')
            print(f"Owner.value: {value}")
        
        # Test the extraction logic as implemented in the actual code
        airline_code = owner_data.get('value', 'Unknown')
        print(f"Extracted airline_code: {airline_code}")
        
        # Check the AirlineOffer structure
        airline_offers_list = airline_offer_group.get('AirlineOffer', [])
        print(f"AirlineOffer count: {len(airline_offers_list) if isinstance(airline_offers_list, list) else 'Not a list'}")
        
        # Print the first offer structure if available
        if isinstance(airline_offers_list, list) and airline_offers_list:
            first_offer = airline_offers_list[0]
            print(f"First offer keys: {list(first_offer.keys()) if isinstance(first_offer, dict) else 'Not a dict'}")
            
            # Check for PricedOffer which is used in ID generation
            if isinstance(first_offer, dict) and 'PricedOffer' in first_offer:
                priced_offer = first_offer['PricedOffer']
                print(f"PricedOffer keys: {list(priced_offer.keys()) if isinstance(priced_offer, dict) else 'Not a dict'}")
                
                # Check for OfferID which might be used instead of generating one
                if isinstance(priced_offer, dict) and 'OfferID' in priced_offer:
                    offer_id = priced_offer['OfferID']
                    print(f"OfferID from PricedOffer: {offer_id}")

def test_transformation_with_debug():
    """Test the full transformation process with debug output."""
    print("\n=== Testing Full Transformation ===")
    
    api_response = load_sample_api_response()
    if not api_response:
        print("No sample API response found. Cannot proceed with test.")
        return
    
    try:
        # Transform the data
        result = transform_verteil_to_frontend(api_response)
        
        print(f"Transformation successful. Found {len(result)} flights.")
        
        # Check the generated offer IDs
        for i, flight in enumerate(result[:3]):  # Show first 3 flights
            print(f"\nFlight {i+1}:")
            print(f"  ID: {flight.get('id', 'No ID')}")
            print(f"  Offer ID: {flight.get('offer_id', 'No offer_id')}")
            print(f"  Airline: {flight.get('airline', 'No airline')}")
            print(f"  Price: {flight.get('price', 'No price')}")
            
    except Exception as e:
        print(f"Transformation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_airline_code_extraction()
    test_transformation_with_debug()
    
    print("\n=== Test Complete ===")
    print("Review the output above to understand the API response structure.")
    print("This will help identify why airline_code might be 'Unknown' in live data.")