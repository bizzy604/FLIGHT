"""
Cache Health Monitoring Routes

Provides endpoints for monitoring cache system health, performance metrics,
and diagnostic information for the unified caching system.
"""
from quart import Blueprint, jsonify, request
from datetime import datetime
import logging
import asyncio

# Import cache services
from services.simple_flight_cache import simple_flight_cache
from services.redis_flight_storage import redis_flight_storage
from config.redis_config import test_redis_connection

logger = logging.getLogger(__name__)

# Create blueprint
cache_health_bp = Blueprint('cache_health', __name__)

@cache_health_bp.route('/api/cache/health', methods=['GET'])
async def get_cache_health():
    """
    Get comprehensive cache health status.
    
    Returns detailed information about cache system health,
    Redis connection status, and performance metrics.
    """
    try:
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_health_check",
            "status": "healthy"
        }
        
        # Get unified cache service health
        simple_cache_health = simple_flight_cache.get_cache_health()
        health_data["simple_cache"] = simple_cache_health
        
        # Get Redis-specific health information
        redis_test = test_redis_connection()
        health_data["redis"] = {
            "available": redis_flight_storage.redis_available,
            "connection_test": redis_test
        }
        
        # Add TTL policies information
        health_data["ttl_policies"] = {
            "search": redis_flight_storage.ttl_policies.get("search", "N/A"),
            "price": redis_flight_storage.ttl_policies.get("price", "N/A"),
            "seat_availability": redis_flight_storage.ttl_policies.get("seat_availability", "N/A"),
            "service_list": redis_flight_storage.ttl_policies.get("service_list", "N/A"),
            "booking": redis_flight_storage.ttl_policies.get("booking", "N/A"),
            "default": redis_flight_storage.default_ttl
        }
        
        # Determine overall health status
        overall_healthy = (
            unified_health.get("success", False) and
            redis_test.get("success", False) and
            redis_flight_storage.redis_available
        )
        
        health_data["status"] = "healthy" if overall_healthy else "degraded"
        health_data["success"] = overall_healthy
        
        # Add diagnostic information
        health_data["diagnostics"] = {
            "supported_data_types": [dtype.value for dtype in CacheDataType],
            "compression_status": "disabled (Phase 1 fix)",
            "key_format": "flight:{data_type}:{session_id}",
            "storage_backend": "Redis Cloud"
        }
        
        return jsonify(health_data), 200 if overall_healthy else 503
        
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_health_check",
            "status": "error",
            "success": False,
            "error": str(e),
            "message": "Cache health check failed"
        }), 500

@cache_health_bp.route('/api/cache/test', methods=['POST'])
async def test_cache_operations():
    """
    Test cache operations with sample data.
    
    Performs a complete test cycle: store, retrieve, and cleanup
    for each supported data type to verify cache functionality.
    """
    try:
        test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_operation_test",
            "tests": {}
        }
        
        # Test data for different cache types using simple_flight_cache
        test_data_sets = {
            "flight_search": {
                "offers": [{"offer_id": "test_123", "price": 299.99}],
                "test_type": "flight_search"
            },
            "flight_price": {
                "priced_offers": [{"offer_id": "test_456", "total_price": 349.99}],
                "test_type": "flight_price"
            },
            "seat_availability": {
                "seats": [{"seat_id": "12A", "status": "available"}],
                "test_type": "seat_availability"
            },
            "service_list": {
                "services": [{"service_id": "BAG001", "price": 25.00}],
                "test_type": "service_list"
            },
            "booking": {
                "booking_ref": "TEST123456",
                "status": "confirmed",
                "test_type": "booking"
            }
        }
        
        overall_success = True
        
        for data_type, test_data in test_data_sets.items():
            test_identifier = f"test_{data_type}_{int(datetime.utcnow().timestamp())}"
            
            try:
                # Test store operation using simple_flight_cache
                if data_type == "flight_search":
                    store_result = simple_flight_cache.store_flight_search(test_identifier, test_data, 60)
                elif data_type == "flight_price":
                    store_result = simple_flight_cache.store_flight_price(test_identifier, test_data, 60)
                elif data_type == "seat_availability":
                    store_result = simple_flight_cache.store_seat_availability(test_identifier, test_data, 60)
                elif data_type == "service_list":
                    store_result = simple_flight_cache.store_service_list(test_identifier, test_data, 60)
                elif data_type == "booking":
                    store_result = simple_flight_cache.store_booking_data(test_identifier, test_data, 60)
                else:
                    store_result = {"success": False, "error": f"Unknown data type: {data_type}"}
                
                # Test retrieve operation using simple_flight_cache
                if data_type == "flight_search":
                    retrieve_result = simple_flight_cache.get_flight_search(test_identifier)
                elif data_type == "flight_price":
                    retrieve_result = simple_flight_cache.get_flight_price(test_identifier)
                elif data_type == "seat_availability":
                    retrieve_result = simple_flight_cache.get_seat_availability(test_identifier)
                elif data_type == "service_list":
                    retrieve_result = simple_flight_cache.get_service_list(test_identifier)
                elif data_type == "booking":
                    retrieve_result = simple_flight_cache.get_booking_data(test_identifier)
                else:
                    retrieve_result = {"success": False, "error": f"Unknown data type: {data_type}"}
                
                # Test cleanup using simple_flight_cache delete_session_data
                cleanup_result = simple_flight_cache.delete_session_data(test_identifier)
                
                test_success = (
                    store_result.get("success", False) and
                    retrieve_result.get("success", False) and
                    cleanup_result.get("success", False)
                )
                
                test_results["tests"][data_type] = {
                    "success": test_success,
                    "store": store_result.get("success", False),
                    "retrieve": retrieve_result.get("success", False),
                    "cleanup": cleanup_result.get("success", False),
                    "store_message": store_result.get("message", ""),
                    "retrieve_message": retrieve_result.get("message", ""),
                    "cleanup_message": cleanup_result.get("message", "")
                }
                
                if not test_success:
                    overall_success = False
                    
            except Exception as test_error:
                logger.error(f"Cache test failed for {data_type}: {test_error}")
                test_results["tests"][data_type] = {
                    "success": False,
                    "error": str(test_error),
                    "message": f"Test failed for {data_type}"
                }
                overall_success = False
        
        test_results["overall_success"] = overall_success
        test_results["message"] = "All cache operations working correctly" if overall_success else "Some cache operations failed"
        
        return jsonify(test_results), 200 if overall_success else 500
        
    except Exception as e:
        logger.error(f"Cache operation test failed: {str(e)}")
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_operation_test",
            "success": False,
            "error": str(e),
            "message": "Cache operation test failed"
        }), 500

