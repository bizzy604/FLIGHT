"""
Simple in-memory cache manager with TTL support
"""
import time
from typing import Any, Dict, Optional

class CacheManager:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._rate_limits: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache if it exists and hasn't expired."""
        if key not in self._cache:
            return None
            
        item = self._cache[key]
        if item['expires_at'] < time.time():
            del self._cache[key]
            return None
            
        return item['value']

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in the cache with a TTL in seconds."""
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self._cache.clear()
    
    def rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if a rate limit has been exceeded.
        
        Args:
            key: The rate limit key
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds
            
        Returns:
            bool: True if rate limit exceeded, False otherwise
        """
        current_time = time.time()
        
        # Remove expired rate limits
        self._rate_limits = {
            k: v for k, v in self._rate_limits.items()
            if v['expires_at'] > current_time
        }
        
        # Get or create rate limit record
        if key not in self._rate_limits:
            self._rate_limits[key] = {
                'count': 1,
                'expires_at': current_time + window
            }
            return False
        
        # Check if rate limit exceeded
        if self._rate_limits[key]['count'] >= limit:
            return True
            
        # Increment counter
        self._rate_limits[key]['count'] += 1
        return False

# Create a singleton instance
cache_manager = CacheManager()
