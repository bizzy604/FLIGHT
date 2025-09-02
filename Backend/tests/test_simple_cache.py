"""
Comprehensive tests for the new simplified cache system
Tests all components: key generator, entities, repository, and service
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import new cache system components
from cache.key_generator import CacheKeyGenerator, CacheNamespace
from cache.entities import CacheEntity, TTLPolicy
from cache.repository import InMemoryCacheRepository, RedisCacheRepository
from cache.service import SimpleCacheService, CacheResult
from cache import create_cache_service, get_cache_service, reset_cache_service


class TestCacheKeyGenerator:
    """Test cache key generation"""
    
    def test_generate_simple_key(self):
        """Test basic key generation"""
        key = CacheKeyGenerator.generate_key(CacheNamespace.FLIGHT_SEARCH, "session123")
        assert key == "flight:search:session123"
    
    def test_generate_compound_key(self):
        """Test compound key generation"""
        key = CacheKeyGenerator.generate_compound_key(
            CacheNamespace.SEAT_AVAILABILITY, "session123", "segment1"
        )
        assert key == "seat:availability:session123:segment1"
    
    def test_generate_deterministic_key(self):
        """Test content-based key generation"""
        data1 = {"origin": "NYC", "destination": "LAX", "date": "2024-01-01"}
        data2 = {"date": "2024-01-01", "destination": "LAX", "origin": "NYC"}  # Different order
        
        key1 = CacheKeyGenerator.generate_deterministic_key(data1)
        key2 = CacheKeyGenerator.generate_deterministic_key(data2)
        
        # Should be identical despite different input order
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
    
    def test_parse_key(self):
        """Test key parsing"""
        key = "flight:search:session123"
        parsed = CacheKeyGenerator.parse_key(key)
        
        assert parsed["namespace"] == "flight:search"
        assert parsed["identifier"] == "session123"
        assert parsed["full_key"] == key
    
    def test_session_id_generation(self):
        """Test session ID generation"""
        session_id = CacheKeyGenerator.generate_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID4 length
        assert session_id.count("-") == 4  # UUID4 format


class TestCacheEntity:
    """Test cache entity model"""
    
    def test_entity_creation(self):
        """Test basic entity creation"""
        data = {"test": "data"}
        entity = CacheEntity(key="test:key", data=data, ttl_seconds=300)
        
        assert entity.key == "test:key"
        assert entity.data == data
        assert entity.ttl_seconds == 300
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.expires_at, datetime)
    
    def test_entity_expiration(self):
        """Test entity expiration logic"""
        # Create entity that expires in 1 second
        entity = CacheEntity(key="test:key", data={"test": True}, ttl_seconds=1)
        
        assert not entity.is_expired()
        
        # Wait and check expiration
        time.sleep(1.1)
        assert entity.is_expired()
    
    def test_entity_serialization(self):
        """Test entity serialization/deserialization"""
        data = {"flight": "data", "number": 123}
        entity = CacheEntity(key="flight:123", data=data, ttl_seconds=600)
        
        # Serialize
        serialized = entity.serialize()
        assert isinstance(serialized, str)
        
        # Deserialize
        deserialized = CacheEntity.deserialize("flight:123", serialized)
        assert deserialized.key == entity.key
        assert deserialized.data == entity.data
        assert deserialized.ttl_seconds == entity.ttl_seconds
    
    def test_storage_dict_conversion(self):
        """Test conversion to/from storage dictionary"""
        data = {"test": "data"}
        entity = CacheEntity(key="test:key", data=data, ttl_seconds=300)
        
        # Convert to dict
        storage_dict = entity.to_storage_dict()
        assert "data" in storage_dict
        assert "created_at" in storage_dict
        assert "expires_at" in storage_dict
        
        # Convert back
        restored = CacheEntity.from_storage_dict("test:key", storage_dict)
        assert restored.key == entity.key
        assert restored.data == entity.data


class TestTTLPolicy:
    """Test TTL policy management"""
    
    def test_default_policies(self):
        """Test default TTL policies"""
        policy = TTLPolicy()
        
        assert policy.get_ttl("flight:search") == 1800  # 30 minutes
        assert policy.get_ttl("flight:price") == 1800
        assert policy.get_ttl("seat:availability") == 900  # 15 minutes
        assert policy.get_ttl("booking") == 3600  # 60 minutes
    
    def test_custom_policies(self):
        """Test custom TTL policies"""
        custom = {"custom:namespace": 1200}
        policy = TTLPolicy(custom)
        
        assert policy.get_ttl("custom:namespace") == 1200
        assert policy.get_ttl("flight:search") == 1800  # Default still works
    
    def test_set_ttl(self):
        """Test setting TTL dynamically"""
        policy = TTLPolicy()
        policy.set_ttl("new:namespace", 2400)
        
        assert policy.get_ttl("new:namespace") == 2400
    
    def test_unknown_namespace_default(self):
        """Test default TTL for unknown namespace"""
        policy = TTLPolicy()
        assert policy.get_ttl("unknown:namespace") == 900  # Default


class TestInMemoryCacheRepository:
    """Test in-memory cache repository"""
    
    def test_save_and_find(self):
        """Test basic save and find operations"""
        repo = InMemoryCacheRepository()
        entity = CacheEntity(key="test:key", data={"test": True}, ttl_seconds=300)
        
        # Save
        assert repo.save(entity) == True
        
        # Find
        found = repo.find("test:key")
        assert found is not None
        assert found.key == "test:key"
        assert found.data == {"test": True}
    
    def test_expired_entity_cleanup(self):
        """Test that expired entities are cleaned up"""
        repo = InMemoryCacheRepository()
        entity = CacheEntity(key="test:key", data={"test": True}, ttl_seconds=1)
        
        repo.save(entity)
        
        # Should find immediately
        assert repo.find("test:key") is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should not find expired entity
        assert repo.find("test:key") is None
    
    def test_delete(self):
        """Test delete operation"""
        repo = InMemoryCacheRepository()
        entity = CacheEntity(key="test:key", data={"test": True}, ttl_seconds=300)
        
        repo.save(entity)
        assert repo.find("test:key") is not None
        
        assert repo.delete("test:key") == True
        assert repo.find("test:key") is None
    
    def test_exists(self):
        """Test exists check"""
        repo = InMemoryCacheRepository()
        entity = CacheEntity(key="test:key", data={"test": True}, ttl_seconds=300)
        
        assert repo.exists("test:key") == False
        
        repo.save(entity)
        assert repo.exists("test:key") == True
        
        repo.delete("test:key")
        assert repo.exists("test:key") == False
    
    def test_find_by_pattern(self):
        """Test pattern-based key finding"""
        repo = InMemoryCacheRepository()
        
        # Save some test entities
        entities = [
            CacheEntity(key="flight:search:123", data={"test": 1}, ttl_seconds=300),
            CacheEntity(key="flight:search:456", data={"test": 2}, ttl_seconds=300),
            CacheEntity(key="seat:availability:123", data={"test": 3}, ttl_seconds=300),
        ]
        
        for entity in entities:
            repo.save(entity)
        
        # Find flight search keys
        flight_keys = repo.find_by_pattern("flight:search:*")
        assert len(flight_keys) == 2
        assert "flight:search:123" in flight_keys
        assert "flight:search:456" in flight_keys
    
    def test_clear_namespace(self):
        """Test namespace clearing"""
        repo = InMemoryCacheRepository()
        
        # Save entities in different namespaces
        entities = [
            CacheEntity(key="flight:search:123", data={"test": 1}, ttl_seconds=300),
            CacheEntity(key="flight:search:456", data={"test": 2}, ttl_seconds=300),
            CacheEntity(key="seat:availability:123", data={"test": 3}, ttl_seconds=300),
        ]
        
        for entity in entities:
            repo.save(entity)
        
        # Clear flight namespace
        deleted = repo.clear_namespace("flight:search")
        assert deleted == 2
        
        # Verify only flight keys were deleted
        assert repo.find("flight:search:123") is None
        assert repo.find("flight:search:456") is None
        assert repo.find("seat:availability:123") is not None
    
    def test_get_stats(self):
        """Test repository statistics"""
        repo = InMemoryCacheRepository()
        
        # Initial stats
        stats = repo.get_stats()
        assert stats["type"] == "in_memory"
        assert stats["total_keys"] == 0
        assert stats["access_count"] == 0
        
        # Add some data and access it
        entity = CacheEntity(key="test:key", data={"test": True}, ttl_seconds=300)
        repo.save(entity)
        repo.find("test:key")  # This should increment access count
        
        stats = repo.get_stats()
        assert stats["total_keys"] == 1
        assert stats["access_count"] == 1
        assert stats["hit_count"] == 1


class TestSimpleCacheService:
    """Test the main cache service"""
    
    def setup_method(self):
        """Setup for each test"""
        self.repo = InMemoryCacheRepository()
        self.service = SimpleCacheService(self.repo)
    
    def test_basic_set_get(self):
        """Test basic set and get operations"""
        # Set data
        result = self.service.set(CacheNamespace.FLIGHT_SEARCH, "session123", {"test": "data"})
        assert result.success == True
        assert result.key == "flight:search:session123"
        
        # Get data
        result = self.service.get(CacheNamespace.FLIGHT_SEARCH, "session123")
        assert result.success == True
        assert result.data == {"test": "data"}
        assert result.cache_hit == True
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent key"""
        result = self.service.get(CacheNamespace.FLIGHT_SEARCH, "nonexistent")
        assert result.success == False
        assert result.cache_hit == False
        assert "not found" in result.error.lower()
    
    def test_delete_operation(self):
        """Test delete operation"""
        # Set then delete
        self.service.set(CacheNamespace.FLIGHT_SEARCH, "session123", {"test": "data"})
        
        result = self.service.delete(CacheNamespace.FLIGHT_SEARCH, "session123")
        assert result.success == True
        
        # Verify deleted
        result = self.service.get(CacheNamespace.FLIGHT_SEARCH, "session123")
        assert result.success == False
    
    def test_exists_operation(self):
        """Test exists check"""
        assert self.service.exists(CacheNamespace.FLIGHT_SEARCH, "session123") == False
        
        self.service.set(CacheNamespace.FLIGHT_SEARCH, "session123", {"test": "data"})
        assert self.service.exists(CacheNamespace.FLIGHT_SEARCH, "session123") == True
    
    def test_convenience_methods(self):
        """Test flight-specific convenience methods"""
        # Test flight search
        result = self.service.set_flight_search("session123", {"flights": []})
        assert result.success == True
        
        result = self.service.get_flight_search("session123")
        assert result.success == True
        assert result.data == {"flights": []}
        
        # Test flight price
        result = self.service.set_flight_price("session123", {"price": 500})
        assert result.success == True
        
        result = self.service.get_flight_price("session123")
        assert result.success == True
        assert result.data == {"price": 500}
    
    def test_content_based_caching(self):
        """Test content-based key generation"""
        data = {"origin": "NYC", "dest": "LAX"}
        
        # Store by content
        result = self.service.set_by_content(CacheNamespace.FLIGHT_SEARCH, data)
        assert result.success == True
        
        # Retrieve by content (same data should generate same key)
        result = self.service.get_by_content(CacheNamespace.FLIGHT_SEARCH, data)
        assert result.success == True
        assert result.data == data
    
    def test_batch_operations(self):
        """Test batch set operations"""
        operations = [
            {
                "namespace": "flight:search",
                "identifier": "session1",
                "data": {"flight": 1}
            },
            {
                "namespace": "flight:search", 
                "identifier": "session2",
                "data": {"flight": 2}
            },
            {
                "namespace": "flight:price",
                "identifier": "session1", 
                "data": {"price": 100}
            }
        ]
        
        result = self.service.batch_set(operations)
        assert result["success"] == True
        assert result["successful"] == 3
        assert result["failed"] == 0
        
        # Verify data was stored
        assert self.service.get_flight_search("session1").success == True
        assert self.service.get_flight_search("session2").success == True
        assert self.service.get_flight_price("session1").success == True
    
    def test_clear_session(self):
        """Test clearing all data for a session"""
        session_id = "test_session"
        
        # Store data in multiple namespaces
        self.service.set_flight_search(session_id, {"search": True})
        self.service.set_flight_price(session_id, {"price": True})
        self.service.set_seat_availability(session_id, {"seats": True})
        
        # Clear session
        deleted = self.service.clear_session(session_id)
        assert deleted > 0
        
        # Verify all data cleared
        assert self.service.get_flight_search(session_id).success == False
        assert self.service.get_flight_price(session_id).success == False
        assert self.service.get_seat_availability(session_id).success == False
    
    def test_clear_namespace(self):
        """Test clearing entire namespace"""
        # Store data in flight search namespace
        self.service.set_flight_search("session1", {"test": 1})
        self.service.set_flight_search("session2", {"test": 2})
        self.service.set_flight_price("session1", {"price": 100})
        
        # Clear flight search namespace
        deleted = self.service.clear_namespace(CacheNamespace.FLIGHT_SEARCH)
        assert deleted == 2
        
        # Verify flight search data cleared but price data remains
        assert self.service.get_flight_search("session1").success == False
        assert self.service.get_flight_search("session2").success == False
        assert self.service.get_flight_price("session1").success == True
    
    def test_health_check(self):
        """Test health check functionality"""
        health = self.service.health_check()
        assert health["healthy"] == True
        assert "operational" in health["message"].lower()
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        stats = self.service.get_stats()
        assert "cache_service" in stats
        assert "repository" in stats
        assert "ttl_policies" in stats
        assert stats["cache_service"] == "SimpleCacheService"


class TestCacheFactory:
    """Test cache factory functions"""
    
    def test_create_cache_service(self):
        """Test cache service creation"""
        service = create_cache_service()
        assert isinstance(service, SimpleCacheService)
    
    def test_get_cache_service_singleton(self):
        """Test singleton pattern"""
        reset_cache_service()  # Reset for clean test
        
        service1 = get_cache_service()
        service2 = get_cache_service()
        
        assert service1 is service2  # Should be same instance
    
    def test_custom_ttl_policies(self):
        """Test custom TTL policies"""
        custom_policies = {"custom:test": 1234}
        service = create_cache_service(custom_policies)
        
        # Access the TTL policy through the service
        assert hasattr(service, 'ttl_policy')
        assert service.ttl_policy.get_ttl("custom:test") == 1234


if __name__ == "__main__":
    """Run tests directly"""
    pytest.main([__file__, "-v"])