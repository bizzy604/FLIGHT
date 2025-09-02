"""
Simple Flight Cache Service - Replacement for complex cache system
Demonstrates how to use the new simplified cache system
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from services.unified_cache_service import UnifiedCacheService, CacheDataType
from services.redis_flight_storage import redis_flight_storage

logger = logging.getLogger(__name__)


class SimpleFlightCache:
    """
    Simplified flight cache service using the existing cache system
    Replaces complex cache operations with clean, simple interface
    """
    
    def __init__(self):
        self.unified_cache = UnifiedCacheService()
        self.redis_storage = redis_flight_storage
        logger.info("SimpleFlightCache initialized")
    
    # FLIGHT SEARCH OPERATIONS
    
    def store_flight_search(self, session_id: str, search_data: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store flight search data - replaces complex store_flight_search"""
        try:
            result = self.redis_storage.store_flight_search(search_data, session_id, ttl)
            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "cache_key": result.get("session_id", session_id),
                "message": "Flight search data stored" if result.get("success", False) else "Failed to store flight search data",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error storing flight search: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "cache_key": session_id,
                "message": "Failed to store flight search data",
                "error": str(e)
            }
    
    def get_flight_search(self, session_id: str) -> Dict[str, Any]:
        """Get flight search data - replaces complex get_flight_search"""
        try:
            result = self.redis_storage.get_flight_search(session_id)
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "cache_hit": result.get("success", False),
                "message": "Flight search data retrieved" if result.get("success", False) else "Flight search data not found",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error getting flight search: {e}")
            return {
                "success": False,
                "data": None,
                "cache_hit": False,
                "message": "Failed to retrieve flight search data",
                "error": str(e)
            }
    
    # FLIGHT PRICE OPERATIONS
    
    def store_flight_price(self, session_id: str, price_data: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store flight price data - replaces complex store_flight_price"""
        try:
            result = self.redis_storage.store_flight_price(price_data, session_id, ttl)
            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "cache_key": result.get("session_id", session_id),
                "message": "Flight price data stored" if result.get("success", False) else "Failed to store flight price data",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error storing flight price: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "cache_key": session_id,
                "message": "Failed to store flight price data",
                "error": str(e)
            }
    
    def get_flight_price(self, session_id: str) -> Dict[str, Any]:
        """Get flight price data - replaces complex get_flight_price"""
        try:
            result = self.redis_storage.get_flight_price(session_id)
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "cache_hit": result.get("success", False),
                "message": "Flight price data retrieved" if result.get("success", False) else "Flight price data not found",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error getting flight price: {e}")
            return {
                "success": False,
                "data": None,
                "cache_hit": False,
                "message": "Failed to retrieve flight price data",
                "error": str(e)
            }
    
    # SEAT AVAILABILITY OPERATIONS
    
    def store_seat_availability(self, session_id: str, seat_data: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store seat availability data - replaces complex store_seat_availability"""
        try:
            result = self.redis_storage.store_seat_availability(seat_data, session_id, ttl)
            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "cache_key": result.get("session_id", session_id),
                "storage_key": result.get("session_id", session_id),  # For backward compatibility
                "message": "Seat availability data stored" if result.get("success", False) else "Failed to store seat availability data",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error storing seat availability: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "cache_key": session_id,
                "storage_key": session_id,
                "message": "Failed to store seat availability data",
                "error": str(e)
            }
    
    def get_seat_availability(self, session_id: str) -> Dict[str, Any]:
        """Get seat availability data - replaces complex get_seat_availability"""
        try:
            result = self.redis_storage.get_seat_availability(session_id)
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "cache_hit": result.get("success", False),
                "cache_key": result.get("session_id", session_id),
                "storage_key": result.get("session_id", session_id),  # For backward compatibility
                "message": "Seat availability data retrieved" if result.get("success", False) else "Seat availability data not found",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error getting seat availability: {e}")
            return {
                "success": False,
                "data": None,
                "cache_hit": False,
                "cache_key": session_id,
                "storage_key": session_id,
                "message": "Failed to retrieve seat availability data",
                "error": str(e)
            }
    
    # SERVICE LIST OPERATIONS
    
    def store_service_list(self, session_id: str, service_data: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store service list data - replaces complex store_service_list"""
        try:
            result = self.redis_storage.store_service_list(service_data, session_id, ttl)
            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "cache_key": result.get("session_id", session_id),
                "message": "Service list data stored" if result.get("success", False) else "Failed to store service list data",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error storing service list: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "cache_key": session_id,
                "message": "Failed to store service list data",
                "error": str(e)
            }
    
    def get_service_list(self, session_id: str) -> Dict[str, Any]:
        """Get service list data - replaces complex get_service_list"""
        try:
            result = self.redis_storage.get_service_list(session_id)
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "cache_hit": result.get("success", False),
                "message": "Service list data retrieved" if result.get("success", False) else "Service list data not found",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error getting service list: {e}")
            return {
                "success": False,
                "data": None,
                "cache_hit": False,
                "message": "Failed to retrieve service list data",
                "error": str(e)
            }
    
    # BOOKING OPERATIONS
    
    def store_booking_data(self, session_id: str, booking_data: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store booking data - replaces complex store_booking_data"""
        try:
            result = self.redis_storage.store_booking_data(booking_data, session_id, ttl)
            return {
                "success": result.get("success", False),
                "session_id": session_id,
                "cache_key": result.get("session_id", session_id),
                "message": "Booking data stored" if result.get("success", False) else "Failed to store booking data",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error storing booking data: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "cache_key": session_id,
                "message": "Failed to store booking data",
                "error": str(e)
            }
    
    def get_booking_data(self, session_id: str) -> Dict[str, Any]:
        """Get booking data - replaces complex get_booking_data"""
        try:
            result = self.redis_storage.get_booking_data(session_id)
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "cache_hit": result.get("success", False),
                "message": "Booking data retrieved" if result.get("success", False) else "Booking data not found",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error getting booking data: {e}")
            return {
                "success": False,
                "data": None,
                "cache_hit": False,
                "message": "Failed to retrieve booking data",
                "error": str(e)
            }
    
    # UTILITY OPERATIONS
    
    def delete_session_data(self, session_id: str) -> Dict[str, Any]:
        """Delete all data for a session - replaces complex delete_session_data"""
        try:
            deleted_count = 0
            # Delete all data types for the session
            for data_type in [CacheDataType.FLIGHT_SEARCH, CacheDataType.FLIGHT_PRICE, 
                            CacheDataType.SEAT_AVAILABILITY, CacheDataType.SERVICE_LIST, 
                            CacheDataType.BOOKING]:
                try:
                    key = f"{data_type.value}_{session_id}"
                    if self.redis_storage.redis_available:
                        self.redis_storage.redis_client.delete(key)
                        deleted_count += 1
                except Exception:
                    pass
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} data entries for session"
            }
        except Exception as e:
            logger.error(f"Error deleting session data: {e}")
            return {
                "success": False,
                "deleted_count": 0,
                "message": "Failed to delete session data",
                "error": str(e)
            }
    
    def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status - replaces complex get_cache_health"""
        try:
            health = {
                "healthy": self.redis_storage.redis_available,
                "message": "Redis cache is available" if self.redis_storage.redis_available else "Redis cache is not available"
            }
            
            stats = {
                "redis_available": self.redis_storage.redis_available,
                "cache_service": "SimpleFlightCache",
                "backend": "RedisFlightStorage"
            }
            
            return {
                "success": health["healthy"],
                "message": health["message"],
                "stats": stats,
                "cache_service": "SimpleFlightCache"
            }
        except Exception as e:
            logger.error(f"Error getting cache health: {e}")
            return {
                "success": False,
                "message": "Failed to get cache health",
                "stats": {"error": str(e)},
                "cache_service": "SimpleFlightCache"
            }
    
    # CONTENT-BASED CACHING
    
    def store_by_content(self, namespace_str: str, data: Dict[str, Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        """Store data using content-based key generation"""
        try:
            # Map string namespace to enum
            namespace_map = {
                "search": CacheDataType.FLIGHT_SEARCH,
                "price": CacheDataType.FLIGHT_PRICE,
                "seat_availability": CacheDataType.SEAT_AVAILABILITY,
                "service_list": CacheDataType.SERVICE_LIST,
                "booking": CacheDataType.BOOKING
            }
            
            namespace = namespace_map.get(namespace_str, CacheDataType.FLIGHT_SEARCH)
            
            # Generate a content-based key
            import hashlib
            content_hash = hashlib.md5(str(data).encode()).hexdigest()[:8]
            cache_key = f"{namespace.value}_{content_hash}"
            
            # Store using the appropriate method
            if namespace == CacheDataType.FLIGHT_SEARCH:
                result = self.store_flight_search(cache_key, data, ttl)
            elif namespace == CacheDataType.FLIGHT_PRICE:
                result = self.store_flight_price(cache_key, data, ttl)
            elif namespace == CacheDataType.SEAT_AVAILABILITY:
                result = self.store_seat_availability(cache_key, data, ttl)
            elif namespace == CacheDataType.SERVICE_LIST:
                result = self.store_service_list(cache_key, data, ttl)
            elif namespace == CacheDataType.BOOKING:
                result = self.store_booking_data(cache_key, data, ttl)
            else:
                result = {"success": False, "error": "Unknown namespace"}
            
            return {
                "success": result.get("success", False),
                "cache_key": cache_key,
                "message": f"{namespace_str} data stored with content-based key" if result.get("success", False) else f"Failed to store {namespace_str} data",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error storing by content: {e}")
            return {
                "success": False,
                "cache_key": None,
                "message": f"Failed to store {namespace_str} data",
                "error": str(e)
            }
    
    def get_by_content(self, namespace_str: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve data using content-based key generation"""
        try:
            # Map string namespace to enum
            namespace_map = {
                "search": CacheDataType.FLIGHT_SEARCH,
                "price": CacheDataType.FLIGHT_PRICE,
                "seat_availability": CacheDataType.SEAT_AVAILABILITY,
                "service_list": CacheDataType.SERVICE_LIST,
                "booking": CacheDataType.BOOKING
            }
            
            namespace = namespace_map.get(namespace_str, CacheDataType.FLIGHT_SEARCH)
            
            # Generate a content-based key
            import hashlib
            content_hash = hashlib.md5(str(data).encode()).hexdigest()[:8]
            cache_key = f"{namespace.value}_{content_hash}"
            
            # Retrieve using the appropriate method
            if namespace == CacheDataType.FLIGHT_SEARCH:
                result = self.get_flight_search(cache_key)
            elif namespace == CacheDataType.FLIGHT_PRICE:
                result = self.get_flight_price(cache_key)
            elif namespace == CacheDataType.SEAT_AVAILABILITY:
                result = self.get_seat_availability(cache_key)
            elif namespace == CacheDataType.SERVICE_LIST:
                result = self.get_service_list(cache_key)
            elif namespace == CacheDataType.BOOKING:
                result = self.get_booking_data(cache_key)
            else:
                result = {"success": False, "error": "Unknown namespace"}
            
            return {
                "success": result.get("success", False),
                "data": result.get("data"),
                "cache_hit": result.get("cache_hit", False),
                "cache_key": cache_key,
                "message": f"{namespace_str} data retrieved with content-based key" if result.get("success", False) else f"{namespace_str} data not found",
                "error": result.get("error") if not result.get("success", False) else None
            }
        except Exception as e:
            logger.error(f"Error getting by content: {e}")
            return {
                "success": False,
                "data": None,
                "cache_hit": False,
                "cache_key": None,
                "message": f"Failed to retrieve {namespace_str} data",
                "error": str(e)
            }


# Create singleton instance
simple_flight_cache = SimpleFlightCache()