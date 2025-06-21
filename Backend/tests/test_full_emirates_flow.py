#!/usr/bin/env python3

import sys
import os
import json

# Add the scripts directory to the path
sys.path.append('../scripts')

from build_ordercreate_rq import generate_order_create_rq

def test_full_emirates_flow():
    """Test the full Emirates flow with ObjectKey fallback"""
    
    # Load the actual Emirates response
    with open('flightpriceresponse.json', 'r') as f:
        emirates_full_response = json.load(f)
    
    # Create test input data
    test_input = {
        'passengers': [
            {
                "PTC": "ADT",
                "Name": {
                    "Title": "Mr",
                    "Given": ["John"],
                    "Surname": "Doe"
                },
                "Gender": "Male",
                "BirthDate": "1985-03-15",
                "Contacts": {
                    "Email": "john.doe@example.com",
                    "Phone": "+1234567890"
                },
                "PassengerIDInfo": {
                    "PassengerDocument": [{
                        "Type": "PT",
                        "ID": "A12345678",
                        "DateOfExpiration": "2030-05-15",
                        "CountryOfIssuance": "US"
                    }]
                }
            },
            {
                "PTC": "ADT",
                "Name": {
                    "Title": "Mrs",
                    "Given": ["Jane"],
                    "Surname": "Doe"
                },
                "Gender": "Female",
                "BirthDate": "1987-07-22",
                "Contacts": {
                    "Email": "jane.doe@example.com",
                    "Phone": "+1234567891"
                },
                "PassengerIDInfo": {
                    "PassengerDocument": [{
                        "Type": "PT",
                        "ID": "B87654321",
                        "DateOfExpiration": "2029-06-15",
                        "CountryOfIssuance": "US"
                    }]
                }
            },
            {
                "PTC": "CHD",
                "Name": {
                    "Title": "Miss",
                    "Given": ["Emily"],
                    "Surname": "Doe"
                },
                "Gender": "Female",
                "BirthDate": "2015-01-01",
                "Contacts": {
                    "Email": "emily.doe@example.com",
                    "Phone": "+1234567892"
                },
                "PassengerIDInfo": {
                    "PassengerDocument": [{
                        "Type": "PT",
                        "ID": "C11111111",
                        "DateOfExpiration": "2028-01-01",
                        "CountryOfIssuance": "US"
                    }]
                }
            }
        ],
        'selected_offer_id': 'OFFER_1',
        'payment_info': {
            "Type": "CC",
            "Method": {
                "PaymentCard": {
                    "CardCode": "VI",
                    "CardNumber": "4111111111111111",
                    "SeriesCode": "123",
                    "CardHolderName": "John Doe",
                    "EffectiveDate": "2023-01",
                    "ExpiryDate": "2025-12"
                }
            },
            "Amount": {
                "value": "1200.00",
                "Code": "USD"
            }
        }
    }
    
    print("=== Full Emirates Flow Test ===")
    
    try:
        # Generate the OrderCreateRQ
        result = generate_order_create_rq(
            flight_price_response=emirates_full_response,
            passengers_data=test_input['passengers'],
            payment_input_info=test_input['payment_info']
        )
        
        # Debug: Print the result structure
        print(f"Result keys: {list(result.keys())}")
        if 'DataLists' in result:
            print(f"DataLists keys: {list(result['DataLists'].keys())}")
        
        # Save the result to a file for debugging
        with open('debug_full_emirates_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("Result saved to debug_full_emirates_result.json")
        
        # Check if passengers exist in the result
        if 'Query' in result and 'Passengers' in result['Query']:
            passengers = result['Query']['Passengers']['Passenger']
            if not isinstance(passengers, list):
                passengers = [passengers]
            print(f"Found {len(passengers)} passengers")
            
            # Check ObjectKeys
            object_keys = [p.get('ObjectKey') for p in passengers]
            print(f"ObjectKeys: {object_keys}")
            
            # Verify the expected pattern: T1 from Emirates, PAX2 and PAX3 as fallbacks
            expected_keys = ['T1', 'PAX2', 'PAX3']
            if object_keys == expected_keys:
                print("✅ Emirates ObjectKey flow test PASSED!")
                print("✅ Correct ObjectKey mapping: T1 from airline, PAX2/PAX3 as fallbacks")
                return True
            else:
                print(f"❌ Expected {expected_keys}, got {object_keys}")
                print("❌ Emirates ObjectKey flow test FAILED!")
                return False
        else:
            print("❌ No passengers found in result")
            if 'Query' in result:
                query_keys = list(result['Query'].keys())
                print(f"Available Query keys: {query_keys}")
            print("❌ Emirates ObjectKey flow test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Error generating OrderCreateRQ: {e}")
        return False

if __name__ == "__main__":
    success = test_full_emirates_flow()
    if success:
        print("\n🎉 Emirates ObjectKey flow test PASSED!")
        print("The system correctly:")
        print("  ✅ Uses Emirates ObjectKey 'T1' for the first passenger")
        print("  ✅ Generates fallback ObjectKeys for additional passengers")
        print("  ✅ Handles mixed airline ObjectKey formats gracefully")
    else:
        print("\n❌ Emirates ObjectKey flow test FAILED!")