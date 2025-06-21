#!/usr/bin/env python3
"""
Test the transformation process to see why airline codes are returning 'Unknown'.
"""

import sys
import json
import os

# Add the current directory to the path
sys.path.append('.')

from utils.data_transformer import transform_verteil_to_frontend, _extract_airline_code_robust

def test_airline_code_extraction():
    print("=== Testing Airline Code Extraction ===")
    
    # Load the API response
    try:
        with open('tests/airshoping_response.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: airshoping_response.json not found")
        return
    
    # Get the airline offers
    offers_group = data.get('OffersGroup', {})
    airline_offers = offers_group.get('AirlineOffers', [])
    
    if not airline_offers:
        print("No airline offers found")
        return
    
    print(f"Found {len(airline_offers)} airline offer groups")
    
    # Test extraction on the first group
    first_group = airline_offers[0]
    print(f"\nTesting extraction on first group with keys: {list(first_group.keys())}")
    
    # Call the extraction function directly
    extracted_code = _extract_airline_code_robust(first_group)
    print(f"Extracted airline code: {extracted_code}")
    
    # Check individual offers in the group
    individual_offers = first_group.get('AirlineOffer', [])
    print(f"\nChecking first 5 individual offers:")
    
    for i, offer in enumerate(individual_offers[:5]):
        offer_id = offer.get('OfferID', {})
        if isinstance(offer_id, dict):
            owner = offer_id.get('Owner')
            print(f"  Offer {i+1}: OfferID.Owner = {owner}")
        else:
            print(f"  Offer {i+1}: OfferID = {offer_id} (not a dict)")

def test_full_transformation():
    print("\n=== Testing Full Transformation ===")
    
    try:
        with open('tests/airshoping_response.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: airshoping_response.json not found")
        return
    
    # Run the full transformation
    try:
        result = transform_verteil_to_frontend(data)
        
        offers = result.get('offers', [])
        print(f"Transformation completed. Found {len(offers)} offers.")
        
        # Check the first few offer IDs
        print("\nFirst 10 offer IDs:")
        for i, offer in enumerate(offers[:10]):
            offer_id = offer.get('id', 'No ID')
            airline_code = offer.get('airline', {}).get('code', 'No Code')
            print(f"  {i+1}: {offer_id} (airline: {airline_code})")
        
        # Count how many start with 'Unknown'
        unknown_count = sum(1 for offer in offers if offer.get('id', '').startswith('Unknown-'))
        print(f"\nOffers starting with 'Unknown-': {unknown_count} out of {len(offers)}")
        
    except Exception as e:
        print(f"Error during transformation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_airline_code_extraction()
    test_full_transformation()