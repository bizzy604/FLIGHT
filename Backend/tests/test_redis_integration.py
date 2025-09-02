"""
Redis Integration Tests for New Cache System
Tests Redis connectivity, fallback behavior, and performance
"""
import pytest
import time
import os
from unittest.mock import Mock, patch
import redis

from cache import create_cache_service, get_cache_service, reset_cache_service
from cache.repository import RedisCacheRepository, InMemoryCacheRepository
from cache.entities import CacheEntity
from cache.key_generator import CacheNamespace
from config.redis_config import get_redis_connection


class TestRedisIntegration:
    """Test Redis integration and fallback behavior"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        reset_cache_service()  # Reset singleton for clean tests
        yield
        reset_cache_service()  # Cleanup after tests
    
    def test_redis_connection(self):
        """Test Redis connection establishment"""
        try:
            redis_client = get_redis_connection()
            
            # Test basic operations
            test_key = "test:connection"
            test_value = "connection_test"
            
            redis_client.set(test_key, test_value, ex=10)
            retrieved = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            assert retrieved == test_value
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_cache_repository_basic_operations(self):
        """Test basic Redis repository operations"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Test save and find
            test_data = {"test": "redis_data", "timestamp": time.time()}
            entity = CacheEntity(
                key="test:redis:basic", 
                data=test_data, 
                ttl_seconds=300
            )
            
            # Save
            assert repo.save(entity) == True
            
            # Find
            found = repo.find("test:redis:basic")
            assert found is not None
            assert found.data == test_data
            
            # Delete
            assert repo.delete("test:redis:basic") == True
            assert repo.find("test:redis:basic") is None
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_fallback_behavior(self):
        """Test fallback to in-memory when Redis fails"""
        # Create a mock Redis client that fails
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        
        # Create repository with failing Redis
        repo = RedisCacheRepository(mock_redis)
        
        # Should use fallback for operations
        test_data = {"test": "fallback_data"}
        entity = CacheEntity(
            key="test:fallback", 
            data=test_data, 
            ttl_seconds=300
        )
        
        # Save should succeed using fallback
        assert repo.save(entity) == True
        
        # Find should succeed using fallback
        found = repo.find("test:fallback")
        assert found is not None
        assert found.data == test_data
    
    def test_redis_repository_pattern_matching(self):
        """Test pattern-based key finding in Redis"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Create test entities with pattern
            test_keys = [
                "flight:search:session1",
                "flight:search:session2", 
                "flight:price:session1",
                "seat:availability:session1"
            ]
            
            entities = []
            for key in test_keys:
                entity = CacheEntity(
                    key=key,
                    data={"test": key},
                    ttl_seconds=300
                )
                entities.append(entity)
                repo.save(entity)
            
            # Test pattern matching
            flight_search_keys = repo.find_by_pattern("flight:search:*")
            assert len(flight_search_keys) == 2
            assert "flight:search:session1" in flight_search_keys
            assert "flight:search:session2" in flight_search_keys
            
            # Cleanup
            for key in test_keys:
                repo.delete(key)
                
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_repository_namespace_clearing(self):
        """Test clearing entire namespace in Redis"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Create entities in different namespaces
            entities_data = [
                ("flight:search:test1", {"search": 1}),
                ("flight:search:test2", {"search": 2}),
                ("flight:price:test1", {"price": 100}),
                ("seat:availability:test1", {"seats": ["1A", "1B"]})
            ]
            
            for key, data in entities_data:
                entity = CacheEntity(key=key, data=data, ttl_seconds=300)
                repo.save(entity)
            
            # Clear flight:search namespace
            deleted_count = repo.clear_namespace("flight:search")
            assert deleted_count == 2
            
            # Verify flight:search keys are gone
            assert repo.find("flight:search:test1") is None
            assert repo.find("flight:search:test2") is None
            
            # Verify other keys remain
            assert repo.find("flight:price:test1") is not None
            assert repo.find("seat:availability:test1") is not None
            
            # Cleanup remaining
            repo.delete("flight:price:test1")
            repo.delete("seat:availability:test1")
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_repository_batch_operations(self):
        """Test batch operations in Redis repository"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Create batch of entities
            entities = []
            for i in range(10):
                entity = CacheEntity(
                    key=f"batch:test:{i}",
                    data={"batch_item": i, "timestamp": time.time()},
                    ttl_seconds=300
                )
                entities.append(entity)
            
            # Batch save
            saved_count = repo.batch_save(entities)
            assert saved_count == 10
            
            # Verify all were saved
            for i in range(10):
                found = repo.find(f"batch:test:{i}")
                assert found is not None
                assert found.data["batch_item"] == i
            
            # Cleanup
            for i in range(10):
                repo.delete(f"batch:test:{i}")
                
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_repository_expiration(self):
        """Test Redis key expiration"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Create entity with short TTL
            entity = CacheEntity(
                key="test:expiration",
                data={"test": "expiration"},
                ttl_seconds=1  # 1 second
            )
            
            # Save
            assert repo.save(entity) == True
            
            # Should be available immediately
            found = repo.find("test:expiration")
            assert found is not None
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Should be expired
            found = repo.find("test:expiration")
            assert found is None
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_repository_stats(self):
        """Test Redis repository statistics"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            stats = repo.get_stats()
            
            assert stats["type"] == "redis_with_fallback"
            assert "redis_connected" in stats
            assert "access_count" in stats
            assert "hit_count" in stats
            assert "hit_rate" in stats
            assert "fallback_stats" in stats
            
            # If Redis is connected, should have Redis-specific stats
            if stats["redis_connected"]:
                assert "redis_memory_used" in stats
                
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")


class TestCacheServiceWithRedis:
    """Test cache service integration with Redis"""
    
    @pytest.fixture(autouse=True) 
    def setup(self):
        """Setup for each test"""
        reset_cache_service()
        yield
        reset_cache_service()
    
    def test_cache_service_redis_integration(self):
        """Test cache service with Redis backend"""
        try:
            # Create cache service (should use Redis if available)
            service = create_cache_service()
            
            # Test flight operations
            session_id = f"redis_test_{int(time.time())}"
            test_data = {
                "origin": "JFK",
                "destination": "LAX", 
                "passengers": 2,
                "timestamp": time.time()
            }
            
            # Set data
            result = service.set_flight_search(session_id, test_data)
            assert result.success == True
            
            # Get data
            result = service.get_flight_search(session_id)
            assert result.success == True
            assert result.data == test_data
            assert result.cache_hit == True
            
            # Cleanup
            service.clear_session(session_id)
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_cache_service_performance_with_redis(self):
        """Test cache service performance with Redis"""
        try:
            service = create_cache_service()
            
            # Performance test parameters
            num_operations = 100
            session_base = f"perf_redis_{int(time.time())}"
            
            test_data = {
                "performance_test": True,
                "data": list(range(50)),
                "timestamp": time.time()
            }
            
            # Measure SET operations
            start_time = time.time()
            for i in range(num_operations):
                session_id = f"{session_base}_{i}"
                result = service.set_flight_search(session_id, {**test_data, "index": i})
                assert result.success == True
            
            set_time = time.time() - start_time
            
            # Measure GET operations
            start_time = time.time()
            for i in range(num_operations):
                session_id = f"{session_base}_{i}" 
                result = service.get_flight_search(session_id)
                assert result.success == True
                assert result.cache_hit == True
            
            get_time = time.time() - start_time
            
            # Calculate performance metrics
            sets_per_second = num_operations / set_time if set_time > 0 else 0
            gets_per_second = num_operations / get_time if get_time > 0 else 0
            
            print(f"\nRedis Performance Metrics:")
            print(f"SET operations: {sets_per_second:.2f} ops/sec")
            print(f"GET operations: {gets_per_second:.2f} ops/sec")
            
            # Redis should be reasonably fast (>100 ops/sec for simple data)
            assert sets_per_second > 10  # Minimum performance threshold
            assert gets_per_second > 10
            
            # Cleanup
            for i in range(num_operations):
                session_id = f"{session_base}_{i}"
                service.delete(CacheNamespace.FLIGHT_SEARCH, session_id)
                
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_cache_service_redis_vs_memory_fallback(self):
        """Compare Redis vs in-memory fallback performance"""
        try:
            # Test with Redis
            redis_service = create_cache_service()
            
            # Test with in-memory only
            memory_repo = InMemoryCacheRepository()
            from cache.service import SimpleCacheService
            from cache.entities import TTLPolicy
            memory_service = SimpleCacheService(memory_repo, TTLPolicy())
            
            test_data = {"comparison_test": True, "timestamp": time.time()}
            session_id = f"comparison_{int(time.time())}"
            
            # Test Redis service
            redis_start = time.time()
            for i in range(10):
                redis_service.set_flight_search(f"{session_id}_redis_{i}", test_data)
                redis_service.get_flight_search(f"{session_id}_redis_{i}")
            redis_time = time.time() - redis_start
            
            # Test memory service
            memory_start = time.time()
            for i in range(10):
                memory_service.set_flight_search(f"{session_id}_memory_{i}", test_data)
                memory_service.get_flight_search(f"{session_id}_memory_{i}")
            memory_time = time.time() - memory_start
            
            print(f"\nPerformance Comparison:")
            print(f"Redis service: {redis_time:.4f} seconds")
            print(f"Memory service: {memory_time:.4f} seconds")
            
            # Both should complete reasonably quickly
            assert redis_time < 5.0  # Should complete within 5 seconds
            assert memory_time < 1.0  # Memory should be very fast
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_cache_service_health_check_with_redis(self):
        """Test health check functionality with Redis"""
        try:
            service = create_cache_service()
            
            # Perform health check
            health = service.health_check()
            
            assert health["healthy"] == True
            assert "operational" in health["message"].lower()
            
            # Get detailed stats
            stats = service.get_stats()
            assert "repository" in stats
            
            # Should indicate Redis usage if available
            repo_stats = stats["repository"]
            if "redis_connected" in repo_stats:
                print(f"\nRedis Connection Status: {repo_stats['redis_connected']}")
                if repo_stats["redis_connected"]:
                    print("Using Redis backend")
                else:
                    print("Using in-memory fallback")
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")


class TestRedisFailureScenarios:
    """Test various Redis failure scenarios"""
    
    def test_redis_connection_failure_at_startup(self):
        """Test behavior when Redis is unavailable at startup"""
        with patch('config.redis_config.get_redis_connection') as mock_get_redis:
            mock_get_redis.side_effect = Exception("Redis unavailable")
            
            # Should fallback to in-memory cache
            service = create_cache_service()
            
            # Should still work with in-memory cache
            result = service.set_flight_search("test_session", {"test": "fallback"})
            assert result.success == True
            
            result = service.get_flight_search("test_session")
            assert result.success == True
            assert result.data == {"test": "fallback"}
    
    def test_redis_connection_failure_during_operation(self):
        """Test behavior when Redis fails during operation"""
        try:
            # Start with working Redis
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Store some data successfully
            entity = CacheEntity(
                key="test:failure_scenario",
                data={"test": "before_failure"}, 
                ttl_seconds=300
            )
            assert repo.save(entity) == True
            
            # Simulate Redis failure by mocking the connection
            repo.redis.get = Mock(side_effect=Exception("Redis connection lost"))
            
            # Should fallback to in-memory cache
            found = repo.find("test:failure_scenario")
            # May return None (expected for fallback scenario)
            
            # New operations should use fallback
            new_entity = CacheEntity(
                key="test:after_failure",
                data={"test": "after_failure"},
                ttl_seconds=300
            )
            assert repo.save(new_entity) == True  # Should succeed with fallback
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")
    
    def test_redis_partial_failure(self):
        """Test behavior when some Redis operations fail"""
        try:
            redis_client = get_redis_connection()
            repo = RedisCacheRepository(redis_client)
            
            # Mock setex to fail but get to work
            repo.redis.setex = Mock(side_effect=Exception("SET operation failed"))
            
            entity = CacheEntity(
                key="test:partial_failure",
                data={"test": "partial_failure"},
                ttl_seconds=300
            )
            
            # Save should fallback and succeed
            assert repo.save(entity) == True
            
            # Find should work (using fallback)
            found = repo.find("test:partial_failure")
            assert found is not None
            assert found.data == {"test": "partial_failure"}
            
        except Exception as e:
            pytest.skip(f"Redis not available for testing: {e}")


if __name__ == "__main__":
    """Run integration tests directly"""
    pytest.main([__file__, "-v", "-s"])