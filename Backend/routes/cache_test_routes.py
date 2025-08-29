"""
Test Routes for New Cache System
Live testing endpoints to verify the new cache system works correctly
"""
from quart import Blueprint, request, jsonify
import logging
from datetime import datetime
import uuid

from services.simple_flight_cache import simple_flight_cache

logger = logging.getLogger(__name__)

# Create blueprint for cache testing
cache_test_bp = Blueprint('cache_test', __name__, url_prefix='/api/cache-test')


@cache_test_bp.route('/health', methods=['GET'])
async def cache_health():
    """Test cache system health"""
    try:
        # Test the simple flight cache
        health = simple_flight_cache.get_cache_health()
        
        return jsonify({
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "flight_cache_health": health,
            "message": "Cache system health check completed"
        }), 200
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Cache health check failed"
        }), 500


@cache_test_bp.route('/basic-operations', methods=['POST'])
async def test_basic_operations():
    """Test basic cache operations (set, get, delete)"""
    try:
        test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        test_data = {
            "test_value": "Hello Cache!",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": test_session_id
        }
        
        results = {}
        
        # Test SET operation
        logger.info(f"Testing SET operation with session: {test_session_id}")
        set_result = simple_flight_cache.store_flight_search(test_session_id, test_data)
        results["set_operation"] = set_result
        
        if not set_result["success"]:
            raise Exception(f"SET failed: {set_result.get('error')}")
        
        # Test GET operation
        logger.info(f"Testing GET operation with session: {test_session_id}")
        get_result = simple_flight_cache.get_flight_search(test_session_id)
        results["get_operation"] = get_result
        
        if not get_result["success"]:
            raise Exception(f"GET failed: {get_result.get('error')}")
        
        # Verify data integrity
        if get_result["data"] != test_data:
            raise Exception("Data integrity check failed - retrieved data doesn't match stored data")
        
        # Test DELETE operation
        logger.info(f"Testing DELETE operation with session: {test_session_id}")
        delete_result = simple_flight_cache.delete_session_data(test_session_id)
        results["delete_operation"] = delete_result
        
        # Verify deletion
        get_after_delete = simple_flight_cache.get_flight_search(test_session_id)
        results["get_after_delete"] = get_after_delete
        
        if get_after_delete["success"]:
            raise Exception("DELETE verification failed - data still exists after deletion")
        
        return jsonify({
            "status": "success",
            "message": "All basic operations completed successfully",
            "test_session_id": test_session_id,
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Basic operations test failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Basic operations test failed"
        }), 500


@cache_test_bp.route('/flight-operations', methods=['POST'])
async def test_flight_operations():
    """Test all flight-specific cache operations"""
    try:
        test_session_id = f"flight_test_{uuid.uuid4().hex[:8]}"
        
        # Test data for different flight operations
        test_data = {
            "search": {
                "origin": "JFK",
                "destination": "LAX", 
                "departure": "2024-03-15",
                "passengers": 2,
                "offers": ["offer1", "offer2", "offer3"]
            },
            "price": {
                "offer_id": "offer1",
                "total_price": 599.99,
                "currency": "USD",
                "breakdown": {"base": 499.99, "taxes": 100.00}
            },
            "seats": {
                "available_seats": ["1A", "1B", "2A", "2B"],
                "seat_map": {"1A": "window", "1B": "aisle"}
            },
            "services": {
                "meals": ["vegetarian", "standard"],
                "baggage": {"carry_on": True, "checked": False},
                "extras": ["wifi", "entertainment"]
            },
            "booking": {
                "booking_ref": "ABC123",
                "passenger_names": ["John Doe", "Jane Doe"],
                "status": "confirmed"
            }
        }
        
        results = {}
        
        # Test Flight Search operations
        logger.info("Testing flight search cache operations")
        search_set = simple_flight_cache.store_flight_search(test_session_id, test_data["search"])
        search_get = simple_flight_cache.get_flight_search(test_session_id)
        results["flight_search"] = {"set": search_set, "get": search_get}
        
        # Test Flight Price operations
        logger.info("Testing flight price cache operations")
        price_set = simple_flight_cache.store_flight_price(test_session_id, test_data["price"])
        price_get = simple_flight_cache.get_flight_price(test_session_id)
        results["flight_price"] = {"set": price_set, "get": price_get}
        
        # Test Seat Availability operations
        logger.info("Testing seat availability cache operations")
        seat_set = simple_flight_cache.store_seat_availability(test_session_id, test_data["seats"])
        seat_get = simple_flight_cache.get_seat_availability(test_session_id)
        results["seat_availability"] = {"set": seat_set, "get": seat_get}
        
        # Test Service List operations
        logger.info("Testing service list cache operations")
        service_set = simple_flight_cache.store_service_list(test_session_id, test_data["services"])
        service_get = simple_flight_cache.get_service_list(test_session_id)
        results["service_list"] = {"set": service_set, "get": service_get}
        
        # Test Booking operations
        logger.info("Testing booking cache operations")
        booking_set = simple_flight_cache.store_booking_data(test_session_id, test_data["booking"])
        booking_get = simple_flight_cache.get_booking_data(test_session_id)
        results["booking"] = {"set": booking_set, "get": booking_get}
        
        # Verify all operations succeeded
        failed_operations = []
        for operation, result in results.items():
            if not result["set"]["success"] or not result["get"]["success"]:
                failed_operations.append(operation)
        
        if failed_operations:
            raise Exception(f"Operations failed: {', '.join(failed_operations)}")
        
        # Test session cleanup
        logger.info("Testing session cleanup")
        cleanup_result = simple_flight_cache.delete_session_data(test_session_id)
        results["cleanup"] = cleanup_result
        
        return jsonify({
            "status": "success",
            "message": "All flight operations completed successfully",
            "test_session_id": test_session_id,
            "results": results,
            "operations_tested": list(test_data.keys())
        }), 200
        
    except Exception as e:
        logger.error(f"Flight operations test failed: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "message": "Flight operations test failed"
        }), 500


