#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced flight cache cleaner with multiple clearing options
"""
import os
import sys
import argparse
from datetime import datetime
from config.redis_config import get_redis_connection
from services.simple_flight_cache import simple_flight_cache
from services.redis_flight_storage import redis_flight_storage

# Fix Windows console encoding
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def clear_all_flight_cache():
    """Clear all flight-related cache data from Redis"""
    try:
        redis_client = get_redis_connection()
        
        if not redis_client:
            print("Could not connect to Redis")
            return False
            
        print("Scanning Redis for flight-related keys...")
        all_keys = redis_client.keys('*')
        print(f"Found {len(all_keys)} total keys in Redis")
        
        # Enhanced flight patterns
        flight_patterns = [
            'flight:',              # New consistent format
            'air_shopping_raw_',    # Legacy patterns
            'flight_price_raw_',
            'flight_price_response:',
            'seat_availability:',
            'service_list:',
            'booking:'
        ]
        
        flight_keys = []
        for key in all_keys:
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            if any(pattern in key_str for pattern in flight_patterns):
                flight_keys.append(key)
        
        print(f"Found {len(flight_keys)} flight-related keys")
        
        if flight_keys:
            # Show first 10 keys
            for i, key in enumerate(flight_keys[:10]):
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                print(f"  {key_str}")
            
            if len(flight_keys) > 10:
                print(f"  ... and {len(flight_keys) - 10} more keys")
            
            deleted_count = redis_client.delete(*flight_keys)
            print(f"Successfully cleared {deleted_count} flight cache keys")
        else:
            print("No flight cache keys found to clear")
            
        return True
        
    except Exception as e:
        print(f"Error clearing cache: {str(e)}")
        return False

def clear_specific_cache_type(cache_type):
    """Clear specific cache type (price, search, etc.)"""
    try:
        redis_client = get_redis_connection()
        
        if not redis_client:
            print("Could not connect to Redis")
            return False
        
        print(f"Scanning for {cache_type} cache keys...")
        
        # Define patterns for specific cache types
        type_patterns = {
            'price': ['flight_price_', 'flight:price:'],
            'search': ['air_shopping_', 'flight:search:'],
            'seat': ['seat_availability:', 'flight:seat_availability:'],
            'service': ['service_list:', 'flight:service_list:'],
            'booking': ['booking:', 'flight:booking:']
        }
        
        if cache_type not in type_patterns:
            print(f"Unknown cache type: {cache_type}")
            print(f"Available types: {', '.join(type_patterns.keys())}")
            return False
        
        all_keys = redis_client.keys('*')
        patterns = type_patterns[cache_type]
        
        matching_keys = []
        for key in all_keys:
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            if any(pattern in key_str for pattern in patterns):
                matching_keys.append(key)
        
        print(f"Found {len(matching_keys)} {cache_type} cache keys")
        
        if matching_keys:
            for key in matching_keys:
                key_str = key.decode() if isinstance(key, bytes) else str(key)
                print(f"  {key_str}")
            
            deleted_count = redis_client.delete(*matching_keys)
            print(f"Successfully cleared {deleted_count} {cache_type} cache keys")
        else:
            print(f"No {cache_type} cache keys found to clear")
            
        return True
        
    except Exception as e:
        print(f"Error clearing {cache_type} cache: {str(e)}")
        return False

def clear_session_cache(session_id):
    """Clear cache for a specific session ID"""
    try:
        print(f"Clearing cache for session: {session_id}")
        
        # Use the simple_flight_cache service
        result = simple_flight_cache.delete_session_data(session_id)
        
        if result.get('success'):
            print(f"{result.get('message', 'Session cache cleared successfully')}")
            if 'deleted_count' in result:
                print(f"Deleted {result['deleted_count']} cache entries")
        else:
            print(f"Failed to clear session cache: {result.get('message', 'Unknown error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"Error clearing session cache: {str(e)}")
        return False

def show_cache_status():
    """Show current cache status"""
    try:
        redis_client = get_redis_connection()
        
        if not redis_client:
            print("Could not connect to Redis")
            return
        
        print("\nCACHE STATUS REPORT")
        print("=" * 50)
        
        all_keys = redis_client.keys('*')
        print(f"Total Redis keys: {len(all_keys)}")
        
        # Count by cache type
        cache_counts = {
            'price': 0,
            'search': 0,
            'seat': 0,
            'service': 0,
            'booking': 0,
            'other': 0
        }
        
        for key in all_keys:
            key_str = key.decode() if isinstance(key, bytes) else str(key)
            if 'flight_price_' in key_str or 'flight:price:' in key_str:
                cache_counts['price'] += 1
            elif 'air_shopping_' in key_str or 'flight:search:' in key_str:
                cache_counts['search'] += 1
            elif 'seat_availability:' in key_str or 'flight:seat_availability:' in key_str:
                cache_counts['seat'] += 1
            elif 'service_list:' in key_str or 'flight:service_list:' in key_str:
                cache_counts['service'] += 1
            elif 'booking:' in key_str or 'flight:booking:' in key_str:
                cache_counts['booking'] += 1
            elif 'flight:' in key_str:
                cache_counts['other'] += 1
        
        for cache_type, count in cache_counts.items():
            if count > 0:
                print(f"  {cache_type.capitalize()} cache: {count} keys")
        
        # Get cache health
        try:
            health = simple_flight_cache.get_cache_health()
            print(f"\n Cache Health: {'Healthy' if health.get('success') else 'Issues detected'}")
            if 'message' in health:
                print(f"   {health['message']}")
        except Exception as e:
            print(f"\n Cache Health: Could not retrieve ({e})")
        
        print(f"\n Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error getting cache status: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Flight Cache Cleaner')
    parser.add_argument('--type', choices=['all', 'price', 'search', 'seat', 'service', 'booking'], 
                       help='Specific cache type to clear')
    parser.add_argument('--session', help='Clear cache for specific session ID')
    parser.add_argument('--status', action='store_true', help='Show cache status only')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    print("Enhanced Flight Cache Cleaner")
    print("=" * 50)
    
    if args.status:
        show_cache_status()
        return
    
    if args.session:
        if not args.confirm:
            confirm = input(f"Clear cache for session '{args.session}'? (y/N): ")
            if confirm.lower() != 'y':
                print("Operation cancelled")
                return
        success = clear_session_cache(args.session)
    elif args.type == 'all':
        if not args.confirm:
            confirm = input("Clear ALL flight cache data? (y/N): ")
            if confirm.lower() != 'y':
                print("Operation cancelled")
                return
        success = clear_all_flight_cache()
    elif args.type:
        if not args.confirm:
            confirm = input(f"Clear {args.type} cache data? (y/N): ")
            if confirm.lower() != 'y':
                print("Operation cancelled")
                return
        success = clear_specific_cache_type(args.type)
    else:
        # Default behavior - show status and ask what to do
        show_cache_status()
        print(f"\nAvailable options:")
        print("  --type all      : Clear all flight cache")
        print("  --type price    : Clear only price cache")
        print("  --type search   : Clear only search cache")
        print("  --session ID    : Clear cache for specific session")
        print("  --status        : Show cache status only")
        print("  --confirm       : Skip confirmation prompts")
        return
    
    if success:
        print("\nCache clearing completed successfully!")
        print("Tip: Use --status to check current cache status")
    else:
        print("\nCache clearing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()