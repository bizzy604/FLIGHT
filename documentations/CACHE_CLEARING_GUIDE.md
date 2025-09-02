# Flight Cache Clearing Guide

This guide provides comprehensive methods to clear flight price cache data and other cached information in your flight booking system.

## 🚀 Quick Start

### Most Common Use Case - Clear All Flight Cache
```bash
cd Backend
python clear_cache.py
```

## 📋 Available Cache Clearing Methods

### Method 1: Original Cache Cleaner ⚡ (Recommended)

**File:** `Backend/clear_cache.py`

**Usage:**
```bash
cd Backend
python clear_cache.py
```

**What it clears:**
- All flight search cache (`flight:search:*`)
- All flight price cache (`flight:price:*`, `flight_price_*`)
- Legacy air shopping cache (`air_shopping_raw_*`)
- Flight price responses (`flight_price_response:*`)

**Output example:**
```
Flight Cache Cleaner
==================================================
Scanning Redis for flight-related keys...
Found 15 total keys in Redis
Found 8 flight-related keys:
  - flight:price:abc123def456
  - flight:search:xyz789ghi012
  ... and 6 more keys
Successfully cleared 8 flight cache keys
Cache clearing completed successfully
```

### Method 2: Enhanced Cache Cleaner 🔧 (Advanced)

**File:** `Backend/enhanced_cache_clearer.py`

**Basic Usage:**
```bash
cd Backend

# Show current cache status
python enhanced_cache_clearer.py --status

# Clear all flight cache (with confirmation)
python enhanced_cache_clearer.py --type all

# Clear specific cache types
python enhanced_cache_clearer.py --type price --confirm
python enhanced_cache_clearer.py --type search --confirm
python enhanced_cache_clearer.py --type seat --confirm
python enhanced_cache_clearer.py --type service --confirm
python enhanced_cache_clearer.py --type booking --confirm

# Clear cache for specific session
python enhanced_cache_clearer.py --session YOUR_SESSION_ID_HERE
```

**Available cache types:**
- `all` - All flight-related cache
- `price` - Flight pricing cache only
- `search` - Flight search results cache only
- `seat` - Seat availability cache only
- `service` - Additional services cache only
- `booking` - Booking confirmation cache only

**Status report example:**
```
🚀 Enhanced Flight Cache Cleaner
==================================================

📊 CACHE STATUS REPORT
==================================================
Total Redis keys: 12
  🔹 Price cache: 5 keys
  🔹 Search cache: 4 keys  
  🔹 Seat cache: 2 keys
  🔹 Service cache: 1 keys

🏥 Cache Health: ✅ Healthy
   Cache service operational

🕒 Report generated: 2025-08-26 20:28:38
```

### Method 3: API Endpoints 🌐 (When Server is Running)

**Prerequisites:** Backend server must be running (`python app.py`)

**Clear all cache:**
```bash
curl -X POST http://localhost:5000/api/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"identifier": "all"}'
```

**Clear specific session:**
```bash
curl -X POST http://localhost:5000/api/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"identifier": "your_session_id_here"}'
```

**Check cache health:**
```bash
curl http://localhost:5000/api/cache/health
```

**Get cache statistics:**
```bash
curl http://localhost:5000/api/cache/stats
```

**API Response example:**
```json
{
  "success": true,
  "message": "Deleted 5 data entries for session",
  "deleted_count": 5,
  "identifier": "all",
  "timestamp": "2025-08-26T17:26:39.039684"
}
```

## 🔍 Troubleshooting Cache Issues

### Problem: Still Getting Cached Flight Prices

**Step 1:** Check current cache status
```bash
cd Backend
python enhanced_cache_clearer.py --status
```

**Step 2:** Clear all cache with confirmation
```bash
python enhanced_cache_clearer.py --type all --confirm
```

**Step 3:** Check browser cache
- Open browser Developer Tools (F12)
- Go to Application/Storage tab
- Clear localStorage and sessionStorage
- Hard refresh page (Ctrl+F5)

**Step 4:** Find your session ID and clear specific session
```bash
# Check browser developer tools for session ID
# Then run:
python enhanced_cache_clearer.py --session YOUR_SESSION_ID
```

### Problem: Cache Cleaner Shows "No keys found" but still getting cached data

This usually means:
1. **Browser caching** - Clear browser cache/localStorage
2. **Frontend caching** - Restart frontend development server
3. **Session-specific cache** - Use session ID to clear specific cache
4. **Different cache service** - Some cache might be in memory cache vs Redis

