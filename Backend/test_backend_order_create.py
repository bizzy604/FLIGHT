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
    """Load the actual raw flight price response from the known good data."""
    # Use the known good KQ flight price response structure
    raw_response = {
        "DataLists": {
            "AnonymousTravelerList": {
                "AnonymousTraveler": [
                    {"ObjectKey": "PAX1", "PTC": {"value": "ADT"}}
                ]
            },
            "FlightSegmentList": {
                "FlightSegment": [
                    {
                        "SegmentKey": "SEG2",
                        "Departure": {
                            "AirportCode": {"value": "NBO"},
                            "Date": "2025-07-09T09:05:00.000",
                            "Time": "09:05"
                        },
                        "Arrival": {
                            "AirportCode": {"value": "LHR"},
                            "Date": "2025-07-09T16:15:00.000",
                            "Time": "16:15"
                        },
                        "MarketingCarrier": {
                            "AirlineID": {"value": "KQ"},
                            "FlightNumber": {"value": "100"},
                            "Name": "Kenya Airways"
                        }
                    }
                ]
            }
        },
        "Document": {
            "Name": "NDC AirShoppingRS",
            "ReferenceVersion": "1.0"
        },
        "PricedFlightOffers": {
            "PricedFlightOffer": [
                {
                    "OfferID": "1H1KQZ_GNV1II47RJNSXHL19XQF91I7GOUL",
                    "OfferPrice": {
                        "RequestedDate": "2025-07-02",
                        "TotalAmount": {
                            "DetailCurrencyPrice": {
                                "Total": {
                                    "Code": "INR",
                                    "value": 49434
                                }
                            }
                        }
                    }
                }
            ]
        },
        "ShoppingResponseID": "test-shopping-response-id"
    }
    return raw_response

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
