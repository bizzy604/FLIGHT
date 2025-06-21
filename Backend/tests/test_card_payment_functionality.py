#!/usr/bin/env python3
"""
Test script to verify OrderCreateRQ generation with PaymentCard method.
This script tests the build_ordercreate_rq.py functionality with card payment.
"""

import json
import os
import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent / 'scripts'))

from build_ordercreate_rq import generate_order_create_rq

def test_card_payment_generation():
    """
    Test OrderCreateRQ generation with PaymentCard method
    """
    print("Testing OrderCreateRQ generation with PaymentCard...")
    
    # Load test data
    test_data_path = Path(__file__).parent / 'tests' / 'flightpriceresponse.json'
    
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            flight_price_response = json.load(f)
    except FileNotFoundError:
        print(f"Error: Test data file not found at {test_data_path}")
        return False
    
    # Define test passengers
    passengers_data = [
        {
            "ObjectKey": "T1", 
            "PTC": "ADT",
            "Name": {"Title": "Mr", "Given": ["AMONI"], "Surname": "KEVIN"},
            "Gender": "Male",
            "BirthDate": "1980-05-25",
            "Contacts": { 
                "Contact": [{
                    "PhoneContact": {"Number": [{"CountryCode": "254", "value": "0700000000"}], "Application": "Home"},
                    "EmailContact": {"Address": {"value": "kevinamoni20@example.com"}},
                    "AddressContact": {"Street": ["Nairobi, Kenya 30500"],"PostalCode": "301","CityName": "Nairobi","CountryCode": {"value": "KE"}}
                }]
            },
            "Documents": [{
                "Type": "PT", "ID": "A12345678", "DateOfExpiration": "2030-12-31", 
                "CountryOfIssuance": "KE", "DateOfIssue": "2020-01-15", "CountryOfResidence": "KE"
            }]
        },
        {
            "ObjectKey": "T2", "PTC": "ADT",
            "Name": {"Title": "Mrs", "Given": ["REBECCA"], "Surname": "MIANO"},
            "Gender": "Female", "BirthDate": "1998-05-25",
            "Contacts": { 
                "Contact": [{
                    "PhoneContact": {"Number": [{"CountryCode": "254", "value": "0700000001"}], "Application": "Home"},
                    "EmailContact": {"Address": {"value": "rebecca.miano@example.com"}},
                    "AddressContact": {"Street": ["Nairobi, Kenya 30500"],"PostalCode": "301","CityName": "Nairobi","CountryCode": {"value": "KE"}}
                }]
            },
            "Documents": [{"Type": "PT", "ID": "B87654321", "DateOfExpiration": "2028-11-20", "CountryOfIssuance": "GB"}]
        }
    ]
    
    # Define PaymentCard payment info
    payment_info_card = {
        "MethodType": "PaymentCard",
        "Details": {
            "CardCode": "VI",  # Visa
            "CardNumberToken": "tok_test_card_4242424242424242",
            "CardHolderName": {"value": "Amoni Kevin", "refs": []},
            "EffectiveExpireDate": {"Expiration": "1228"},  # December 2028
            "CardType": "Credit"
        }
    }
    
    # Define Cash payment info for comparison
    payment_info_cash = {
        "MethodType": "Cash",
        "Details": {"CashInd": True}
    }
    
    try:
        # Generate OrderCreateRQ with PaymentCard
        print("\n1. Generating OrderCreateRQ with PaymentCard...")
        order_rq_card = generate_order_create_rq(
            flight_price_response,
            passengers_data,
            payment_info_card
        )
        
        # Generate OrderCreateRQ with Cash for comparison
        print("2. Generating OrderCreateRQ with Cash for comparison...")
        order_rq_cash = generate_order_create_rq(
            flight_price_response,
            passengers_data,
            payment_info_cash
        )
        
        # Save both versions
        output_dir = Path(__file__).parent / 'tests'
        
        card_output_path = output_dir / 'test_ordercreate_card.json'
        with open(card_output_path, 'w', encoding='utf-8') as f:
            json.dump(order_rq_card, f, indent=2, ensure_ascii=False)
        
        cash_output_path = output_dir / 'test_ordercreate_cash.json'
        with open(cash_output_path, 'w', encoding='utf-8') as f:
            json.dump(order_rq_cash, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ PaymentCard OrderCreateRQ saved to: {card_output_path}")
        print(f"✅ Cash OrderCreateRQ saved to: {cash_output_path}")
        
        # Validate PaymentCard structure
        print("\n3. Validating PaymentCard structure...")
        
        # Check if payment section exists
        payments_card = order_rq_card.get('Query', {}).get('Payments', {}).get('Payment', [])
        if not payments_card:
            print("❌ No Payment section found in PaymentCard OrderCreateRQ")
            return False
        
        payment_method_card = payments_card[0].get('Method', {})
        if 'PaymentCard' not in payment_method_card:
            print("❌ PaymentCard method not found in payment section")
            return False
        
        card_details = payment_method_card['PaymentCard']
        
        # Validate required PaymentCard fields
        required_fields = ['CardNumber', 'EffectiveExpireDate', 'CardType', 'CardCode', 'CardHolderName']
        missing_fields = []
        
        for field in required_fields:
            if field not in card_details:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required PaymentCard fields: {missing_fields}")
            return False
        
        # Validate specific field values
        validations = [
            (card_details['CardCode'] == 'VI', "CardCode should be 'VI' for Visa"),
            (card_details['CardType'] == 'Credit', "CardType should be 'Credit'"),
            ('value' in card_details['CardNumber'], "CardNumber should have 'value' field"),
            ('Expiration' in card_details['EffectiveExpireDate'], "EffectiveExpireDate should have 'Expiration' field"),
            ('value' in card_details['CardHolderName'], "CardHolderName should have 'value' field")
        ]
        
        for validation, message in validations:
            if not validation:
                print(f"❌ {message}")
                return False
        
        print("✅ All PaymentCard fields are present and valid")
        
        # Compare with Cash payment
        print("\n4. Comparing PaymentCard vs Cash payment structures...")
        
        payments_cash = order_rq_cash.get('Query', {}).get('Payments', {}).get('Payment', [])
        payment_method_cash = payments_cash[0].get('Method', {})
        
        if 'Cash' in payment_method_cash:
            print("✅ Cash payment method correctly generated for comparison")
        else:
            print("❌ Cash payment method not found in comparison OrderCreateRQ")
        
        # Check amounts are the same
        card_amount = payments_card[0].get('Amount', {}).get('value')
        cash_amount = payments_cash[0].get('Amount', {}).get('value')
        
        if card_amount == cash_amount:
            print(f"✅ Payment amounts match: {card_amount} {payments_card[0].get('Amount', {}).get('Code')}")
        else:
            print(f"❌ Payment amounts differ: Card={card_amount}, Cash={cash_amount}")
        
        print("\n🎉 PaymentCard functionality test completed successfully!")
        print("\nKey findings:")
        print(f"  • PaymentCard method: {card_details['CardCode']} {card_details['CardType']}")
        print(f"  • Card holder: {card_details['CardHolderName']['value']}")
        print(f"  • Expiration: {card_details['EffectiveExpireDate']['Expiration']}")
        print(f"  • Token: {card_details['CardNumber']['value']}")
        print(f"  • Amount: {card_amount} {payments_card[0].get('Amount', {}).get('Code')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during OrderCreateRQ generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_card_payment_generation()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)