**Solutions:**
```bash
# Backend: Restart server
cd Backend
# Stop server (Ctrl+C) then restart
python app.py

# Frontend: Clear Next.js cache and restart
cd Frontend
rm -rf .next
npm run dev
```

### Problem: Redis Connection Issues

**Check Redis connection:**
```bash
cd Backend
python -c "from config.redis_config import test_redis_connection; print(test_redis_connection())"
```

**Expected output:**
```json
{'success': True, 'message': 'Redis connection successful', 'redis_info': {...}}
```

## 📊 Cache Architecture Overview

### Cache Types and Patterns

| Cache Type | Redis Key Pattern | TTL | Description |
|------------|------------------|-----|-------------|
| Flight Search | `flight:search:*` | 15min | Air shopping results |
| Flight Pricing | `flight:price:*` | 30min | Flight price calculations |
| Seat Availability | `flight:seat_availability:*` | 10min | Available seats |
| Service List | `flight:service_list:*` | 1hr | Additional services |
| Booking Data | `flight:booking:*` | 2hr | Booking confirmations |

### Legacy Patterns (Still Supported)
- `air_shopping_raw_*`
- `flight_price_raw_*` 
- `flight_price_response:*`

### Cache Services Used
- **Redis Cloud** - Primary cache storage
- **SimpleFlightCache** - Unified cache service wrapper
- **In-memory cache** - Local rate limiting and temporary storage

## 🛠️ Advanced Operations

### Create Custom Cache Cleaner Script

```python
#!/usr/bin/env python3
from config.redis_config import get_redis_connection

def clear_custom_cache_pattern(pattern):
    redis_client = get_redis_connection()
    keys = redis_client.keys(f"*{pattern}*")
    if keys:
        deleted = redis_client.delete(*keys)
        print(f"Cleared {deleted} keys matching '{pattern}'")
    else:
        print(f"No keys found matching '{pattern}'")

# Usage
clear_custom_cache_pattern("flight:price:")
```

### Monitor Cache in Real-time

```bash
# Watch cache changes
cd Backend
watch -n 2 "python enhanced_cache_clearer.py --status"
```

### Scheduled Cache Clearing

Add to crontab for scheduled clearing:
```bash
# Clear cache every hour
0 * * * * cd /path/to/Backend && python clear_cache.py

# Clear only price cache every 30 minutes  
*/30 * * * * cd /path/to/Backend && python enhanced_cache_clearer.py --type price --confirm
```

## 📝 Best Practices

### When to Clear Cache

1. **Development:** Clear cache when testing new pricing logic
2. **After API changes:** Clear cache when backend API responses change
3. **User reports stale data:** Clear specific session cache
4. **Performance issues:** Clear all cache if memory usage is high
5. **Deployment:** Clear cache after production deployments

### Which Method to Use

- **Daily development:** Use `clear_cache.py` (Method 1)
- **Debugging specific issues:** Use enhanced cleaner (Method 2)  
- **Production monitoring:** Use API endpoints (Method 3)
- **Automated scripts:** Use enhanced cleaner with `--confirm` flag

### Cache Clearing Order

1. **Start with session-specific** if you know the session ID
2. **Then try cache-type specific** (e.g., just price cache)
3. **Finally use full clear** if issues persist
4. **Check browser cache** if backend cache is clear but still seeing cached data

## 🚨 Important Notes

- **Production Warning:** Always backup important data before clearing production cache
- **Performance Impact:** Clearing cache will temporarily increase API calls until cache rebuilds
- **Session IDs:** Can be found in browser developer tools under Application → Local Storage
- **TTL Awareness:** Some cache expires automatically - check TTL before manual clearing
- **Multi-instance:** If running multiple app instances, clear cache on all instances

## 🔗 Related Files

- `Backend/clear_cache.py` - Original cache cleaner
- `Backend/enhanced_cache_clearer.py` - Enhanced cache cleaner
- `Backend/routes/cache_health.py` - Cache health API endpoints
- `Backend/services/simple_flight_cache.py` - Main cache service
- `Backend/config/redis_config.py` - Redis configuration
- `CLAUDE.md` - Development guidelines and commands

## 📞 Support

If cache clearing issues persist:

1. Check Redis connection status
2. Verify environment variables (REDIS_URL, etc.)
3. Check application logs for cache-related errors
4. Use `--status` flag to monitor cache state
5. Consider restarting both backend and frontend services

---

*Last updated: 2025-08-26*
*Created for Flight Booking Portal cache management*