"""
Async Decorators for Flight Service

This module contains decorators for caching and rate limiting async functions.
"""
from typing import TypeVar, Callable, Awaitable, Any, Optional
from functools import wraps
from utils.cache_manager import cache_manager
from services.flight.exceptions import RateLimitExceeded

# Type variable for generic function typing
T = TypeVar('T')

def async_cache(timeout: int = 300, key_prefix: str = 'acache_') -> Callable:
    """
    Decorator to cache async function results.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated async function with caching
    """
    def decorator(f: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(f)
        async def decorated_function(*args: Any, **kwargs: Any) -> T:
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get cached result
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call the async function if not in cache
            result = await f(*args, **kwargs)
            
            # Cache the result if not None
            if result is not None:
                cache_manager.set(cache_key, result, timeout)
                
            return result
        return decorated_function
    return decorator

def async_rate_limited(limit: int = 100, window: int = 60, key_prefix: str = 'arl_') -> Callable:
    """
    Decorator to rate limit async function calls.
    
    Args:
        limit: Maximum number of requests allowed in the time window
        window: Time window in seconds (default: 60)
        key_prefix: Prefix for rate limit keys
        
    Returns:
        Decorated async function with rate limiting
    """
    def decorator(f: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(f)
        async def decorated_function(*args: Any, **kwargs: Any) -> T:
            # Generate rate limit key
            rate_key = f"{key_prefix}{f.__name__}:{str(args)[:50]}"
            
            if cache_manager.rate_limit(rate_key, limit, window):
                raise RateLimitExceeded("Rate limit exceeded. Please try again later.")
                
            return await f(*args, **kwargs)
        return decorated_function
    return decorator
