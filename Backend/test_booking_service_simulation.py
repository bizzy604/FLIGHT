#!/usr/bin/env python3
"""
Test script to simulate exactly what the booking service is doing
to debug why generate_order_create_rq is throwing an exception.
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

def simulate_booking_service_data_transformation(raw_response):
    """Simulate the data transformations that the booking service does."""
    
    # This simulates what the booking service does to create enhanced_flight_price_response
    enhanced_flight_price_response = raw_response.copy()
    
    # Simulate passenger transformation (from frontend format to backend format)
    transformed_passengers = [
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
    
    # Simulate payment transformation (from frontend format to backend format)
    transformed_payment = {
        "payment_method": "CASH",
        "MethodType": "CASH",
        "Details": {
            "CashInd": True
        }
    }
    
    return enhanced_flight_price_response, transformed_passengers, transformed_payment

def main():
    print("=== Simulating Booking Service Call to generate_order_create_rq ===")
    
    try:
        print("Loading actual raw flight price response from logs...")
        raw_response = load_actual_raw_response()
        
        print("Simulating booking service data transformations...")
        enhanced_flight_price_response, transformed_passengers, transformed_payment = simulate_booking_service_data_transformation(raw_response)
        
        print(f"Enhanced flight price response keys: {list(enhanced_flight_price_response.keys())}")
        print(f"Enhanced flight price response type: {type(enhanced_flight_price_response)}")
        print(f"Transformed passengers count: {len(transformed_passengers)}")
        print(f"Transformed payment keys: {list(transformed_payment.keys())}")
        
        print("\n=== CALLING generate_order_create_rq (EXACTLY LIKE BOOKING SERVICE) ===")
        payload = generate_order_create_rq(
            flight_price_response=enhanced_flight_price_response,
            passengers_data=transformed_passengers,
            payment_input_info=transformed_payment
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
        with open('booking_service_simulation_payload.json', 'w') as f:
            json.dump(payload, f, indent=2, default=str)
        
        print("📁 Saved generated payload to 'booking_service_simulation_payload.json'")
        
    except Exception as e:
        print(f"❌ Error occurred (THIS IS WHY FALLBACK IS USED): {e}")
        import traceback
        traceback.print_exc()
        print("\n🔍 This exception is why the booking service falls back to manual construction!")

if __name__ == "__main__":
    main()
