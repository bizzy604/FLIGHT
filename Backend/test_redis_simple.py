#!/usr/bin/env python3
"""
Simple Redis Cloud connection test
"""
import sys
import os
import logging
from datetime import datetime

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from config.redis_config import test_redis_connection, get_redis_connection
from services.redis_flight_storage import RedisFlightStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Redis connection"""
    print("=" * 50)
    print("TESTING REDIS CLOUD CONNECTION")
    print("=" * 50)
    
    result = test_redis_connection()
    
    if result["success"]:
        print("SUCCESS: Redis connection working!")
        print(f"URL: {result['url']}")
        print(f"Message: {result['message']}")
        return True
    else:
        print("FAILED: Redis connection failed!")
        print(f"Error: {result['message']}")
        return False

def test_storage():
    """Test Redis Flight Storage"""
    print("\n" + "=" * 50)
    print("TESTING REDIS FLIGHT STORAGE")
    print("=" * 50)
    
    try:
        storage = RedisFlightStorage()
        
        if not storage.redis_available:
            print("FAILED: Redis Flight Storage not available")
            return False
            
        print("SUCCESS: RedisFlightStorage initialized")
        
        # Test data storage and retrieval
        sample_data = {
            "origin": "LAX",
            "destination": "JFK", 
            "departure_date": "2024-12-15",
            "passengers": 2,
            "test_timestamp": datetime.utcnow().isoformat()
        }
        
        print("Testing data storage...")
        store_result = storage.store_flight_search(sample_data)
        
        if store_result["success"]:
            session_id = store_result["session_id"]
            print(f"SUCCESS: Data stored with session ID: {session_id}")
            
            print("Testing data retrieval...")
            retrieve_result = storage.get_flight_search(session_id)
            
            if retrieve_result["success"]:
                print("SUCCESS: Data retrieved successfully")
                print(f"Origin: {retrieve_result['data']['origin']}")
                print(f"Destination: {retrieve_result['data']['destination']}")
                
                print("Testing data cleanup...")
                cleanup_result = storage.delete_session_data(session_id)
                
                if cleanup_result["success"]:
                    print(f"SUCCESS: Cleanup completed, deleted {cleanup_result['deleted_count']} keys")
                    return True
                else:
                    print(f"FAILED: Cleanup failed: {cleanup_result['message']}")
                    return False
            else:
                print(f"FAILED: Data retrieval failed: {retrieve_result['message']}")
                return False
        else:
            print(f"FAILED: Data storage failed: {store_result['message']}")
            return False
            
    except Exception as e:
        print(f"FAILED: Storage test exception: {str(e)}")
        return False

def main():
    """Run tests"""
    print("STARTING REDIS CLOUD TESTS")
    print(f"Test time: {datetime.utcnow().isoformat()}")
    
    success_count = 0
    total_tests = 2
    
    if test_connection():
        success_count += 1
    
    if test_storage():
        success_count += 1
    
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"Passed: {success_count}/{total_tests} tests")
    
    if success_count == total_tests:
        print("SUCCESS: All tests passed! Redis Cloud is working!")
        print("Your setup supports:")
        print("- Flight search result caching")
        print("- Data compression") 
        print("- Session management")
        print("- Automatic expiration")
        return True
    else:
        print(f"FAILED: {total_tests - success_count} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)