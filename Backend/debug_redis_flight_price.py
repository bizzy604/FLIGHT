"""
Debug script to check what's actually stored in Redis for flight price responses.
This will help us understand why ShoppingResponseID is missing.
"""

import sys
import json
from services.simple_flight_cache import SimpleFlightCache

# Initialize cache
cache = SimpleFlightCache()

def debug_cache_key(cache_key):
    """Debug a specific cache key."""
    print(f"\n{'='*80}")
    print(f"Debugging Cache Key: {cache_key}")
    print(f"{'='*80}\n")
    
    # Try to retrieve the data
    result = cache.get_flight_price(cache_key)
    
    print(f"Retrieval Success: {result.get('success')}")
    print(f"Retrieval Message: {result.get('message')}")
    
    if result.get('success') and result.get('data'):
        data = result['data']
        print(f"\nData Type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"\nTop-Level Keys ({len(data)} total):")
            for key in data.keys():
                print(f"  - {key}")
            
            # Check for ShoppingResponseID
            if 'ShoppingResponseID' in data:
                shopping_id = data['ShoppingResponseID']
                print(f"\n✅ ShoppingResponseID Found:")
                print(f"   Structure: {json.dumps(shopping_id, indent=2)}")
                if isinstance(shopping_id, dict) and 'ResponseID' in shopping_id:
                    response_id_value = shopping_id['ResponseID'].get('value')
                    print(f"   ✅ ResponseID.value = {response_id_value}")
            else:
                print(f"\n❌ ShoppingResponseID NOT FOUND!")
                
            # Check for FlightPriceRS wrapper
            if 'FlightPriceRS' in data:
                print(f"\n🔍 FlightPriceRS Wrapper Found - checking inside...")
                flight_price_rs = data['FlightPriceRS']
                if isinstance(flight_price_rs, dict):
                    print(f"   FlightPriceRS Keys: {list(flight_price_rs.keys())}")
                    if 'ShoppingResponseID' in flight_price_rs:
                        shopping_id = flight_price_rs['ShoppingResponseID']
                        print(f"   ✅ ShoppingResponseID inside FlightPriceRS:")
                        print(f"      Structure: {json.dumps(shopping_id, indent=2)}")
            
            # Check for PricedFlightOffers
            if 'PricedFlightOffers' in data:
                print(f"\n✅ PricedFlightOffers Found")
                offers = data['PricedFlightOffers']
                if isinstance(offers, dict) and 'PricedFlightOffer' in offers:
                    offer_list = offers['PricedFlightOffer']
                    print(f"   Number of offers: {len(offer_list) if isinstance(offer_list, list) else 1}")
            else:
                print(f"\n❌ PricedFlightOffers NOT FOUND!")
                
            # Check for DataLists
            if 'DataLists' in data:
                print(f"\n✅ DataLists Found")
            else:
                print(f"\n❌ DataLists NOT FOUND!")
                
        else:
            print(f"\n❌ Data is not a dictionary!")
            print(f"   Data: {str(data)[:200]}")
    else:
        print(f"\n❌ Failed to retrieve data from cache")
        print(f"   Error: {result.get('error')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Debug specific cache key from command line
        cache_key = sys.argv[1]
        debug_cache_key(cache_key)
    else:
        print("Usage: python debug_redis_flight_price.py <cache_key>")
        print("\nExample:")
        print("  python debug_redis_flight_price.py flight_price_raw_abc123_1759692173")
        print("\nYou can find cache keys in the logs, they look like:")
        print("  flight_price_raw_<request_id>_<timestamp>")