@cache_test_bp.route('/performance-test', methods=['POST'])
async def test_performance():
    """Test cache performance with multiple operations"""
    try:
        data = await request.get_json()
        num_operations = data.get('num_operations', 100)
        
        import time
        start_time = time.time()
        
        cache_service = simple_flight_cache # Assuming simple_flight_cache is the primary cache service
        session_base = f"perf_test_{uuid.uuid4().hex[:8]}"
        
        # Performance metrics
        metrics = {
            "operations": num_operations,
            "successful_sets": 0,
            "successful_gets": 0,
            "cache_hits": 0,
            "errors": 0
        }
        
        # Test data
        test_data = {
            "performance_test": True,
            "data": list(range(100)),  # Some data to cache
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # SET operations
        logger.info(f"Starting {num_operations} SET operations")
        set_start = time.time()
        for i in range(num_operations):
            try:
                session_id = f"{session_base}_{i}"
                result = cache_service.store_flight_search(session_id, {**test_data, "index": i})
                if result.success:
                    metrics["successful_sets"] += 1
                else:
                    metrics["errors"] += 1
            except Exception as e:
                metrics["errors"] += 1
                logger.warning(f"SET operation {i} failed: {e}")
        
        set_time = time.time() - set_start
        
        # GET operations
        logger.info(f"Starting {num_operations} GET operations")
        get_start = time.time()
        for i in range(num_operations):
            try:
                session_id = f"{session_base}_{i}"
                result = cache_service.get_flight_search(session_id)
                if result.success:
                    metrics["successful_gets"] += 1
                    if result.cache_hit:
                        metrics["cache_hits"] += 1
                else:
                    metrics["errors"] += 1
            except Exception as e:
                metrics["errors"] += 1
                logger.warning(f"GET operation {i} failed: {e}")
        
        get_time = time.time() - get_start
        total_time = time.time() - start_time
        
        # Cleanup test data
        logger.info("Cleaning up performance test data")
        cleanup_count = 0
        for i in range(num_operations):
            try:
                session_id = f"{session_base}_{i}"
                if cache_service.delete_session_data(session_id).success:
                    cleanup_count += 1
            except:
                pass
        
        # Calculate performance metrics
        metrics.update({
            "total_time_seconds": round(total_time, 3),
            "set_time_seconds": round(set_time, 3),
            "get_time_seconds": round(get_time, 3),
            "sets_per_second": round(metrics["successful_sets"] / set_time if set_time > 0 else 0, 2),
            "gets_per_second": round(metrics["successful_gets"] / get_time if get_time > 0 else 0, 2),
            "cache_hit_rate": round(metrics["cache_hits"] / max(metrics["successful_gets"], 1) * 100, 2),
            "error_rate": round(metrics["errors"] / (num_operations * 2) * 100, 2),
            "cleaned_up": cleanup_count
        })
        
        return jsonify({
            "status": "success",
            "message": f"Performance test completed with {num_operations} operations",
            "metrics": metrics,
            "cache_stats": cache_service.get_stats()
        }), 200
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Performance test failed"
        }), 500


@cache_test_bp.route('/redis-fallback-test', methods=['POST'])
async def test_redis_fallback():
    """Test Redis fallback to in-memory cache"""
    try:
        cache_service = simple_flight_cache # Assuming simple_flight_cache is the primary cache service
        test_session_id = f"fallback_test_{uuid.uuid4().hex[:8]}"
        test_data = {"fallback_test": True, "timestamp": datetime.utcnow().isoformat()}
        
        results = {}
        
        # Test normal operation
        logger.info("Testing normal cache operation")
        set_result = cache_service.store_flight_search(test_session_id, test_data)
        get_result = cache_service.get_flight_search(test_session_id)
        
        results["normal_operation"] = {
            "set": set_result.to_dict(),
            "get": get_result.to_dict()
        }
        
        # Get repository stats to see if using Redis or memory
        stats = cache_service.get_stats()
        results["cache_stats"] = stats
        
        # Determine cache type
        if "redis_connected" in stats.get("repository", {}):
            cache_type = "Redis" if stats["repository"]["redis_connected"] else "In-Memory Fallback"
        else:
            cache_type = stats.get("repository", {}).get("type", "Unknown")
        
        results["cache_type"] = cache_type
        
        # Test health
        health = cache_service.get_cache_health()
        results["health"] = health
        
        # Cleanup
        cache_service.delete_session_data(test_session_id)
        
        return jsonify({
            "status": "success",
            "message": "Redis fallback test completed",
            "cache_type_detected": cache_type,
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Redis fallback test failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Redis fallback test failed"
        }), 500


