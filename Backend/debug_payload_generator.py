#!/usr/bin/env python3
"""
Debug script to generate and inspect FlightPrice request payload
"""

import json
import sys
from pathlib import Path

# Add the Backend directory to the Python path
sys.path.append('.')

from scripts.build_flightprice_rq import build_flight_price_request

def main():
    # Load the test data
    test_file = Path('../postman/airshopingresponse.json')
    
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        return 1
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # Build a flight price request for offer index 0
    try:
        request = build_flight_price_request(test_data, selected_offer_index=0)
        
        # Save to file for inspection
        output_file = Path('debug_flightprice_request.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(request, f, indent=2, ensure_ascii=False)
        
        print('FlightPrice request generated successfully!')
        print('Key structure:')
        print(f'- Top level keys: {list(request.keys())}')
        print(f'- DataLists keys: {list(request.get("DataLists", {}).keys())}')
        print(f'- Query keys: {list(request.get("Query", {}).keys())}')
        print(f'- ShoppingResponseID type: {type(request.get("ShoppingResponseID"))}')
        
        if isinstance(request.get('ShoppingResponseID'), dict):
            print(f'- ShoppingResponseID keys: {list(request.get("ShoppingResponseID", {}).keys())}')
            print(f'- ShoppingResponseID value: {request.get("ShoppingResponseID")}')
        
        print(f'- Travelers keys: {list(request.get("Travelers", {}).keys())}')
        
        # Check Query structure
        query = request.get("Query", {})
        if "Offers" in query:
            offers = query["Offers"]
            print(f'- Query.Offers keys: {list(offers.keys())}')
            if "Offer" in offers and offers["Offer"]:
                first_offer = offers["Offer"][0]
                print(f'- First offer keys: {list(first_offer.keys())}')
                if "OfferID" in first_offer:
                    print(f'- OfferID structure: {first_offer["OfferID"]}')
        
        print(f'\nPayload saved to: {output_file}')
        return 0
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
