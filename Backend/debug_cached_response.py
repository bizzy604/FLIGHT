#!/usr/bin/env python3
"""
Debug script to examine the actual cached flight price response structure.
"""

import json
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from utils.cache_manager import cache_manager

def debug_cached_response():
    """Debug the cached flight price response structure."""
    
    # Try to find cached responses
    print("🔍 Looking for cached flight price responses...")
    
    # Common cache key patterns
    cache_keys_to_try = [
        "flight_price_response:4hi0aoiHMPXWTAmxgDFrzKh-G-sdXT3Q-9MmLfVhVSQ-QR",
        "flight_price_response:1H0QRZ_HG9OC1FYFHN89TO7Z9QBJE2WMRLU",
        "flight_price_response:d016c19e-9472-41a9-b8aa-3f57e038c309"
    ]
    
    for cache_key in cache_keys_to_try:
        print(f"\n🔑 Trying cache key: {cache_key}")
        cached_response = cache_manager.get(cache_key)
        
        if cached_response:
            print(f"✅ Found cached response!")
            print(f"📊 Response type: {type(cached_response)}")
            
            if isinstance(cached_response, dict):
                print(f"📋 Top-level keys: {list(cached_response.keys())}")
                
                # Check PricedFlightOffers structure
                if 'PricedFlightOffers' in cached_response:
                    priced_offers = cached_response['PricedFlightOffers']
                    print(f"🎯 PricedFlightOffers type: {type(priced_offers)}")
                    
                    if isinstance(priced_offers, dict) and 'PricedFlightOffer' in priced_offers:
                        offer_list = priced_offers['PricedFlightOffer']
                        print(f"📦 PricedFlightOffer list length: {len(offer_list) if isinstance(offer_list, list) else 'Not a list'}")
                        
                        if isinstance(offer_list, list) and len(offer_list) > 0:
                            first_offer = offer_list[0]
                            print(f"🎪 First offer keys: {list(first_offer.keys())}")
                            
                            # Check OfferPrice structure
                            if 'OfferPrice' in first_offer:
                                offer_price = first_offer['OfferPrice']
                                print(f"💰 OfferPrice type: {type(offer_price)}")
                                print(f"💰 OfferPrice length: {len(offer_price) if isinstance(offer_price, list) else 'Not a list'}")
                                
                                if isinstance(offer_price, list) and len(offer_price) > 0:
                                    first_price = offer_price[0]
                                    print(f"💵 First OfferPrice keys: {list(first_price.keys())}")
                                    
                                    # Check for OfferItemID
                                    if 'OfferItemID' in first_price:
                                        print(f"🎫 OfferItemID found: {first_price['OfferItemID']}")
                                    else:
                                        print(f"❌ OfferItemID NOT found in first OfferPrice")
                                        print(f"🔍 First OfferPrice structure: {json.dumps(first_price, indent=2)[:500]}...")
                                else:
                                    print(f"❌ OfferPrice is not a list or is empty: {offer_price}")
                            else:
                                print(f"❌ OfferPrice NOT found in first offer")
                                print(f"🔍 First offer structure: {json.dumps(first_offer, indent=2)[:500]}...")
                        else:
                            print(f"❌ PricedFlightOffer is not a list or is empty")
                    else:
                        print(f"❌ PricedFlightOffer not found in PricedFlightOffers")
                        print(f"🔍 PricedFlightOffers structure: {json.dumps(priced_offers, indent=2)[:300]}...")
                else:
                    print(f"❌ PricedFlightOffers not found in cached response")
                    
                # Save the response for detailed analysis
                with open(f'debug_cached_response_{cache_key.split(":")[-1]}.json', 'w') as f:
                    json.dump(cached_response, f, indent=2)
                print(f"💾 Saved cached response to debug_cached_response_{cache_key.split(':')[-1]}.json")
                
            else:
                print(f"❌ Cached response is not a dictionary: {cached_response}")
                
            return  # Found one, stop looking
        else:
            print(f"❌ No cached response found")
    
    print(f"\n🚫 No cached responses found with any of the tried keys")

if __name__ == "__main__":
    debug_cached_response()
