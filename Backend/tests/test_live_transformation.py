#!/usr/bin/env python3
"""
Test script to debug transformation using the latest live API response.
"""

import json
import sys
import os
import logging

# Configure logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Add the Backend directory to the Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from utils.data_transformer import transform_verteil_to_frontend

def test_live_transformation():
    """Test transformation using the latest live API response."""
    
    # Load the latest live API response
    response_file = 'api_response.json'
    
    try:
        with open(response_file, 'r', encoding='utf-8') as f:
            api_response = json.load(f)
        
        print(f"Loaded API response from: {response_file}")
        print(f"Actual response keys: {list(api_response.keys())}")
        
        # Test the transformation
        result = transform_verteil_to_frontend(api_response)
        
        if result and isinstance(result, dict):
            offers = result.get('offers', [])
            if offers and len(offers) > 0:
                print(f"\nTransformation successful!")
                print(f"Number of offers: {len(offers)}")
                
                # Print first offer details
                first_offer = offers[0]
                print(f"\nFirst offer details:")
                print(f"- Flight Number: {first_offer['segments'][0]['flightNumber']}")
                print(f"- Departure: {first_offer['segments'][0]['departure']['airport']} -> {first_offer['segments'][0]['arrival']['airport']}")
                print(f"- Price: {first_offer['priceBreakdown']['totalPrice']} {first_offer['priceBreakdown']['currency']}")
                print(f"- Full price breakdown: {first_offer['priceBreakdown']}")
                
                # Debug: Check the original price structure
                priced_offer = api_response['OffersGroup']['AirlineOffers'][0]['AirlineOffer'][0]['PricedOffer']
                print(f"\nDebug - PricedOffer TotalPrice: {priced_offer.get('TotalPrice', 'Not found')}")
                offer_price = priced_offer.get('OfferPrice', [{}])[0]
                print(f"Debug - OfferPrice PriceDetail: {offer_price.get('PriceDetail', 'Not found')}")
            else:
                print("\nTransformation failed - no offers returned")
        else:
            print("\nTransformation failed - invalid result format")
            
    except Exception as e:
        print(f"Error during transformation test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == '__main__':
    test_live_transformation()