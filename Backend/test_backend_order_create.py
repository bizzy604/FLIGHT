#!/usr/bin/env python3
"""
Test script to directly call the backend order-create endpoint
to verify it's working and see the debug logs.
"""

import json
import requests
import sys
import os

def load_actual_raw_response():
    """Load the actual raw flight price response from the KQ test file."""
    try:
        # Load the actual KQ flight price response from the test file
        test_file_path = os.path.join(os.path.dirname(__file__), 'tests', 'FlightPriceRS_KQ.json')
        with open(test_file_path, 'r', encoding='utf-8') as f:
            raw_response = json.load(f)

        print(f"✅ Loaded actual KQ flight price response from: {test_file_path}")
        print(f"   - Document Name: {raw_response.get('Document', {}).get('Name', 'Unknown')}")
        print(f"   - OfferID: {raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferID', {}).get('value', 'Unknown')}")
        print(f"   - Number of OfferPrice items: {len(raw_response.get('PricedFlightOffers', {}).get('PricedFlightOffer', [{}])[0].get('OfferPrice', []))}")

        return raw_response

    except FileNotFoundError:
        print(f"❌ Could not find KQ test file at: {test_file_path}")

def test_backend_order_create():
    """Test the backend order-create endpoint directly."""
    
    print("=== Testing Backend Order-Create Endpoint ===")
    
    # Load the actual raw flight price response
    raw_response = load_actual_raw_response()
    
    # Prepare test data that matches what the frontend sends
    test_data = {
        "flight_price_response": raw_response,
        "passengers": [
            {
                "type": "adult",
                "title": "mr",
                "firstName": "John",
                "lastName": "Doe",
                "dob": {"year": "1990", "month": "01", "day": "01"},
                "gender": "male",
                "nationality": "US",  # Added missing nationality field
                "documentNumber": "P123456789",
                "expiryDate": {"year": "2030", "month": "01", "day": "01"},
                "documentType": "passport",
                "issuingCountry": "US"
            }
        ],
        "payment": {
            "payment_method": "CASH"
        },
        "contact_info": {
            "phone": "1234567890",
            "phoneCountryCode": "+1",
            "email": "john.doe@example.com",
            "street": "123 Main Street",  # Added missing street address
            "city": "New York",
            "state": "NY",
            "postalCode": "10001",
            "countryCode": "US"  # Fixed: should be countryCode, not country
        }
    }
    
    # Backend URL
    backend_url = "http://localhost:5000/api/verteil/order-create"
    
    print(f"Sending request to: {backend_url}")
    print(f"Data summary:")
    print(f"  - Flight price response keys: {list(raw_response.keys())}")
    print(f"  - Passengers count: {len(test_data['passengers'])}")
    print(f"  - Payment method: {test_data['payment']['payment_method']}")
    print(f"  - Contact email: {test_data['contact_info']['email']}")
    print(f"  - Passenger details: {test_data['passengers'][0]}")
    
    try:
        # Send the request
        response = requests.post(
            backend_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"\n=== Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Backend order-create endpoint is working!")
                
                # Check if we got the expected response structure
                if response_data.get('status') == 'success':
                    print("✅ Order creation was successful!")
                    
                    # Check if the response contains KQ airline data
                    booking_data = response_data.get('data', {})
                    if 'KQ' in str(booking_data):
                        print("✅ Response contains KQ airline data (correct)!")
                    else:
                        print("❌ Response does not contain KQ airline data")
                        
                else:
                    print(f"❌ Order creation failed: {response_data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Backend returned error status: {response.status_code}")
                
        except json.JSONDecodeError:
            print(f"❌ Response is not valid JSON: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend - is it running on localhost:5000?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out - backend might be processing or stuck")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_backend_order_create()