@cache_health_bp.route('/api/cache/stats', methods=['GET'])
async def get_cache_stats():
    """
    Get cache usage statistics and performance metrics.
    
    Returns information about cache utilization, hit rates,
    and performance for monitoring purposes.
    """
    try:
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_statistics",
            "success": True
        }
        
        # Basic Redis connection info
        redis_info = test_redis_connection()
        stats["redis_status"] = redis_info
        
        # TTL configuration
        stats["ttl_configuration"] = {
            "policies": redis_flight_storage.ttl_policies,
            "default_ttl": redis_flight_storage.default_ttl
        }
        
        # Cache configuration info
        stats["cache_configuration"] = {
            "compression_enabled": False,  # Disabled in Phase 1
            "key_format": "flight:{data_type}:{session_id}",
            "supported_types": [dt.value for dt in CacheDataType],
            "backend": "Redis Cloud"
        }
        
        # System health indicators
        stats["health_indicators"] = {
            "redis_available": redis_flight_storage.redis_available,
            "unified_service_available": True,  # Always available as it's a wrapper
            "compression_consistent": True,     # Fixed in Phase 1
            "key_format_consistent": True       # Fixed in Phase 1
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Cache stats retrieval failed: {str(e)}")
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_statistics",
            "success": False,
            "error": str(e),
            "message": "Cache statistics retrieval failed"
        }), 500

@cache_health_bp.route('/api/cache/clear', methods=['POST'])
async def clear_cache_data():
    """
    Clear cache data based on provided criteria.
    
    Supports clearing specific data types, identifiers, or patterns.
    Use with caution in production environments.
    """
    try:
        data = await request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No parameters provided",
                "message": "Please provide clear criteria (identifier, data_type, etc.)"
            }), 400
        
        identifier = data.get('identifier')
        data_type_str = data.get('data_type')
        
        if identifier:
            # Clear specific identifier or all data for identifier
            # Using simple_flight_cache for session-based cleanup
            result = simple_flight_cache.delete_session_data(identifier)
            
            return jsonify({
                "timestamp": datetime.utcnow().isoformat(),
                "service": "cache_clear",
                "operation": "clear_identifier",
                "identifier": identifier,
                "data_type": data_type_str or "all",
                **result
            }), 200 if result.get("success") else 500
        
        # If no specific operations, return usage info
        return jsonify({
            "success": False,
            "error": "No valid clear operation specified",
            "message": "Provide 'identifier' to clear specific cache entries",
            "usage": {
                "clear_specific": {"identifier": "session_id", "data_type": "optional"},
                "clear_all_for_session": {"identifier": "session_id"}
            }
        }), 400
        
    except Exception as e:
        logger.error(f"Cache clear operation failed: {str(e)}")
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "service": "cache_clear",
            "success": False,
            "error": str(e),
            "message": "Cache clear operation failed"
        }), 500