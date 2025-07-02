#!/usr/bin/env python3
"""
Test script to test the build_ordercreate_rq function with the actual raw flight price response
from the logs to debug why it's falling back to manual construction.
"""

import json
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def load_actual_raw_response():
    """Load the actual raw flight price response from the logs file."""
    with open('../logs', 'r') as f:
        data = json.load(f)
    
    # Extract the raw_flight_price_response
    raw_response = data.get('raw_flight_price_response', {})
    
    print(f"Raw response keys: {list(raw_response.keys())}")
    print(f"Raw response type: {type(raw_response)}")
    
    return raw_response

def create_test_passengers():
    """Create test passenger data."""
    return [
        {
            "type": "adult",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "dob": "1990-01-01",
            "gender": "male",
            "documentNumber": "P123456789",
            "expiryDate": "2030-01-01",
            "nationality": "US",
            "ObjectKey": "PAX1"
        }
    ]

def create_test_payment():
    """Create test payment data."""
    return {
        "payment_method": "CASH",
        "MethodType": "CASH",
        "Details": {
            "CashInd": True
        }
    }

def main():
    print("=== Testing build_ordercreate_rq with ACTUAL raw flight price response ===")
    
    try:
        print("Loading actual raw flight price response from logs...")
        raw_response = load_actual_raw_response()
        
        print("Creating test passengers and payment data...")
        passengers_data = create_test_passengers()
        payment_input_info = create_test_payment()
        
        print(f"Raw response structure: {list(raw_response.keys())}")
        print(f"Number of passengers: {len(passengers_data)}")
        print(f"Payment method: {payment_input_info['payment_method']}")
        
        print("\n=== CALLING generate_order_create_rq ===")
        payload = generate_order_create_rq(
            flight_price_response=raw_response,
            passengers_data=passengers_data,
            payment_input_info=payment_input_info
        )
        
        print("✅ Successfully generated payload!")
        print(f"Payload keys: {list(payload.keys())}")
        
        # Check key values in the payload
        if 'Query' in payload and 'OrderItems' in payload['Query']:
            order_items = payload['Query']['OrderItems']
            if 'ShoppingResponse' in order_items:
                shopping_response = order_items['ShoppingResponse']
                print(f"Generated Owner: {shopping_response.get('Owner')}")
                print(f"Generated ResponseID: {shopping_response.get('ResponseID', {}).get('value')}")
                
                if 'Offers' in shopping_response and 'Offer' in shopping_response['Offers']:
                    offers = shopping_response['Offers']['Offer']
                    if offers and len(offers) > 0:
                        offer = offers[0]
                        if 'OfferID' in offer:
                            offer_id = offer['OfferID']
                            print(f"Generated OfferID: {offer_id.get('value')}")
                            print(f"Generated OfferID Owner: {offer_id.get('Owner')}")
        
        # Save the generated payload for inspection
        with open('actual_raw_response_payload.json', 'w') as f:
            json.dump(payload, f, indent=2, default=str)
        
        print("📁 Saved generated payload to 'actual_raw_response_payload.json'")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
