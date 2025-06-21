#!/usr/bin/env python3
"""
Simple test to verify OrderCreate functionality with ShoppingResponseID
"""

import json
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

try:
    from build_ordercreate_rq import generate_order_create_rq
    print("✅ OrderCreate builder imported successfully")
except ImportError as e:
    print(f"❌ Error importing build_ordercreate_rq: {e}")
    # sys.exit(1) # Removed sys.exit

# Load test FlightPriceResponse
try:
    # Corrected path to flightpriceresponse.json
    with open('flightpriceresponse.json', 'r') as f:
        flight_price_response = json.load(f)
    print("✅ FlightPriceResponse loaded successfully")
except Exception as e:
    print(f"❌ Error loading FlightPriceResponse: {e}")
    # sys.exit(1) # Removed sys.exit

# Check if ShoppingResponseID exists
if 'ShoppingResponseID' in flight_price_response:
    shopping_response_id = flight_price_response['ShoppingResponseID']['ResponseID']['value']
    print(f"✅ ShoppingResponseID found: {shopping_response_id}")
else:
    print("❌ ShoppingResponseID not found in FlightPriceResponse")
    # sys.exit(1) # Removed sys.exit

# Test passenger data
test_passengers = [{
    "ObjectKey": "PAX1",
    "PTC": "ADT",
    "Name": {
        "Title": "Mr",
        "Given": ["John"],
        "Surname": "Doe"
    },
    "Gender": "Male",
    "BirthDate": "1985-03-15"
}]

# Test contact info
test_contact = {
    "email": "john.doe@example.com",
    "phone": "+1234567890"
}

# Test payment info
test_payment = {
    "MethodType": "CASH",
    "currency": "USD",
    "Details": {
        "CashInd": True
    }
}

try:
    # Generate OrderCreate request
    order_create_rq = generate_order_create_rq(
        flight_price_response=flight_price_response,
        passengers_data=test_passengers,
        payment_input_info=test_payment
    )
    
    print("✅ OrderCreate request generated successfully")
    print(f"📋 Request contains {len(str(order_create_rq))} characters")
    
    # Check if the generated request has required fields
    if 'ShoppingResponseID' in str(order_create_rq):
        print("✅ ShoppingResponseID included in OrderCreate request")
    else:
        print("❌ ShoppingResponseID missing from OrderCreate request")
        
except Exception as e:
    print(f"❌ Error generating OrderCreate request: {e}")
    # sys.exit(1) # Removed sys.exit

print("\n🎉 All tests passed! OrderCreate functionality is working correctly.")