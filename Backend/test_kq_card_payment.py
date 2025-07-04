#!/usr/bin/env python3
"""
Test script using real FlightPriceRS_KQ.json with card payment
Outputs the final OrderCreate request to a file for validation

This script:
1. Loads the real KQ flight price response
2. Creates sample passenger data matching the travelers in the response
3. Uses card payment method
4. Generates OrderCreate request
5. Outputs the result to a JSON file for validation

Author: FLIGHT Application
Created: 2025-07-03
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from scripts.build_ordercreate_rq import generate_order_create_rq


def load_kq_flight_price_response():
    """Load the real KQ flight price response from test file."""
    test_file_path = backend_dir / "tests" / "FlightPriceRS_KQ.json"
    
    try:
        with open(test_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: Could not find test file at {test_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in test file: {e}")
        return None


def create_passenger_data_for_kq_response():
    """Create passenger data matching the travelers in KQ response."""
    # Based on the KQ response, we have:
    # PAX11 - INF (Infant)
    # PAX1 - ADT (Adult)
    # PAX2 - ADT (Adult) 
    # PAX3 - CHD (Child)
    
    passengers_data = [
        {
            "PTC": "ADT",
            "ObjectKey": "PAX1",
            "Name": {
                "Title": "Mr",
                "Given": ["John"],
                "Surname": "Smith"
            },
            "Gender": "Male",
            "BirthDate": "1985-03-15",
            "Documents": [{
                "Type": "PT",
                "ID": "P123456789",
                "DateOfExpiration": "2030-03-15",
                "CountryOfIssuance": "US"
            }],
            "ContactInfo": {
                "EmailAddress": "john.smith@email.com",
                "Phone": {
                    "Number": "+1234567890",
                    "CountryCode": "1"
                }
            }
        },
        {
            "PTC": "ADT",
            "ObjectKey": "PAX2",
            "Name": {
                "Title": "Mrs",
                "Given": ["Jane"],
                "Surname": "Smith"
            },
            "Gender": "Female",
            "BirthDate": "1987-07-22",
            "Documents": [{
                "Type": "PT",
                "ID": "P987654321",
                "DateOfExpiration": "2030-07-22",
                "CountryOfIssuance": "US"
            }],
            "ContactInfo": {
                "EmailAddress": "jane.smith@email.com",
                "Phone": {
                    "Number": "+1234567891",
                    "CountryCode": "1"
                }
            }
        },
        {
            "PTC": "CHD",
            "ObjectKey": "PAX3",
            "Name": {
                "Title": "Miss",
                "Given": ["Emily"],
                "Surname": "Smith"
            },
            "Gender": "Female",
            "BirthDate": "2015-12-10",
            "Documents": [{
                "Type": "PT",
                "ID": "P456789123",
                "DateOfExpiration": "2030-12-10",
                "CountryOfIssuance": "US"
            }]
        },
        {
            "PTC": "INF",
            "ObjectKey": "PAX11",
            "Name": {
                "Title": "Master",
                "Given": ["Baby"],
                "Surname": "Smith"
            },
            "Gender": "Male",
            "BirthDate": "2024-08-15",
            "Documents": [{
                "Type": "PT",
                "ID": "P789123456",
                "DateOfExpiration": "2029-08-15",
                "CountryOfIssuance": "US"
            }]
        }
    ]
    
    return passengers_data


def create_card_payment_data():
    """Create comprehensive card payment data for testing."""
    return {
        "MethodType": "PAYMENTCARD",
        "Details": {
            "CardNumberToken": "4111111111111111",  # Test Visa card number
            "EffectiveExpireDate": {
                "Expiration": "1227",  # MMYY format (December 2027)
                "Effective": "0125"    # MMYY format (January 2025)
            },
            "CardType": "VI",  # Visa
            "CardCode": "123",  # CVV
            "CardHolderName": {
                "value": "John Smith",
                "refs": ["PAX1"]  # Reference to primary passenger
            },
            "CardHolderBillingAddress": {
                "Street": ["123 Main Street", "Suite 456"],
                "PostalCode": "12345",
                "CityName": "New York",
                "CountryCode": {"value": "US"}
            },
            "SeriesCode": {"value": "123"},
            "ProductTypeCode": ["CREDIT", "REWARDS"],
            "SecurePaymentVersion2": {
                "AuthenticationValue": "BwABBJQ1AgAAAAAgJDUCAAAAAAA=",
                "DirectoryServerTransactionId": "8a880dc0-d2d2-4067-bcb1-b08d1690b26e",
                "ElectronicCommerceIndicator": "05"
            }
        }
    }


def calculate_total_amount(flight_price_response):
    """Calculate total amount from flight price response."""
    total_amount = 0
    currency = "INR"  # Default from KQ response
    
    try:
        offers = flight_price_response.get("PricedFlightOffers", {}).get("PricedFlightOffer", [])
        for offer in offers:
            offer_prices = offer.get("OfferPrice", [])
            for offer_price in offer_prices:
                price_detail = offer_price.get("RequestedDate", {}).get("PriceDetail", {})
                total_amount_data = price_detail.get("TotalAmount", {}).get("SimpleCurrencyPrice", {})
                
                amount = total_amount_data.get("value", 0)
                currency = total_amount_data.get("Code", "INR")
                total_amount += amount
                
    except Exception as e:
        print(f"⚠️ Warning: Could not calculate total amount: {e}")
        
    return total_amount, currency


def main():
    """Main test function."""
    print("🧪 Testing KQ Flight Price Response with Card Payment")
    print("=" * 60)
    
    # Load KQ flight price response
    print("📂 Loading KQ flight price response...")
    flight_price_response = load_kq_flight_price_response()
    if not flight_price_response:
        return False
    
    print("✅ Successfully loaded KQ flight price response")
    
    # Calculate total amount
    total_amount, currency = calculate_total_amount(flight_price_response)
    print(f"💰 Total flight amount: {total_amount:,.2f} {currency}")
    
    # Create passenger data
    print("👥 Creating passenger data...")
    passengers_data = create_passenger_data_for_kq_response()
    print(f"✅ Created data for {len(passengers_data)} passengers:")
    for passenger in passengers_data:
        print(f"   - {passenger['Name']['Given'][0]} {passenger['Name']['Surname']} ({passenger['PTC']})")
    
    # Create card payment data
    print("💳 Creating card payment data...")
    payment_data = create_card_payment_data()
    print("✅ Card payment data created:")
    print(f"   - Card Type: {payment_data['Details']['CardType']}")
    print(f"   - Card Holder: {payment_data['Details']['CardHolderName']['value']}")
    print(f"   - Expiration: {payment_data['Details']['EffectiveExpireDate']['Expiration']}")
    print(f"   - 3D Secure: {'Yes' if 'SecurePaymentVersion2' in payment_data['Details'] else 'No'}")
    
    # Generate OrderCreate request
    print("\n🔄 Generating OrderCreate request...")
    try:
        order_create_request = generate_order_create_rq(
            flight_price_response=flight_price_response,
            passengers_data=passengers_data,
            payment_input_info=payment_data
        )
        
        print("✅ OrderCreate request generated successfully!")
        
        # Validate payment information in the request
        payments = order_create_request.get('Query', {}).get('Payments', {}).get('Payment', [])
        if payments:
            payment = payments[0]
            payment_amount = payment.get('Amount', {})
            card_details = payment.get('Method', {}).get('PaymentCard', {})
            
            print(f"\n💳 Payment Validation:")
            print(f"   - Payment Amount: {payment_amount.get('value', 0):,.2f} {payment_amount.get('Code', 'N/A')}")
            print(f"   - Card Type: {card_details.get('CardType', 'N/A')}")
            print(f"   - Card Holder: {card_details.get('CardHolderName', {}).get('value', 'N/A')}")
            print(f"   - Billing Address: {'Yes' if 'CardHolderBillingAddress' in card_details else 'No'}")
            print(f"   - 3D Secure: {'Yes' if 'SecurePaymentVersion2' in card_details else 'No'}")
        
        # Output to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"OrderCreate_KQ_CardPayment_{timestamp}.json"
        output_path = backend_dir / output_filename
        
        print(f"\n📄 Writing OrderCreate request to file: {output_filename}")
        with open(output_path, 'w', encoding='utf-8') as output_file:
            json.dump(order_create_request, output_file, indent=2, ensure_ascii=False)
        
        print(f"✅ OrderCreate request saved to: {output_path}")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"   - Input: FlightPriceRS_KQ.json")
        print(f"   - Passengers: {len(passengers_data)} (2 Adults, 1 Child, 1 Infant)")
        print(f"   - Payment Method: Credit Card (Visa)")
        print(f"   - Total Amount: {total_amount:,.2f} {currency}")
        print(f"   - Output File: {output_filename}")
        print(f"   - Status: ✅ SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating OrderCreate request: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 KQ Card Payment Test")
    print("Testing build_ordercreate_rq.py with real KQ flight data")
    print()
    
    success = main()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        print("📁 Check the generated JSON file for the complete OrderCreate request.")
    else:
        print("💥 Test failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)
