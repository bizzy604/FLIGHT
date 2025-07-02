#!/usr/bin/env python3
"""
Test script to simulate EXACTLY what the booking service is doing
including the exact passenger and payment transformations.
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

def simulate_exact_booking_service_transformations(raw_response):
    """Simulate the EXACT transformations that the booking service does."""
    
    # This simulates what the booking service does to create enhanced_flight_price_response
    enhanced_flight_price_response = raw_response.copy()
    
    # Simulate the EXACT passenger transformation from booking service
    # This is what the frontend would send
    frontend_passengers = [
        {
            "type": "adult",
            "title": "mr",
            "firstName": "John",
            "lastName": "Doe", 
            "dob": {"year": "1990", "month": "01", "day": "01"},
            "gender": "male",
            "documentNumber": "P123456789",
            "expiryDate": {"year": "2030", "month": "01", "day": "01"},
            "documentType": "passport",
            "issuingCountry": "US"
        }
    ]
    
    # Frontend contact info
    contact_info = {
        "phone": "1234567890",
        "phoneCountryCode": "+1",
        "email": "john.doe@example.com"
    }
    
    # Frontend payment info
    payment_info = {
        "payment_method": "CASH"
    }
    
    # EXACT transformation logic from booking service
    transformed_passengers = []
    for passenger in frontend_passengers:
        # Map frontend passenger type to expected format
        pax_type = passenger.get('type', 'adult')
        ptc_mapping = {
            'adult': 'ADT',
            'child': 'CHD', 
            'infant': 'INF'
        }
        ptc = ptc_mapping.get(pax_type, 'ADT')
        
        # Format birth date from frontend dob object
        dob = passenger.get('dob', {})
        birth_date = None
        if dob and dob.get('year') and dob.get('month') and dob.get('day'):
            birth_date = f"{dob['year']}-{dob['month'].zfill(2)}-{dob['day'].zfill(2)}"
        
        # Map title from frontend
        title_mapping = {
            'mr': 'Mr',
            'ms': 'Ms', 
            'mrs': 'Mrs',
            'miss': 'Miss',
            'dr': 'Dr'
        }
        title = title_mapping.get(passenger.get('title', '').lower(), 
                                "Mr" if passenger.get('gender', '').lower() == 'male' else "Ms")
        
        # Transform to the structure expected by build_ordercreate_rq
        transformed_passenger = {
            'PTC': ptc,  # Direct value, not nested
            'Name': {
                'Title': title,
                'Given': [passenger.get('firstName', '')],  # List format expected
                'Surname': passenger.get('lastName', '')
            },
            'Gender': passenger.get('gender', '').capitalize(),
            'BirthDate': birth_date
        }
        
        # Add document information if available
        if passenger.get('documentNumber'):
            # Format expiry date from frontend expiryDate object
            expiry = passenger.get('expiryDate', {})
            expiry_date = None
            if expiry and expiry.get('year') and expiry.get('month') and expiry.get('day'):
                expiry_date = f"{expiry['year']}-{expiry['month'].zfill(2)}-{expiry['day'].zfill(2)}"
            
            # Map document type
            doc_type_mapping = {
                'passport': 'PT',
                'national_id': 'NI',
                'id': 'ID'
            }
            doc_type = doc_type_mapping.get(passenger.get('documentType', 'passport').lower(), 'PT')
            
            transformed_passenger['Documents'] = [{
                'Type': doc_type,
                'ID': passenger.get('documentNumber'),
                'DateOfExpiration': expiry_date,
                'CountryOfIssuance': passenger.get('issuingCountry', '')
            }]
        
        # Add ObjectKey
        transformed_passenger['ObjectKey'] = f"PAX{len(transformed_passengers) + 1}"
        
        transformed_passengers.append(transformed_passenger)
    
    # EXACT payment transformation from booking service
    payment_method = payment_info.get('payment_method', 'CASH')
    method_type_mapping = {
        'CASH': 'CASH',
        'CREDIT_CARD': 'CC',
        'DEBIT_CARD': 'CC',
        'BANK_TRANSFER': 'EASYPAY',
        'OTHER': 'OTHER'
    }
    
    mapped_method_type = method_type_mapping.get(payment_method, 'CASH')
    
    transformed_payment = {
        'MethodType': mapped_method_type,
        'currency': payment_info.get('currency', 'USD'),
        'Details': {}
    }
    
    if mapped_method_type == 'CASH':
        transformed_payment['Details']['CashInd'] = payment_info.get('CashInd', True)
    
    return enhanced_flight_price_response, transformed_passengers, transformed_payment

def main():
    print("=== EXACT Booking Service Simulation ===")
    
    try:
        print("Loading actual raw flight price response from logs...")
        raw_response = load_actual_raw_response()
        
        print("Simulating EXACT booking service data transformations...")
        enhanced_flight_price_response, transformed_passengers, transformed_payment = simulate_exact_booking_service_transformations(raw_response)
        
        print(f"Enhanced flight price response keys: {list(enhanced_flight_price_response.keys())}")
        print(f"Transformed passengers count: {len(transformed_passengers)}")
        print(f"First passenger structure: {json.dumps(transformed_passengers[0], indent=2)}")
        print(f"Transformed payment structure: {json.dumps(transformed_payment, indent=2)}")
        
        print("\n=== CALLING generate_order_create_rq (EXACT BOOKING SERVICE CALL) ===")
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
        with open('exact_booking_service_payload.json', 'w') as f:
            json.dump(payload, f, indent=2, default=str)
        
        print("📁 Saved generated payload to 'exact_booking_service_payload.json'")
        
    except Exception as e:
        print(f"❌ Error occurred (THIS IS WHY FALLBACK IS USED): {e}")
        import traceback
        traceback.print_exc()
        print("\n🔍 This exception is why the booking service falls back to manual construction!")

if __name__ == "__main__":
    main()
