#!/usr/bin/env python3
"""
Test script to verify the cache retrieval logic in booking.py
"""
import json
from utils.cache_manager import cache_manager

def test_cache_retrieval_logic():
    """Test the cache retrieval logic that was added to booking.py"""
    
    # Sample frontend flight_price_response (transformed data)
    frontend_flight_price_response = {
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
    }
    
    # Sample raw flight price response (proper NDC structure)
    raw_flight_price_response = {
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
    
    request_id = 'abbb6b38-02dc-494b-af2d-43b071663337'
    
    print("🧪 Testing cache retrieval logic...")
    
    # Test 1: No cache - should use frontend data
    print("\n📋 Test 1: No cache available")
    flight_price_response = frontend_flight_price_response.copy()
    
    # Simulate the cache retrieval logic from booking.py
    raw_flight_price_response_from_cache = None
    try:
        flight_price_cache_key = f"flight_price_response:{request_id}"
        raw_flight_price_response_from_cache = cache_manager.get(flight_price_cache_key)
        
        if raw_flight_price_response_from_cache:
            print(f"✅ Retrieved raw flight price response from cache")
            print(f"Raw flight price response keys: {list(raw_flight_price_response_from_cache.keys())}")
            
            # Check if the raw response has PricedFlightOffers with OfferPrice entries
            if isinstance(raw_flight_price_response_from_cache, dict) and 'PricedFlightOffers' in raw_flight_price_response_from_cache:
                priced_offers = raw_flight_price_response_from_cache['PricedFlightOffers']
                if isinstance(priced_offers, dict) and 'PricedFlightOffer' in priced_offers:
                    priced_offer_list = priced_offers['PricedFlightOffer']
                    if isinstance(priced_offer_list, list) and len(priced_offer_list) > 0:
                        first_offer = priced_offer_list[0]
                        if 'OfferPrice' in first_offer:
                            print(f"✅ Raw response has proper PricedFlightOffers with OfferPrice entries - using raw response")
                            flight_price_response = raw_flight_price_response_from_cache
                        else:
                            print(f"❌ Raw response PricedFlightOffers missing OfferPrice entries - will enhance frontend data")
                    else:
                        print(f"❌ Raw response PricedFlightOffers has no PricedFlightOffer list - will enhance frontend data")
                else:
                    print(f"❌ Raw response PricedFlightOffers missing PricedFlightOffer key - will enhance frontend data")
            else:
                print(f"❌ Raw response missing PricedFlightOffers - will enhance frontend data")
        else:
            print(f"❌ No raw flight price response found in cache for key: {flight_price_cache_key}")
            print(f"Will enhance the frontend flight_price_response")
            
    except Exception as cache_error:
        print(f"❌ Error retrieving raw flight price response from cache: {str(cache_error)}")
        print(f"Will enhance the frontend flight_price_response")
    
    # Check final result
    if 'PricedFlightOffers' in flight_price_response:
        print(f"✅ Final flight_price_response has PricedFlightOffers")
    else:
        print(f"❌ Final flight_price_response missing PricedFlightOffers")
    
    # Test 2: Cache available - should use cached data
    print("\n📋 Test 2: Cache available with proper NDC structure")
    
    # Store the raw response in cache
    flight_price_cache_key = f"flight_price_response:{request_id}"
    cache_manager.set(flight_price_cache_key, raw_flight_price_response, ttl=1800)
    print(f"✅ Stored raw flight price response in cache")
    
    # Reset to frontend data
    flight_price_response = frontend_flight_price_response.copy()
    
    # Simulate the cache retrieval logic again
    raw_flight_price_response_from_cache = None
    try:
        raw_flight_price_response_from_cache = cache_manager.get(flight_price_cache_key)
        
        if raw_flight_price_response_from_cache:
            print(f"✅ Retrieved raw flight price response from cache")
            print(f"Raw flight price response keys: {list(raw_flight_price_response_from_cache.keys())}")
            
            # Check if the raw response has PricedFlightOffers with OfferPrice entries
            if isinstance(raw_flight_price_response_from_cache, dict) and 'PricedFlightOffers' in raw_flight_price_response_from_cache:
                priced_offers = raw_flight_price_response_from_cache['PricedFlightOffers']
                if isinstance(priced_offers, dict) and 'PricedFlightOffer' in priced_offers:
                    priced_offer_list = priced_offers['PricedFlightOffer']
                    if isinstance(priced_offer_list, list) and len(priced_offer_list) > 0:
                        first_offer = priced_offer_list[0]
                        if 'OfferPrice' in first_offer:
                            print(f"✅ Raw response has proper PricedFlightOffers with OfferPrice entries - using raw response")
                            flight_price_response = raw_flight_price_response_from_cache
                        else:
                            print(f"❌ Raw response PricedFlightOffers missing OfferPrice entries - will enhance frontend data")
                    else:
                        print(f"❌ Raw response PricedFlightOffers has no PricedFlightOffer list - will enhance frontend data")
                else:
                    print(f"❌ Raw response PricedFlightOffers missing PricedFlightOffer key - will enhance frontend data")
            else:
                print(f"❌ Raw response missing PricedFlightOffers - will enhance frontend data")
        else:
            print(f"❌ No raw flight price response found in cache")
            
    except Exception as cache_error:
        print(f"❌ Error retrieving raw flight price response from cache: {str(cache_error)}")
    
    # Check final result
    if 'PricedFlightOffers' in flight_price_response:
        priced_offers = flight_price_response['PricedFlightOffers']
        if 'PricedFlightOffer' in priced_offers and len(priced_offers['PricedFlightOffer']) > 0:
            first_offer = priced_offers['PricedFlightOffer'][0]
            if 'OfferPrice' in first_offer:
                print(f"✅ SUCCESS: Final flight_price_response has proper PricedFlightOffers with OfferPrice entries!")
                print(f"OfferPrice count: {len(first_offer['OfferPrice'])}")
            else:
                print(f"❌ Final flight_price_response PricedFlightOffers missing OfferPrice entries")
        else:
            print(f"❌ Final flight_price_response PricedFlightOffers has no PricedFlightOffer list")
    else:
        print(f"❌ Final flight_price_response missing PricedFlightOffers")
    
    print(f"\n🎯 Cache retrieval logic test completed!")

if __name__ == "__main__":
    test_cache_retrieval_logic()
