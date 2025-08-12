#!/usr/bin/env python3
"""
Simple utility to clear flight-related cache from Redis
"""
import os
import sys
from config.redis_config import get_redis_connection

def clear_flight_cache():
    """Clear all flight-related cache data"""
    try:
        # Get Redis connection using the same config as the app
        redis_client = get_redis_connection()
        
        if not redis_client:
            print("Could not connect to Redis")
            return False
            
        # Get all keys
        print("Scanning Redis for flight-related keys...")
        all_keys = redis_client.keys('*')
        print(f"Found {len(all_keys)} total keys in Redis")
        
        # Filter flight-related keys
        flight_patterns = [
            'flight_search:',
            'flight_price:',
            'flight:',
            'air_shopping_raw_',
            'flight_price_raw_',
            'flight_price_response:'
        ]
        
        flight_keys = []
        for key in all_keys:
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            if any(pattern in key_str for pattern in flight_patterns):
                flight_keys.append(key)
        
        print(f"Found {len(flight_keys)} flight-related keys:")
        
        # Show keys to be deleted
        for key in flight_keys[:10]:  # Show first 10
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            print(f"  - {key_str}")
        
        if len(flight_keys) > 10:
            print(f"  ... and {len(flight_keys) - 10} more keys")
        
        if flight_keys:
            # Delete all flight keys
            deleted_count = redis_client.delete(*flight_keys)
            print(f"Successfully cleared {deleted_count} flight cache keys")
        else:
            print("No flight cache keys found to clear")
            
        return True
        
    except Exception as e:
        print(f"Error clearing cache: {str(e)}")
        return False

if __name__ == "__main__":
    print("Flight Cache Cleaner")
    print("=" * 50)
    success = clear_flight_cache()
    if success:
        print("Cache clearing completed successfully")
    else:
        print("Cache clearing failed")
        sys.exit(1)