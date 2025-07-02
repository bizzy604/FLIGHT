#!/usr/bin/env python3
"""
Test script to verify the cache fix for booking
"""
import requests
import json

def test_cache_fix():
    """Test the cache fix for booking"""
    
    # Test flight search first
    search_data = {
        'origin': 'BOM',
        'destination': 'DXB', 
        'departure_date': '2025-07-15',
        'return_date': '2025-07-20',
        'passengers': [{'type': 'adult', 'count': 1}],
        'trip_type': 'round-trip'
    }

    print('🔍 Testing flight search...')
    search_response = requests.post('http://localhost:5000/api/verteil/air-shopping', json=search_data)
    print(f'Search status: {search_response.status_code}')

    if search_response.status_code == 200:
        search_result = search_response.json()
        if search_result.get('status') == 'success':
            offers = search_result.get('data', {}).get('offers', [])
            print(f'✅ Found {len(offers)} flight offers')
            
            if offers:
                # Test flight pricing for first offer
                pricing_data = {
                    'offer_id': 0,  # Use index 0
                    'airshopping_response': search_result['data'],
                    'passengers': [{'type': 'ADT', 'count': 1}]
                }
                
                print('💰 Testing flight pricing...')
                pricing_response = requests.post('http://localhost:5000/api/verteil/flight-price', json=pricing_data)
                print(f'Pricing status: {pricing_response.status_code}')
                
                if pricing_response.status_code == 200:
                    pricing_result = pricing_response.json()
                    print(f'✅ Flight pricing successful')
                    request_id = pricing_result.get('request_id')
                    print(f'Request ID: {request_id}')
                    
                    # Now test booking with the pricing result
                    booking_data = {
                        'passengers': [
                            {
                                'first_name': 'John', 
                                'last_name': 'Doe', 
                                'date_of_birth': '1990-01-01', 
                                'gender': 'M', 
                                'passport_number': 'A12345678', 
                                'passport_expiry': '2030-01-01', 
                                'nationality': 'US'
                            }
                        ],
                        'payment': {'method': 'CASH'},
                        'contact_info': {'email': 'test@example.com', 'phone': '+1234567890'},
                        'flight_price_response': pricing_result['data'],
                        'ShoppingResponseID': pricing_result['data'].get('ShoppingResponseID'),
                        'OfferID': 0
                    }
                    
                    print('📋 Testing booking creation...')
                    booking_response = requests.post('http://localhost:5000/api/verteil/order-create', json=booking_data)
                    print(f'Booking status: {booking_response.status_code}')
                    
                    if booking_response.status_code == 200:
                        booking_result = booking_response.json()
                        print(f'✅ Booking successful!')
                        booking_request_id = booking_result.get('request_id')
                        print(f'Booking request ID: {booking_request_id}')
                        
                        # Check if the request IDs are different
                        if request_id != booking_request_id:
                            print(f'🔍 Request ID mismatch detected:')
                            print(f'  Pricing request ID: {request_id}')
                            print(f'  Booking request ID: {booking_request_id}')
                            print(f'✅ Cache fix should handle this mismatch!')
                        else:
                            print(f'✅ Request IDs match: {request_id}')
                            
                    else:
                        print(f'❌ Booking failed: {booking_response.text[:500]}')
                else:
                    print(f'❌ Pricing failed: {pricing_response.text[:500]}')
            else:
                print('❌ No offers found in search result')
        else:
            print(f'❌ Search not successful: {search_result}')
    else:
        print(f'❌ Search failed: {search_response.text[:500]}')

if __name__ == "__main__":
    test_cache_fix()