@cache_test_bp.route('/comparison-test', methods=['POST'])
async def test_old_vs_new_cache():
    """Compare old cache system vs new cache system (if both available)"""
    try:
        results = {"new_cache": {}, "old_cache": {}, "comparison": {}}
        
        test_session_id = f"comparison_test_{uuid.uuid4().hex[:8]}"
        test_data = {
            "comparison_test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": list(range(50))  # Some test data
        }
        
        import time
        
        # Test NEW cache system
        logger.info("Testing NEW cache system")
        new_start = time.time()
        
        try:
            # Test new cache operations
            new_set = simple_flight_cache.store_flight_search(test_session_id, test_data)
            new_get = simple_flight_cache.get_flight_search(test_session_id)
            new_health = simple_flight_cache.get_cache_health()
            
            new_time = time.time() - new_start
            
            results["new_cache"] = {
                "available": True,
                "set_success": new_set["success"],
                "get_success": new_get["success"],
                "health": new_health["success"],
                "response_time": round(new_time * 1000, 2),  # milliseconds
                "cache_hit": new_get.get("cache_hit", False)
            }
            
            # Cleanup new cache
            simple_flight_cache.delete_session_data(test_session_id)
            
        except Exception as e:
            results["new_cache"] = {
                "available": False,
                "error": str(e)
            }
        
        # Test OLD cache system (if available)
        logger.info("Testing OLD cache system")
        old_start = time.time()
        
        try:
            from services.unified_cache_service import unified_cache_service
            from services.redis_flight_storage import redis_flight_storage
            
            # Test old cache operations
            old_set = redis_flight_storage.store_flight_search(test_data, test_session_id)
            old_get = redis_flight_storage.get_flight_search(test_session_id)
            
            old_time = time.time() - old_start
            
            results["old_cache"] = {
                "available": True,
                "set_success": old_set.get("success", False),
                "get_success": old_get.get("success", False),
                "response_time": round(old_time * 1000, 2),  # milliseconds
                "redis_available": redis_flight_storage.redis_available
            }
            
            # Cleanup old cache
            try:
                redis_flight_storage.delete_session_data(test_session_id)
            except:
                pass
                
        except ImportError:
            results["old_cache"] = {
                "available": False,
                "error": "Old cache system not available (expected for clean installation)"
            }
        except Exception as e:
            results["old_cache"] = {
                "available": False,
                "error": str(e)
            }
        
        # Generate comparison if both systems are available
        if results["new_cache"].get("available") and results["old_cache"].get("available"):
            new_time = results["new_cache"]["response_time"]
            old_time = results["old_cache"]["response_time"]
            
            results["comparison"] = {
                "performance_improvement": round(((old_time - new_time) / old_time) * 100, 2) if old_time > 0 else 0,
                "new_faster": new_time < old_time,
                "time_difference_ms": round(old_time - new_time, 2)
            }
        
        return jsonify({
            "status": "success",
            "message": "Cache system comparison completed",
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Cache comparison test failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Cache comparison test failed"
        }), 500


# Add route to get all available test endpoints
@cache_test_bp.route('/endpoints', methods=['GET'])
async def get_test_endpoints():
    """Get list of all available test endpoints"""
    endpoints = {
        "health": {
            "method": "GET",
            "url": "/api/cache-test/health",
            "description": "Check cache system health and get statistics"
        },
        "basic_operations": {
            "method": "POST", 
            "url": "/api/cache-test/basic-operations",
            "description": "Test basic cache operations (set, get, delete)"
        },
        "flight_operations": {
            "method": "POST",
            "url": "/api/cache-test/flight-operations", 
            "description": "Test all flight-specific cache operations"
        },
        "performance_test": {
            "method": "POST",
            "url": "/api/cache-test/performance-test",
            "description": "Performance test with configurable number of operations",
            "body": {"num_operations": 100}
        },
        "redis_fallback_test": {
            "method": "POST",
            "url": "/api/cache-test/redis-fallback-test",
            "description": "Test Redis fallback to in-memory cache"
        },
        "comparison_test": {
            "method": "POST",
            "url": "/api/cache-test/comparison-test",
            "description": "Compare old vs new cache system performance"
        }
    }
    
    return jsonify({
        "status": "success",
        "message": "Available cache test endpoints",
        "endpoints": endpoints,
        "base_url": "/api/cache-test"
    }), 200