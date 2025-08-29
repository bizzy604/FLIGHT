"""
Unified Cache Service for Flight Data

This service provides a consolidated caching interface for all flight-related data,
ensuring consistent storage, retrieval, and key management across the application.
"""
import json
import uuid
import hashlib
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from enum import Enum
import logging

from services.redis_flight_storage import redis_flight_storage

logger = logging.getLogger(__name__)

class CacheDataType(Enum):
    """Enumeration of supported cache data types"""
    FLIGHT_SEARCH = "search"
    FLIGHT_PRICE = "price"
    SEAT_AVAILABILITY = "seat_availability"
    SERVICE_LIST = "service_list"
    BOOKING = "booking"

class TTLPolicy(Enum):
    """TTL policies for different data types"""
    SHORT = 300      # 5 minutes - for volatile data like pricing
    MEDIUM = 900     # 15 minutes - for seat/service data
    LONG = 1800      # 30 minutes - for search results and booking data
    EXTENDED = 3600  # 1 hour - for reference data

class UnifiedCacheService:
    """Unified caching service with consistent behavior across all data types"""

    def __init__(self):
        """Initialize the unified cache service"""
        self.redis_storage = redis_flight_storage
        
        # Define TTL policies for different data types
        self.ttl_policies = {
            CacheDataType.FLIGHT_SEARCH: TTLPolicy.LONG.value,
            CacheDataType.FLIGHT_PRICE: TTLPolicy.LONG.value,
            CacheDataType.SEAT_AVAILABILITY: TTLPolicy.MEDIUM.value,
            CacheDataType.SERVICE_LIST: TTLPolicy.MEDIUM.value,
            CacheDataType.BOOKING: TTLPolicy.EXTENDED.value,
        }
        
        logger.info("UnifiedCacheService initialized with Redis backend")

    def generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())

    def generate_cache_key(self, data_type: CacheDataType, identifier: str) -> str:
        """
        Generate a consistent cache key format.
        
        Args:
            data_type: Type of data being cached
            identifier: Unique identifier (session_id, offer_id, etc.)
        
        Returns:
            Consistent cache key string
        """
        return f"{data_type.value}_{identifier}"

    def store_data(
        self,
        data_type: CacheDataType,
        data: Dict[str, Any],
        identifier: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Store data in cache with automatic key generation and TTL assignment.
        
        Args:
            data_type: Type of data being cached
            data: Data to be cached
            identifier: Optional identifier, generates UUID if not provided
            ttl: Optional TTL, uses policy default if not provided
        
        Returns:
            Dictionary with success status, identifier, and metadata
        """
        try:
            # Generate identifier if not provided
            if not identifier:
                identifier = self.generate_session_id()
            
            # Use default TTL for data type if not specified
            if not ttl:
                ttl = self.ttl_policies.get(data_type, TTLPolicy.MEDIUM.value)
            
            # Route to appropriate storage method
            result = None
            if data_type == CacheDataType.FLIGHT_SEARCH:
                result = self.redis_storage.store_flight_search(data, identifier, ttl)
            elif data_type == CacheDataType.FLIGHT_PRICE:
                result = self.redis_storage.store_flight_price(data, identifier, ttl)
            elif data_type == CacheDataType.SEAT_AVAILABILITY:
                result = self.redis_storage.store_seat_availability(data, identifier, ttl)
            elif data_type == CacheDataType.SERVICE_LIST:
                result = self.redis_storage.store_service_list(data, identifier, ttl)
            elif data_type == CacheDataType.BOOKING:
                result = self.redis_storage.store_booking_data(data, identifier, ttl)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            if result and result.get('success'):
                logger.info(f"Successfully stored {data_type.value} data with identifier: {identifier}")
                return {
                    "success": True,
                    "identifier": identifier,
                    "data_type": data_type.value,
                    "ttl": ttl,
                    "expires_at": result.get("expires_at"),
                    "message": f"{data_type.value} data cached successfully"
                }
            else:
                logger.warning(f"Failed to store {data_type.value} data: {result.get('message') if result else 'Unknown error'}")
                return {
                    "success": False,
                    "error": result.get('error') if result else 'Storage operation failed',
                    "message": f"Failed to cache {data_type.value} data"
                }
            
        except Exception as e:
            logger.error(f"Error storing {data_type.value} data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while caching {data_type.value} data"
            }

    def retrieve_data(
        self,
        data_type: CacheDataType,
        identifier: str
    ) -> Dict[str, Any]:
        """
        Retrieve data from cache.
        
        Args:
            data_type: Type of data being retrieved
            identifier: Identifier used when storing the data
        
        Returns:
            Dictionary with success status and retrieved data or error info
        """
        try:
            # Route to appropriate retrieval method
            result = None
            if data_type == CacheDataType.FLIGHT_SEARCH:
                result = self.redis_storage.get_flight_search(identifier)
            elif data_type == CacheDataType.FLIGHT_PRICE:
                result = self.redis_storage.get_flight_price(identifier)
            elif data_type == CacheDataType.SEAT_AVAILABILITY:
                result = self.redis_storage.get_seat_availability(identifier)
            elif data_type == CacheDataType.SERVICE_LIST:
                result = self.redis_storage.get_service_list(identifier)
            elif data_type == CacheDataType.BOOKING:
                result = self.redis_storage.get_booking_data(identifier)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            if result and result.get('success'):
                logger.info(f"Successfully retrieved {data_type.value} data with identifier: {identifier}")
                return {
                    "success": True,
                    "data": result.get("data"),
                    "data_type": data_type.value,
                    "identifier": identifier,
                    "stored_at": result.get("stored_at"),
                    "expires_at": result.get("expires_at"),
                    "message": f"{data_type.value} data retrieved successfully"
                }
            else:
                logger.info(f"No {data_type.value} data found for identifier: {identifier}")
                return {
                    "success": False,
                    "error": result.get('error') if result else 'Data not found',
                    "message": f"No {data_type.value} data found for identifier: {identifier}"
                }
            
        except Exception as e:
            logger.error(f"Error retrieving {data_type.value} data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while retrieving {data_type.value} data"
            }

    def delete_data(
        self,
        data_type: CacheDataType,
        identifier: str
    ) -> Dict[str, Any]:
        """
        Delete specific data from cache.
        
        Args:
            data_type: Type of data being deleted
            identifier: Identifier of the data to delete
        
        Returns:
            Dictionary with success status and deletion info
        """
        try:
            # For now, use the session deletion which removes all data for a session
            result = self.redis_storage.delete_session_data(identifier)
            
            if result and result.get('success'):
                logger.info(f"Successfully deleted data for identifier: {identifier}")
                return {
                    "success": True,
                    "identifier": identifier,
                    "deleted_count": result.get("deleted_count", 0),
                    "message": f"Data deleted for identifier: {identifier}"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error') if result else 'Deletion failed',
                    "message": f"Failed to delete data for identifier: {identifier}"
                }
            
        except Exception as e:
            logger.error(f"Error deleting data for identifier {identifier}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while deleting data for identifier: {identifier}"
            }

    def get_cache_health(self) -> Dict[str, Any]:
        """
        Get cache health status and statistics.
        
        Returns:
            Dictionary with cache health information
        """
        try:
            # Test Redis connection
            from config.redis_config import test_redis_connection
            redis_health = test_redis_connection()
            
            return {
                "success": True,
                "redis_available": self.redis_storage.redis_available,
                "redis_connection": redis_health,
                "ttl_policies": {dt.name: ttl for dt, ttl in self.ttl_policies.items()},
                "supported_data_types": [dt.value for dt in CacheDataType],
                "message": "Cache service is operational"
            }
            
        except Exception as e:
            logger.error(f"Error getting cache health: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get cache health status"
            }

    def generate_deterministic_key(self, data: Dict[str, Any]) -> str:
        """
        Generate a deterministic cache key based on data content.
        
        Args:
            data: Data to generate key from
        
        Returns:
            MD5 hash string that can be used as identifier
        """
        try:
            # Sort data for consistent hashing
            sorted_data = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(sorted_data.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to generate deterministic key: {e}")
            return str(uuid.uuid4())

    def batch_store(
        self,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store multiple items in batch with support for different data types.
        
        Args:
            operations: List of operations, each containing data_type, data, and optional identifier/ttl
        
        Returns:
            Dictionary with batch operation results
        """
        results = []
        successful = 0
        failed = 0
        
        for op in operations:
            try:
                data_type = CacheDataType(op.get('data_type'))
                data = op.get('data')
                identifier = op.get('identifier')
                ttl = op.get('ttl')
                
                result = self.store_data(data_type, data, identifier, ttl)
                results.append(result)
                
                if result.get('success'):
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                results.append({
                    "success": False,
                    "error": str(e),
                    "message": "Invalid operation parameters"
                })
        
        return {
            "success": failed == 0,
            "total_operations": len(operations),
            "successful": successful,
            "failed": failed,
            "results": results,
            "message": f"Batch operation completed: {successful} successful, {failed} failed"
        }


# Create a singleton instance
unified_cache_service = UnifiedCacheService()