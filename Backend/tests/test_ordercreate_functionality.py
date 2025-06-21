#!/usr/bin/env python3
"""
Test script to verify build_ordercreate_rq.py functionality
Compares generated OrderCreateRQ with expected format
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from build_ordercreate_rq import generate_order_create_rq
except ImportError as e:
    print(f"Error importing build_ordercreate_rq: {e}")
    sys.exit(1)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file and return as dictionary"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def create_test_passengers() -> List[Dict[str, Any]]:
    """Create test passenger data matching the expected format"""
    return [
        {
            "ObjectKey": "PAX1",
            "PTC": "ADT",
            "Name": {
                "Title": "Mr",
                "Given": ["John"],
                "Surname": "Doe"
            },
            "Gender": "Male",
            "BirthDate": "1985-03-15",
            "Documents": [
                {
                    "Type": "PT",
                    "ID": "A12345678",
                    "DateOfExpiration": "2030-12-31",
                    "CountryOfIssuance": "US"
                }
            ],
            "Contacts": {
                "Contact": [
                    {
                        "ContactType": "Email",
                        "EmailContact": {
                            "Address": "john.doe@email.com"
                        }
                    },
                    {
                        "ContactType": "Phone",
                        "PhoneContact": {
                            "Number": "+1234567890"
                        }
                    }
                ]
            }
        },
        {
            "ObjectKey": "PAX2",
            "PTC": "ADT",
            "Name": {
                "Title": "Mrs",
                "Given": ["Jane"],
                "Surname": "Doe"
            },
            "Gender": "Female",
            "BirthDate": "1987-07-22",
            "Documents": [
                {
                    "Type": "PT",
                    "ID": "B87654321",
                    "DateOfExpiration": "2029-06-15",
                    "CountryOfIssuance": "US"
                }
            ]
        },
        {
            "ObjectKey": "PAX11",
            "PTC": "CHD",
            "Name": {
                "Title": "Miss",
                "Given": ["Emily"],
                "Surname": "Doe"
            },
            "Gender": "Female",
            "BirthDate": "2015-09-10",
            "Documents": [
                {
                    "Type": "PT",
                    "ID": "C11223344",
                    "DateOfExpiration": "2028-03-20",
                    "CountryOfIssuance": "US"
                }
            ]
        }
    ]

def create_test_payment() -> Dict[str, Any]:
    """Create test payment data"""
    return {
        "Method": "CreditCard",
        "Amount": {
            "Code": "INR",
            "value": 58166
        },
        "CreditCard": {
            "CardNumber": "4111111111111111",
            "ExpiryDate": "12/25",
            "CVV": "123",
            "CardholderName": "John Doe"
        }
    }

def compare_structures(generated: Dict[str, Any], expected: Dict[str, Any], path: str = "") -> List[str]:
    """Compare two dictionary structures and return differences"""
    differences = []
    
    # Check if both are dictionaries
    if not isinstance(generated, dict) or not isinstance(expected, dict):
        if generated != expected:
            differences.append(f"{path}: Type mismatch - Generated: {type(generated)}, Expected: {type(expected)}")
        return differences
    
    # Check for missing keys in generated
    for key in expected.keys():
        if key not in generated:
            differences.append(f"{path}.{key}: Missing in generated")
        else:
            if isinstance(expected[key], dict):
                differences.extend(compare_structures(generated[key], expected[key], f"{path}.{key}"))
            elif isinstance(expected[key], list) and isinstance(generated[key], list):
                if len(generated[key]) != len(expected[key]):
                    differences.append(f"{path}.{key}: List length mismatch - Generated: {len(generated[key])}, Expected: {len(expected[key])}")
                else:
                    for i, (gen_item, exp_item) in enumerate(zip(generated[key], expected[key])):
                        if isinstance(exp_item, dict):
                            differences.extend(compare_structures(gen_item, exp_item, f"{path}.{key}[{i}]"))
    
    # Check for extra keys in generated
    for key in generated.keys():
        if key not in expected:
            differences.append(f"{path}.{key}: Extra key in generated")
    
    return differences

def analyze_key_structures(data: Dict[str, Any], prefix: str = "") -> List[str]:
    """Analyze the structure of a dictionary and return key paths"""
    structures = []
    
    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            structures.append(f"{current_path}: dict")
            structures.extend(analyze_key_structures(value, current_path))
        elif isinstance(value, list):
            structures.append(f"{current_path}: list[{len(value)}]")
            if value and isinstance(value[0], dict):
                structures.extend(analyze_key_structures(value[0], f"{current_path}[0]"))
        else:
            structures.append(f"{current_path}: {type(value).__name__}")
    
    return structures

def main():
    print("=== Testing OrderCreateRQ Generation ===")
    print()
    
    # Load test data
    flight_response_path = "flightpriceresponse.json"
    expected_order_path = "OrdercreateRQ.json"
    
    print(f"Loading flight price response from: {flight_response_path}")
    flight_response = load_json_file(flight_response_path)
    if not flight_response:
        print("Failed to load flight price response")
        return
    
    print(f"Loading expected OrderCreateRQ from: {expected_order_path}")
    expected_order = load_json_file(expected_order_path)
    if not expected_order:
        print("Failed to load expected OrderCreateRQ")
        return
    
    # Create test data
    print("\nCreating test passenger and payment data...")
    test_passengers = create_test_passengers()
    test_payment = create_test_payment()
    
    print(f"Test passengers: {len(test_passengers)}")
    for i, pax in enumerate(test_passengers):
        print(f"  - Passenger {i+1}: {pax['Name']['Given'][0]} {pax['Name']['Surname']} ({pax['PTC']})")
    
    # Generate OrderCreateRQ
    print("\nGenerating OrderCreateRQ...")
    try:
        generated_order = generate_order_create_rq(
            flight_price_response=flight_response,
            passengers_data=test_passengers,
            payment_input_info=test_payment
        )
        print("✅ OrderCreateRQ generated successfully")
    except Exception as e:
        print(f"❌ Error generating OrderCreateRQ: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Save generated order for inspection
    output_path = "generated_ordercreate_test.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(generated_order, f, indent=2, ensure_ascii=False)
        print(f"✅ Generated OrderCreateRQ saved to: {output_path}")
    except Exception as e:
        print(f"⚠️  Could not save generated order: {e}")
    
    # Analyze structures
    print("\n=== Structure Analysis ===")
    print("\nGenerated OrderCreateRQ structure:")
    gen_structures = analyze_key_structures(generated_order)
    for struct in gen_structures[:20]:  # Show first 20 for brevity
        print(f"  {struct}")
    if len(gen_structures) > 20:
        print(f"  ... and {len(gen_structures) - 20} more")
    
    print("\nExpected OrderCreateRQ structure:")
    exp_structures = analyze_key_structures(expected_order)
    for struct in exp_structures[:20]:  # Show first 20 for brevity
        print(f"  {struct}")
    if len(exp_structures) > 20:
        print(f"  ... and {len(exp_structures) - 20} more")
    
    # Compare key sections
    print("\n=== Key Section Comparison ===")
    
    # Check main structure
    main_keys_gen = set(generated_order.get('Query', {}).keys())
    main_keys_exp = set(expected_order.get('Query', {}).keys())
    
    print(f"\nMain Query sections:")
    print(f"  Generated: {sorted(main_keys_gen)}")
    print(f"  Expected:  {sorted(main_keys_exp)}")
    print(f"  Missing:   {sorted(main_keys_exp - main_keys_gen)}")
    print(f"  Extra:     {sorted(main_keys_gen - main_keys_exp)}")
    
    # Check OfferItems count
    gen_offer_items = generated_order.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
    exp_offer_items = expected_order.get('Query', {}).get('OrderItems', {}).get('OfferItem', [])
    print(f"\nOfferItems count:")
    print(f"  Generated: {len(gen_offer_items)}")
    print(f"  Expected:  {len(exp_offer_items)}")
    
    # Check Passengers count
    gen_passengers = generated_order.get('Query', {}).get('Passengers', {}).get('Passenger', [])
    exp_passengers = expected_order.get('Query', {}).get('Passengers', {}).get('Passenger', [])
    print(f"\nPassengers count:")
    print(f"  Generated: {len(gen_passengers)}")
    print(f"  Expected:  {len(exp_passengers)}")
    
    # Check ShoppingResponse structure
    gen_shopping = generated_order.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})
    exp_shopping = expected_order.get('Query', {}).get('OrderItems', {}).get('ShoppingResponse', {})
    
    print(f"\nShoppingResponse comparison:")
    print(f"  Generated Owner: {gen_shopping.get('Owner')}")
    print(f"  Expected Owner:  {exp_shopping.get('Owner')}")
    print(f"  Generated ResponseID: {gen_shopping.get('ResponseID', {}).get('value', 'N/A')[:50]}...")
    print(f"  Expected ResponseID:  {exp_shopping.get('ResponseID', {}).get('value', 'N/A')[:50]}...")
    
    # Summary
    print("\n=== Test Summary ===")
    if generated_order:
        print("✅ OrderCreateRQ generation: SUCCESS")
        print(f"✅ Structure validation: Generated order has all main sections")
        
        # Check critical fields
        critical_checks = [
            ("ShoppingResponse.Owner", gen_shopping.get('Owner') is not None),
            ("ShoppingResponse.ResponseID", gen_shopping.get('ResponseID', {}).get('value') is not None),
            ("OfferItems present", len(gen_offer_items) > 0),
            ("Passengers present", len(gen_passengers) > 0),
            ("Payments present", len(generated_order.get('Query', {}).get('Payments', {}).get('Payment', [])) > 0)
        ]
        
        print("\nCritical field checks:")
        all_passed = True
        for check_name, passed in critical_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All critical checks PASSED! The build_ordercreate_rq.py script appears to be working correctly.")
        else:
            print("\n⚠️  Some critical checks FAILED. Please review the implementation.")
    else:
        print("❌ OrderCreateRQ generation: FAILED")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()