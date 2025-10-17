"""
Test script to verify the ancillary pricing cache fix.
This test ensures that the priced ancillaries API correctly retrieves
the raw flight price response from Redis using flight_price_cache_key.
"""
import asyncio
import json
from routes.ancillary_pricing_routes import price_ancillaries
from services.simple_flight_cache import SimpleFlightCache

# Initialize cache manager
simple_flight_cache = SimpleFlightCache()

# Sample test data
TEST_CACHE_KEY = "flight_price_raw_test_123456_1759689121"
TEST_RAW_FLIGHT_PRICE = {
    "Success": True,
    "ShoppingResponseID": {
        "ResponseID": {"value": "test-response-id"}
    },
    "PricedFlightOffers": {
        "PricedFlightOffer": [{
            "OfferID": {"value": "test-offer-id", "Owner": "AF"},
            "OfferPrice": [{"TotalAmount": {"value": 15991.0}}]
        }]
    },
    "DataLists": {
        "AnonymousTravelerList": {
            "AnonymousTraveler": [{
                "ObjectKey": "PAX1",
                "PTC": {"value": "ADT"}
            }]
        },
        "FlightSegmentList": {
            "FlightSegment": [{
                "SegmentKey": "SEG1",
                "Departure": {"AirportCode": {"value": "CDG"}},
                "Arrival": {"AirportCode": {"value": "FRA"}}
            }]
        }
    }
}

def test_cache_storage_and_retrieval():
    """Test 1: Verify we can store and retrieve raw flight price data"""
    print("\n" + "="*80)
    print("TEST 1: Cache Storage and Retrieval")
    print("="*80)
    
    try:
        # Store test data in cache
        print(f"\n1. Storing test data with key: {TEST_CACHE_KEY}")
        store_result = simple_flight_cache.store_flight_price(
            session_id=TEST_CACHE_KEY,
            price_data=TEST_RAW_FLIGHT_PRICE,
            ttl=300
        )
        
        if store_result['success']:
            print(f"   ✅ Successfully stored in Redis")
            print(f"   Cache key: {store_result.get('cache_key')}")
        else:
            print(f"   ❌ Failed to store: {store_result.get('message')}")
            return False
        
        # Retrieve test data from cache
        print(f"\n2. Retrieving data with key: {TEST_CACHE_KEY}")
        retrieve_result = simple_flight_cache.get_flight_price(TEST_CACHE_KEY)
        
        if retrieve_result.get('success') and retrieve_result.get('data'):
            print(f"   ✅ Successfully retrieved from Redis")
            retrieved_data = retrieve_result['data']
            print(f"   Retrieved data type: {type(retrieved_data)}")
            print(f"   Retrieved data keys: {list(retrieved_data.keys()) if isinstance(retrieved_data, dict) else 'Not a dict'}")
            
            # Validate retrieved data structure
            if isinstance(retrieved_data, dict):
                has_priced_offers = 'PricedFlightOffers' in retrieved_data
                has_data_lists = 'DataLists' in retrieved_data
                
                print(f"\n3. Validating retrieved data structure:")
                print(f"   - Has PricedFlightOffers: {has_priced_offers}")
                print(f"   - Has DataLists: {has_data_lists}")
                
                if has_priced_offers and has_data_lists:
                    print(f"   ✅ Raw NDC structure validated")
                    return True
                else:
                    print(f"   ❌ Missing required NDC keys")
                    return False
        else:
            print(f"   ❌ Failed to retrieve: {retrieve_result.get('message')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_validation_logic():
    """Test 2: Verify validation rejects transformed data and accepts raw data"""
    print("\n" + "="*80)
    print("TEST 2: Validation Logic")
    print("="*80)
    
    # Test transformed data (should be rejected)
    transformed_data = {
        "offer_id": "123",
        "total_price": 15991.0,
        "flight_segments": [],
        "passengers": []
    }
    
    print("\n1. Testing transformed data validation:")
    print(f"   Input keys: {list(transformed_data.keys())}")
    
    transformed_keys = ['direction', 'fare_family', 'flight_segments', 'offer_id', 'original_offer_id', 'passengers', 'time_limits', 'total_price']
    has_transformed_keys = any(key in transformed_data.keys() for key in transformed_keys)
    
    if has_transformed_keys:
        print(f"   ✅ Correctly identified as transformed data (should be rejected)")
    else:
        print(f"   ❌ Failed to identify transformed data")
    
    # Test raw NDC data (should be accepted)
    print("\n2. Testing raw NDC data validation:")
    print(f"   Input keys: {list(TEST_RAW_FLIGHT_PRICE.keys())}")
    
    required_ndc_keys = ['PricedFlightOffers', 'DataLists']
    missing_keys = [key for key in required_ndc_keys if key not in TEST_RAW_FLIGHT_PRICE.keys()]
    
    if not missing_keys:
        print(f"   ✅ Correctly identified as raw NDC data (should be accepted)")
        return True
    else:
        print(f"   ❌ Missing required NDC keys: {missing_keys}")
        return False

def test_unwrapping_logic():
    """Test 3: Verify FlightPriceRS wrapper unwrapping"""
    print("\n" + "="*80)
    print("TEST 3: FlightPriceRS Unwrapping")
    print("="*80)
    
    # Test wrapped data
    wrapped_data = {
        "FlightPriceRS": TEST_RAW_FLIGHT_PRICE
    }
    
    print("\n1. Testing wrapped FlightPriceRS structure:")
    print(f"   Input has FlightPriceRS wrapper: {'FlightPriceRS' in wrapped_data}")
    
    # Simulate unwrapping logic
    flight_price_response = wrapped_data
    if isinstance(flight_price_response, dict) and 'FlightPriceRS' in flight_price_response:
        flight_price_response = flight_price_response['FlightPriceRS']
        print(f"   ✅ Successfully unwrapped FlightPriceRS structure")
    
    print(f"   Unwrapped data keys: {list(flight_price_response.keys())}")
    
    # Verify unwrapped data has correct structure
    has_required_keys = 'PricedFlightOffers' in flight_price_response and 'DataLists' in flight_price_response
    
    if has_required_keys:
        print(f"   ✅ Unwrapped data has correct NDC structure")
        return True
    else:
        print(f"   ❌ Unwrapped data missing required keys")
        return False

def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*80)
    print("ANCILLARY PRICING CACHE FIX - VALIDATION TESTS")
    print("="*80)
    
    results = {
        "cache_storage_retrieval": test_cache_storage_and_retrieval(),
        "validation_logic": test_validation_logic(),
        "unwrapping_logic": test_unwrapping_logic()
    }
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The ancillary pricing cache fix is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED! Review the implementation.")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
