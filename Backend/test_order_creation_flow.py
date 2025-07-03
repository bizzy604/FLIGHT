#!/usr/bin/env python3
"""
Test script for multi-airline order creation flow.
Tests the enhanced order creation functionality with multi-airline flight price responses.
"""

import json
import sys
import os

# Add the Backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.build_ordercreate_rq import generate_order_create_rq
from scripts.build_flightprice_rq import build_flight_price_request

def load_test_data():
    """Load test data from the multi-airline air shopping response."""
    try:
        # Try different possible paths
        possible_paths = [
            'postman/airshopingresponse.json',
            '../postman/airshopingresponse.json',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'postman', 'airshopingresponse.json')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)

        print("Error: airshopingresponse.json not found in any expected location")
        return None
    except Exception as e:
        print(f"Error loading test data: {e}")
        return None

def create_mock_flight_price_response(airshopping_response, offer_index=0):
    """Create a mock flight price response for testing."""
    try:
        # Build a flight price request first
        flight_price_request = build_flight_price_request(
            airshopping_response=airshopping_response,
            selected_offer_index=offer_index
        )
        
        # Extract key information for mock response
        data_lists = flight_price_request.get('DataLists', {})
        shopping_response_id = flight_price_request.get('ShoppingResponseID', {})
        
        # Create a mock flight price response structure
        mock_response = {
            "PricedFlightOffers": {
                "PricedFlightOffer": [{
                    "OfferID": {
                        "Owner": shopping_response_id.get('Owner', 'UNKNOWN'),
                        "value": f"MOCK_OFFER_{offer_index}",
                        "Channel": "NDC"
                    },
                    "OfferPrice": [{
                        "OfferItemID": {
                            "Owner": shopping_response_id.get('Owner', 'UNKNOWN'),
                            "value": f"MOCK_ITEM_{offer_index}"
                        },
                        "RequestedDate": {
                            "PriceDetail": {
                                "TotalAmount": {
                                    "SimpleCurrencyPrice": {
                                        "Code": "USD",
                                        "value": 500.00
                                    }
                                }
                            },
                            "Associations": [{
                                "AssociatedTraveler": {
                                    "TravelerReferences": ["PAX1"]
                                }
                            }]
                        }
                    }]
                }]
            },
            "DataLists": data_lists,
            "ShoppingResponseID": shopping_response_id,
            "Metadata": flight_price_request.get('Metadata', {})
        }
        
        return mock_response
        
    except Exception as e:
        print(f"Error creating mock flight price response: {e}")
        return None

def create_test_passenger_data():
    """Create test passenger data."""
    return [{
        "PTC": "ADT",
        "ObjectKey": "PAX1",
        "Individual": {
            "GivenName": ["John"],
            "Surname": "Doe",
            "Birthdate": "1990-01-01",
            "Gender": "Male"
        },
        "IdentityDocument": {
            "IdentityDocumentNumber": "P123456789",
            "IdentityDocumentType": "PT",
            "IssuingCountryCode": "US",
            "ExpiryDate": "2030-01-01"
        },
        "ContactInfoRef": "CONTACT1"
    }]

def create_test_payment_data():
    """Create test payment data."""
    return {
        "MethodType": "CASH",
        "Details": {
            "CashInd": True
        }
    }

def test_order_creation_for_airline(airshopping_response, airline_code, offer_index):
    """Test order creation for a specific airline."""
    print(f"\n--- Testing Order Creation for Airline: {airline_code} ---")
    print(f"  Offer Index: {offer_index}")
    
    try:
        # Create mock flight price response
        flight_price_response = create_mock_flight_price_response(airshopping_response, offer_index)
        if not flight_price_response:
            print(f"  ❌ Failed to create mock flight price response")
            return False
        
        # Create test data
        passengers_data = create_test_passenger_data()
        payment_data = create_test_payment_data()
        
        # Generate OrderCreate request
        order_create_request = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )
        
        # Validate the generated request
        validation_result = validate_order_create_request(order_create_request, airline_code)
        
        if validation_result['valid']:
            print(f"  ✅ OrderCreate request generated successfully")
            print(f"  ✅ Airline: {validation_result['airline']}")
            print(f"  ✅ Passengers: {validation_result['passenger_count']}")
            print(f"  ✅ Payment Amount: {validation_result['payment_amount']}")
            
            # Save the request for inspection
            filename = f"test_ordercreate_{airline_code}_{offer_index}.json"
            with open(filename, 'w') as f:
                json.dump(order_create_request, f, indent=2)
            print(f"  💾 Saved: {filename}")
            
            return True
        else:
            print(f"  ❌ Validation failed: {validation_result['issues']}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def validate_order_create_request(request, expected_airline):
    """Validate the generated OrderCreate request."""
    issues = []
    
    try:
        # Check basic structure
        if 'Query' not in request:
            issues.append("Missing Query section")
        
        query = request.get('Query', {})
        
        # Check OrderItems
        order_items = query.get('OrderItems', {})
        if not order_items:
            issues.append("Missing OrderItems")
        
        # Check ShoppingResponse
        shopping_response = order_items.get('ShoppingResponse', {})
        airline = shopping_response.get('Owner')
        if not airline:
            issues.append("Missing airline in ShoppingResponse.Owner")
        elif airline != expected_airline:
            issues.append(f"Airline mismatch: expected {expected_airline}, got {airline}")
        
        # Check Passengers
        passengers = query.get('Passengers', {}).get('Passenger', [])
        passenger_count = len(passengers) if isinstance(passengers, list) else (1 if passengers else 0)
        if passenger_count == 0:
            issues.append("No passengers found")
        
        # Check Payments
        payments = query.get('Payments', {}).get('Payment', [])
        payment_count = len(payments) if isinstance(payments, list) else (1 if payments else 0)
        if payment_count == 0:
            issues.append("No payments found")
        
        payment_amount = "Unknown"
        if payments:
            first_payment = payments[0] if isinstance(payments, list) else payments
            amount_obj = first_payment.get('Amount', {})
            payment_amount = f"{amount_obj.get('value', 0)} {amount_obj.get('Code', 'USD')}"
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'airline': airline,
            'passenger_count': passenger_count,
            'payment_amount': payment_amount
        }
        
    except Exception as e:
        return {
            'valid': False,
            'issues': [f"Validation error: {e}"],
            'airline': 'Unknown',
            'passenger_count': 0,
            'payment_amount': 'Unknown'
        }

def main():
    """Main test function."""
    print("Multi-Airline Order Creation Flow Test")
    print("=" * 50)
    
    # Load test data
    airshopping_response = load_test_data()
    if not airshopping_response:
        return
    
    # Test airlines and their offer indices (from previous testing)
    test_cases = [
        ('KL', 0),
        ('LHG', 3),
        ('AF', 81),
        ('ET', 126),
        ('QR', 168),
        ('KQ', 257),
        ('EK', 297)
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for airline_code, offer_index in test_cases:
        success = test_order_creation_for_airline(airshopping_response, airline_code, offer_index)
        if success:
            successful_tests += 1
    
    print(f"\n" + "=" * 50)
    print(f"✅ ORDER CREATION TEST COMPLETE")
    print(f"Successful: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All order creation tests passed!")
    else:
        print(f"⚠️  {total_tests - successful_tests} tests failed")

if __name__ == "__main__":
    main()
