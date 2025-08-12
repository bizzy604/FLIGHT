"""
Redis-based Flight Data Storage Service

This service provides persistent storage for flight search data, pricing data,
and booking data using Redis with automatic expiration.
"""
import json
import uuid
import gzip
import base64
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging

import redis
import os
from config.redis_config import get_redis_connection, _mask_password

logger = logging.getLogger(__name__)

class RedisFlightStorage:
    """Redis-based storage for flight data with automatic expiration."""

    def __init__(self):
        """Initialize Redis Flight Storage with enhanced connection handling"""
        try:
            # Use the centralized Redis connection configuration
            self.redis_client = get_redis_connection()
            self.redis_available = True
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            logger.info(f"Redis Flight Storage initialized successfully using: {_mask_password(redis_url)}")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without Redis cache.")
            self.redis_client = None
            self.redis_available = False

        self.default_ttl = 300  # 5 minutes in seconds (reduced to match typical offer expiration times)
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for flight data."""
        return str(uuid.uuid4())
    
    def _get_key(self, session_id: str, data_type: str) -> str:
        """Generate Redis key for flight data."""
        return f"flight:{data_type}:{session_id}"

    def _compress_data(self, data: Dict[str, Any]) -> str:
        """Compress data using gzip and base64 encoding."""
        try:
            # Convert to JSON string
            json_str = json.dumps(data, default=str)

            # Compress using gzip
            compressed = gzip.compress(json_str.encode('utf-8'))

            # Encode to base64 for storage
            encoded = base64.b64encode(compressed).decode('utf-8')

            logger.info(f"Data compression: {len(json_str)} -> {len(encoded)} bytes ({len(encoded)/len(json_str)*100:.1f}%)")

            return encoded
        except Exception as e:
            logger.error(f"Failed to compress data: {str(e)}")
            raise

    def _decompress_data(self, encoded_data: str) -> Dict[str, Any]:
        """Decompress data from base64 and gzip."""
        try:
            # Decode from base64
            compressed = base64.b64decode(encoded_data.encode('utf-8'))

            # Decompress using gzip
            json_str = gzip.decompress(compressed).decode('utf-8')

            # Parse JSON
            data = json.loads(json_str)

            return data
        except Exception as e:
            logger.error(f"Failed to decompress data: {str(e)}")
            raise
    
    def store_flight_search(
        self,
        search_data: Dict[str, Any],
        session_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Store flight search data in Redis.

        Args:
            search_data: Flight search response data
            session_id: Optional session ID, generates new one if not provided
            ttl: Time to live in seconds, uses default if not provided

        Returns:
            Dict with success status, session_id, and any error messages
        """
        try:
            if not session_id:
                session_id = self._generate_session_id()

            if not ttl:
                ttl = self.default_ttl

            # If Redis is not available, return session_id but don't store
            if not self.redis_available:
                logger.warning("Redis not available, returning session_id without storage")
                return {
                    "success": True,
                    "session_id": session_id,
                    "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                    "message": "Session created (Redis unavailable - data not cached)"
                }

            key = self._get_key(session_id, "search")

            # Prepare data for storage
            storage_data = {
                "data": search_data,
                "stored_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                "data_type": "flight_search",
                "compressed": True
            }

            # Compress the data before storing
            compressed_data = self._compress_data(storage_data)

            # Store compressed data in Redis with expiration
            self.redis_client.setex(key, ttl, compressed_data)

            logger.info(f"Stored flight search data with session_id: {session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "expires_at": storage_data["expires_at"],
                "message": "Flight search data stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to store flight search data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to store flight search data"
            }
    
    def get_flight_search(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve flight search data from Redis.

        Args:
            session_id: Session ID to retrieve data for

        Returns:
            Dict with success status, data, and any error messages
        """
        try:
            # If Redis is not available, return not found
            if not self.redis_available:
                logger.warning("Redis not available, cannot retrieve flight search data")
                return {
                    "success": False,
                    "error": "Redis cache unavailable",
                    "message": "Flight search data cannot be retrieved (Redis unavailable)"
                }

            key = self._get_key(session_id, "search")
            stored_data = self.redis_client.get(key)

            if not stored_data:
                return {
                    "success": False,
                    "error": "Flight search data not found or expired",
                    "message": "No flight search data found for this session"
                }

            # Check if data is compressed
            try:
                # Try to decompress first (new format)
                parsed_data = self._decompress_data(stored_data)
                logger.info(f"Retrieved compressed flight search data for session_id: {session_id}")
            except:
                # Fallback to uncompressed format (old format)
                parsed_data = json.loads(stored_data)
                logger.info(f"Retrieved uncompressed flight search data for session_id: {session_id}")

            return {
                "success": True,
                "data": parsed_data["data"],
                "stored_at": parsed_data["stored_at"],
                "expires_at": parsed_data["expires_at"],
                "message": "Flight search data retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve flight search data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve flight search data"
            }
    
    def store_flight_price(
        self,
        price_data: Dict[str, Any],
        session_id: str,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Store flight price data in Redis.

        Args:
            price_data: Flight price response data
            session_id: Session ID to associate data with
            ttl: Time to live in seconds, uses default if not provided

        Returns:
            Dict with success status and any error messages
        """
        try:
            if not ttl:
                ttl = self.default_ttl

            # If Redis is not available, return success but don't store
            if not self.redis_available:
                logger.warning("Redis not available, cannot store flight price data")
                return {
                    "success": True,
                    "session_id": session_id,
                    "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                    "message": "Flight price data processed (Redis unavailable - data not cached)"
                }

            key = self._get_key(session_id, "price")

            # Prepare data for storage
            storage_data = {
                "data": price_data,
                "stored_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                "data_type": "flight_price"
            }

            # Store in Redis with expiration
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(storage_data, default=str)
            )

            logger.info(f"Stored flight price data for session_id: {session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "expires_at": storage_data["expires_at"],
                "message": "Flight price data stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to store flight price data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to store flight price data"
            }
    
    def get_flight_price(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve flight price data from Redis.

        Args:
            session_id: Session ID to retrieve data for

        Returns:
            Dict with success status, data, and any error messages
        """
        try:
            # If Redis is not available, return not found
            if not self.redis_available:
                logger.warning("Redis not available, cannot retrieve flight price data")
                return {
                    "success": False,
                    "error": "Redis cache unavailable",
                    "message": "Flight price data cannot be retrieved (Redis unavailable)"
                }

            key = self._get_key(session_id, "price")
            stored_data = self.redis_client.get(key)

            if not stored_data:
                return {
                    "success": False,
                    "error": "Flight price data not found or expired",
                    "message": "No flight price data found for this session"
                }

            parsed_data = json.loads(stored_data)

            logger.info(f"Retrieved flight price data for session_id: {session_id}")

            return {
                "success": True,
                "data": parsed_data["data"],
                "stored_at": parsed_data["stored_at"],
                "expires_at": parsed_data["expires_at"],
                "message": "Flight price data retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve flight price data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve flight price data"
            }
    
    def store_booking_data(
        self,
        booking_data: Dict[str, Any],
        session_id: str,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Store booking data in Redis.

        Args:
            booking_data: Booking response data
            session_id: Session ID to associate data with
            ttl: Time to live in seconds, uses default if not provided

        Returns:
            Dict with success status and any error messages
        """
        try:
            if not ttl:
                ttl = self.default_ttl

            # If Redis is not available, return success but don't store
            if not self.redis_available:
                logger.warning("Redis not available, cannot store booking data")
                return {
                    "success": True,
                    "session_id": session_id,
                    "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                    "message": "Booking data processed (Redis unavailable - data not cached)"
                }

            key = self._get_key(session_id, "booking")

            # Prepare data for storage
            storage_data = {
                "data": booking_data,
                "stored_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                "data_type": "booking_data"
            }

            # Store in Redis with expiration
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(storage_data, default=str)
            )

            logger.info(f"Stored booking data for session_id: {session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "expires_at": storage_data["expires_at"],
                "message": "Booking data stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to store booking data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to store booking data"
            }
    
    def get_booking_data(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve booking data from Redis.

        Args:
            session_id: Session ID to retrieve data for

        Returns:
            Dict with success status, data, and any error messages
        """
        try:
            # If Redis is not available, return not found
            if not self.redis_available:
                logger.warning("Redis not available, cannot retrieve booking data")
                return {
                    "success": False,
                    "error": "Redis cache unavailable",
                    "message": "Booking data cannot be retrieved (Redis unavailable)"
                }

            key = self._get_key(session_id, "booking")
            stored_data = self.redis_client.get(key)

            if not stored_data:
                return {
                    "success": False,
                    "error": "Booking data not found or expired",
                    "message": "No booking data found for this session"
                }

            parsed_data = json.loads(stored_data)

            logger.info(f"Retrieved booking data for session_id: {session_id}")

            return {
                "success": True,
                "data": parsed_data["data"],
                "stored_at": parsed_data["stored_at"],
                "expires_at": parsed_data["expires_at"],
                "message": "Booking data retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve booking data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve booking data"
            }
    
    def delete_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        Delete all flight data for a session.

        Args:
            session_id: Session ID to delete data for

        Returns:
            Dict with success status and any error messages
        """
        try:
            # If Redis is not available, return success (nothing to delete)
            if not self.redis_available:
                logger.warning("Redis not available, cannot delete session data")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "Session data deletion skipped (Redis unavailable)"
                }

            keys_to_delete = [
                self._get_key(session_id, "search"),
                self._get_key(session_id, "price"),
                self._get_key(session_id, "booking")
            ]

            deleted_count = self.redis_client.delete(*keys_to_delete)

            logger.info(f"Deleted {deleted_count} keys for session_id: {session_id}")

            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} data entries for session"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete session data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete session data"
            }

# Create a singleton instance
redis_flight_storage = RedisFlightStorage()
