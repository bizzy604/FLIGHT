#!/usr/bin/env python3
"""
Test script to generate OrderCreate payload using the proper build_ordercreate_rq.py function
with actual flight price response data.
"""

import json
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def load_test_data():
    """Load test flight price response data."""
    
    # Load the KQ flight price response
    with open('tests/FlightPriceRS_KQ.json', 'r') as f:
        flight_price_response = json.load(f)
    
    # Sample passenger data (similar to what we receive from frontend)
    passengers_data = [
        {
            "type": "adult",
            "title": "mr",
            "first_name": "AMONI",
            "last_name": "KEVIN",
            "date_of_birth": "1988-03-06",
            "gender": "male",
            "passport_number": "A3293EWNIIIH",
            "passport_expiry": "2033-06-05",
            "nationality": "DE"
        }
    ]
    
    # Sample payment info
    payment_input_info = {
        "payment_method": "CASH",
        "email": "kevinamoni20@gmail.com",
        "phone": "0796861525"
    }
    
    return flight_price_response, passengers_data, payment_input_info

def test_payload_generation():
    """Test the OrderCreate payload generation."""
    
    print("Loading test data...")
    flight_price_response, passengers_data, payment_input_info = load_test_data()
    
    print(f"Flight price response keys: {list(flight_price_response.keys())}")
    print(f"Number of passengers: {len(passengers_data)}")
    print(f"Payment method: {payment_input_info['payment_method']}")
    
    print("\nGenerating OrderCreate payload...")
    try:
        payload = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_input_info
        )
        
        print("✅ Successfully generated payload!")
        print(f"Payload keys: {list(payload.keys())}")
        
        # Save the generated payload for comparison
        with open('generated_ordercreate_payload.json', 'w') as f:
            json.dump(payload, f, indent=2, default=str)
        
        print("📁 Saved generated payload to 'generated_ordercreate_payload.json'")
        
        # Compare key structures with expected OrderCreateRQ.json
        print("\n=== STRUCTURE COMPARISON ===")
        
        # Load expected structure
        with open('../OrderCreateRQ.json', 'r') as f:
            expected = json.load(f)
        
        print(f"Expected top-level keys: {list(expected.keys())}")
        print(f"Generated top-level keys: {list(payload.keys())}")
        
        # Check if Query structure exists
        if 'Query' in payload:
            print("✅ Query structure found in generated payload")
            if 'OrderItems' in payload['Query']:
                print("✅ OrderItems structure found")
                if 'ShoppingResponse' in payload['Query']['OrderItems']:
                    print("✅ ShoppingResponse structure found")
                else:
                    print("❌ ShoppingResponse structure missing")
            else:
                print("❌ OrderItems structure missing")
        else:
            print("❌ Query structure missing from generated payload")
        
        # Show a sample of the generated payload
        print("\n=== GENERATED PAYLOAD SAMPLE ===")
        print(json.dumps(payload, indent=2, default=str)[:2000] + "...")
        
        return payload
        
    except Exception as e:
        print(f"❌ Error generating payload: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_payload_generation()
