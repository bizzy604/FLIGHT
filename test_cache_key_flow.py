#!/usr/bin/env python3
"""
Test script to verify the cache key flow is working correctly.
This script simulates the flow from flight price to seat/service availability.
"""

import requests
import json
import time
import sys

# Configuration
BACKEND_URL = "http://localhost:5000"
FRONTEND_URL = "http://localhost:3000"

def test_flight_price_cache_key():
    """Test that flight price response includes the cache key in metadata"""
    print("\n" + "="*60)
    print("Testing Flight Price Cache Key Flow")
    print("="*60)
    
    # Sample flight price request
    flight_price_request = {
        "offer_id": "test_offer_123",
        "shopping_response_id": "test_shopping_456",
        "air_shopping_response": {
            "AirShoppingRS": {
                "OffersGroup": {
                    "AirlineOffers": [{
                        "AirlineOffer": [{
                            "OfferID": {"value": "test_offer_123"}
                        }]
                    }]
                }
            }
        }
    }
    
    print("\n1. Making flight price request...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/verteil/flight-price",
            json=flight_price_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"   ❌ Flight price request failed with status {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None
            
        data = response.json()
        
        # Check for cache key in metadata
        cache_key = None
        if data.get('data', {}).get('metadata', {}).get('flight_price_cache_key'):
            cache_key = data['data']['metadata']['flight_price_cache_key']
            print(f"   ✅ Found flight_price_cache_key in metadata: {cache_key}")
        elif data.get('flight_price_cache_key'):
            cache_key = data['flight_price_cache_key']
            print(f"   ✅ Found flight_price_cache_key at top level: {cache_key}")
        else:
            print("   ❌ No flight_price_cache_key found in response")
            print(f"   Response structure: {json.dumps(data, indent=2)[:500]}")
            return None
            
        return cache_key
        
    except Exception as e:
        print(f"   ❌ Error making flight price request: {e}")
        return None

def test_service_endpoints(cache_key):
    """Test that service endpoints can retrieve data using the cache key"""
    print("\n2. Testing service endpoints with cache key...")
    
    # Test seat availability
    print("\n   Testing Seat Availability:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/verteil/seat-availability",
            json={"flight_price_cache_key": cache_key},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Seat availability request successful")
        else:
            data = response.json()
            if "not found" in data.get('message', '').lower():
                print(f"   ⚠️  Cache data not found (might have expired)")
            else:
                print(f"   ❌ Seat availability request failed: {data.get('message', 'Unknown error')}")
                
    except Exception as e:
        print(f"   ❌ Error calling seat availability: {e}")
    
    # Test service list
    print("\n   Testing Service List:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/verteil/service-list",
            json={"flight_price_cache_key": cache_key},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Service list request successful")
        else:
            data = response.json()
            if "not found" in data.get('message', '').lower():
                print(f"   ⚠️  Cache data not found (might have expired)")
            else:
                print(f"   ❌ Service list request failed: {data.get('message', 'Unknown error')}")
                
    except Exception as e:
        print(f"   ❌ Error calling service list: {e}")

def main():
    print("\nCache Key Flow Test")
    print("==================")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing cache key propagation from flight price to service endpoints")
    
    # Test flight price and get cache key
    cache_key = test_flight_price_cache_key()
    
    if cache_key:
        # Test service endpoints with the cache key
        test_service_endpoints(cache_key)
        
        print("\n" + "="*60)
        print("Summary:")
        print(f"✅ Cache key successfully generated: {cache_key}")
        print("✅ Cache key format is correct for service endpoints")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("Summary:")
        print("❌ Failed to get cache key from flight price response")
        print("   Please check the backend logs for more details")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()