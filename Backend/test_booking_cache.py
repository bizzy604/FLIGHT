#!/usr/bin/env python3
"""
Test script to verify the booking cache retrieval functionality
"""
import asyncio
import json
from services.flight.booking import FlightBookingService
from utils.cache_manager import cache_manager

async def test_booking_cache():
    """Test the booking cache retrieval functionality"""
    
    # Sample request data that would come from frontend
    sample_request_data = {
        'flight_offer': {
            'offer_id': '1H1QRZ_RS5SQAOSQ6YSHTJID680BNTIDEZ4',
            'shopping_response_id': 'abbb6b38-02dc-494b-af2d-43b071663337',
            'DataLists': {
                'AnonymousTravelerList': [
                    {'PTC': 'ADT', 'ObjectKey': 'PAX1'}
                ]
            },
            'OffersGroup': {
                'AirlineOffers': [
                    {
                        'AirlineOffer': [
                            {
                                'PricedOffer': {
                                    'OfferPrice': [
                                        {
                                            'OfferItemID': '1H1QRZ_RS5SQAOSQ6YSHTJID680BNTIDEZ4-1',
                                            'BaseAmount': {'value': 100.00, 'Code': 'USD'},
                                            'TotalAmount': {'value': 150.00, 'Code': 'USD'}
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        },
        'passengers': [
            {
                'type': 'adult',
                'title': 'Mr',
                'first_name': 'John',
                'last_name': 'Doe',
                'date_of_birth': '1990-01-01',
                'gender': 'M',
                'nationality': 'US',
                'passport_number': 'A12345678',
                'passport_expiry': '2030-01-01',
                'passport_country': 'US'
            }
        ],
        'payment': {
            'method': 'CASH'
        },
        'contact': {
            'email': 'test@example.com',
            'phone': '+1234567890'
        }
    }
    
    # Create a sample raw flight price response that would be in cache
    sample_raw_flight_price_response = {
        'ShoppingResponseID': {
            'ResponseID': {'value': 'abbb6b38-02dc-494b-af2d-43b071663337'}
        },
        'PricedFlightOffers': {
            'PricedFlightOffer': [
                {
                    'OfferID': {
                        'value': '1H1QRZ_RS5SQAOSQ6YSHTJID680BNTIDEZ4',
                        'Owner': 'QR',
                        'Channel': 'NDC'
                    },
                    'OfferPrice': [
                        {
                            'OfferItemID': '1H1QRZ_RS5SQAOSQ6YSHTJID680BNTIDEZ4-1',
                            'BaseAmount': {'value': 100.00, 'Code': 'USD'},
                            'TotalAmount': {'value': 150.00, 'Code': 'USD'},
                            'Taxes': {'Total': {'value': 50.00, 'Code': 'USD'}}
                        }
                    ]
                }
            ]
        },
        'DataLists': {
            'AnonymousTravelerList': [
                {'PTC': 'ADT', 'ObjectKey': 'PAX1'}
            ]
        }
    }
    
    # Store the raw response in cache
    request_id = 'abbb6b38-02dc-494b-af2d-43b071663337'
    flight_price_cache_key = f"flight_price_response:{request_id}"
    cache_manager.set(flight_price_cache_key, sample_raw_flight_price_response, ttl=1800)
    print(f"✅ Stored raw flight price response in cache with key: {flight_price_cache_key}")
    
    # Verify cache storage
    cached_response = cache_manager.get(flight_price_cache_key)
    if cached_response:
        print(f"✅ Cache verification successful - retrieved response with keys: {list(cached_response.keys())}")
        if 'PricedFlightOffers' in cached_response:
            priced_offers = cached_response['PricedFlightOffers']
            if 'PricedFlightOffer' in priced_offers and len(priced_offers['PricedFlightOffer']) > 0:
                first_offer = priced_offers['PricedFlightOffer'][0]
                if 'OfferPrice' in first_offer:
                    print(f"✅ Cache contains proper PricedFlightOffers with OfferPrice entries")
                else:
                    print(f"❌ Cache missing OfferPrice entries")
            else:
                print(f"❌ Cache missing PricedFlightOffer list")
        else:
            print(f"❌ Cache missing PricedFlightOffers")
    else:
        print(f"❌ Cache verification failed - no response found")
        return
    
    # Test the booking service
    try:
        service = FlightBookingService()
        
        print(f"\n🚀 Testing booking creation with cache retrieval...")
        result = await service.create_booking(
            flight_price_response=sample_request_data['flight_offer'],
            passengers=sample_request_data['passengers'],
            payment_info=sample_request_data['payment'],
            contact_info=sample_request_data['contact'],
            request_id=request_id
        )
        
        print(f"✅ Booking creation completed")
        print(f"Result status: {result.get('status', 'unknown')}")
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success: {result.get('message', 'No message')}")
            
    except Exception as e:
        print(f"❌ Exception during booking creation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing booking cache retrieval functionality...")
    asyncio.run(test_booking_cache())
