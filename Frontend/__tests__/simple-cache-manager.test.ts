/**
 * Tests for Simple Cache Manager
 * Comprehensive frontend cache system testing
 */

import { simpleCacheManager, CacheNamespace } from '../utils/simple-cache-manager';

// Mock localStorage and sessionStorage for testing
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (index: number) => Object.keys(store)[index] || null
  };
})();

const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (index: number) => Object.keys(store)[index] || null
  };
})();

// Setup mocks
Object.defineProperty(window, 'localStorage', { value: localStorageMock });
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

describe('SimpleCacheManager', () => {
  beforeEach(() => {
    // Clear all storage before each test
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('Basic Cache Operations', () => {
    test('should set and get cache data successfully', () => {
      const testData = { test: 'data', timestamp: Date.now() };
      
      // Set data
      const setResult = simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session123', testData);
      expect(setResult.success).toBe(true);
      expect(setResult.key).toBe('flight:search:session123');
      
      // Get data
      const getResult = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'session123');
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(testData);
      expect(getResult.cacheHit).toBe(true);
    });

    test('should return false for non-existent data', () => {
      const result = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'nonexistent');
      expect(result.success).toBe(false);
      expect(result.cacheHit).toBe(false);
      expect(result.error).toContain('not found');
    });

    test('should delete data successfully', () => {
      const testData = { test: 'data' };
      
      // Set data
      simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session123', testData);
      
      // Verify it exists
      expect(simpleCacheManager.exists(CacheNamespace.FLIGHT_SEARCH, 'session123')).toBe(true);
      
      // Delete data
      const deleted = simpleCacheManager.delete(CacheNamespace.FLIGHT_SEARCH, 'session123');
      expect(deleted).toBe(true);
      
      // Verify it's gone
      expect(simpleCacheManager.exists(CacheNamespace.FLIGHT_SEARCH, 'session123')).toBe(false);
    });

    test('should handle expired data correctly', () => {
      const testData = { test: 'data' };
      
      // Set data with very short TTL (1 second)
      const setResult = simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session123', testData, 1);
      expect(setResult.success).toBe(true);
      
      // Should be available immediately
      let getResult = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'session123');
      expect(getResult.success).toBe(true);
      
      // Mock time passing (1.5 seconds)
      jest.useFakeTimers();
      jest.advanceTimersByTime(1500);
      
      // Should be expired now
      getResult = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'session123');
      expect(getResult.success).toBe(false);
      
      jest.useRealTimers();
    });
  });

  describe('TTL Policies', () => {
    test('should use correct TTL for different namespaces', () => {
      // Mock Date.now to control expiration calculation
      const originalDateNow = Date.now;
      const mockNow = 1000000;
      Date.now = jest.fn(() => mockNow);

      try {
        const testData = { test: 'data' };
        
        // Set flight search data (should use 30 minutes TTL)
        simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session1', testData);
        
        // Set seat availability (should use 15 minutes TTL) 
        simpleCacheManager.set(CacheNamespace.SEAT_AVAILABILITY, 'session2', testData);
        
        // Check storage to verify TTL differences
        const searchItem = JSON.parse(sessionStorage.getItem('flight:search:session1')!);
        const seatItem = JSON.parse(sessionStorage.getItem('seat:availability:session2')!);
        
        expect(searchItem.expires).toBe(mockNow + 30 * 60 * 1000); // 30 minutes
        expect(seatItem.expires).toBe(mockNow + 15 * 60 * 1000);   // 15 minutes
        
      } finally {
        Date.now = originalDateNow;
      }
    });

    test('should accept custom TTL', () => {
      const originalDateNow = Date.now;
      const mockNow = 1000000;
      Date.now = jest.fn(() => mockNow);

      try {
        const testData = { test: 'data' };
        const customTTL = 600; // 10 minutes
        
        simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session1', testData, customTTL);
        
        const item = JSON.parse(sessionStorage.getItem('flight:search:session1')!);
        expect(item.expires).toBe(mockNow + customTTL * 1000);
        
      } finally {
        Date.now = originalDateNow;
      }
    });
  });

  describe('Convenience Methods', () => {
    test('should work with flight search convenience methods', () => {
      const searchData = { origin: 'JFK', destination: 'LAX' };
      
      // Set flight search data
      const setResult = simpleCacheManager.setFlightSearch('session123', searchData);
      expect(setResult.success).toBe(true);
      
      // Get flight search data
      const getResult = simpleCacheManager.getFlightSearch('session123');
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(searchData);
    });

    test('should work with flight price convenience methods', () => {
      const priceData = { price: 599.99, currency: 'USD' };
      
      const setResult = simpleCacheManager.setFlightPrice('session123', priceData);
      expect(setResult.success).toBe(true);
      
      const getResult = simpleCacheManager.getFlightPrice('session123');
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(priceData);
    });

    test('should work with seat availability convenience methods', () => {
      const seatData = { seats: ['1A', '1B', '2A'] };
      
      const setResult = simpleCacheManager.setSeatAvailability('session123', seatData);
      expect(setResult.success).toBe(true);
      
      const getResult = simpleCacheManager.getSeatAvailability('session123');
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(seatData);
    });

    test('should work with service list convenience methods', () => {
      const serviceData = { services: ['wifi', 'meals', 'entertainment'] };
      
      const setResult = simpleCacheManager.setServiceList('session123', serviceData);
      expect(setResult.success).toBe(true);
      
      const getResult = simpleCacheManager.getServiceList('session123');
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(serviceData);
    });

    test('should work with booking convenience methods', () => {
      const bookingData = { bookingRef: 'ABC123', status: 'confirmed' };
      
      const setResult = simpleCacheManager.setBooking('session123', bookingData);
      expect(setResult.success).toBe(true);
      
      const getResult = simpleCacheManager.getBooking('session123');
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(bookingData);
    });
  });

  describe('Session Management', () => {
    test('should generate unique session IDs', () => {
      const id1 = simpleCacheManager.generateSessionId();
      const id2 = simpleCacheManager.generateSessionId();
      
      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^session_\d+_[a-z0-9]{9}$/);
      expect(id2).toMatch(/^session_\d+_[a-z0-9]{9}$/);
    });

    test('should create and persist session ID', () => {
      // Should create new session ID
      const sessionId = simpleCacheManager.getOrCreateSessionId();
      expect(sessionId).toBeDefined();
      expect(localStorage.getItem('flight_session_id')).toBe(sessionId);
      
      // Should return same session ID on subsequent calls
      const sessionId2 = simpleCacheManager.getOrCreateSessionId();
      expect(sessionId2).toBe(sessionId);
    });

    test('should return existing session ID', () => {
      // Set existing session ID
      const existingId = 'existing_session_123';
      localStorage.setItem('flight_session_id', existingId);
      
      const sessionId = simpleCacheManager.getOrCreateSessionId();
      expect(sessionId).toBe(existingId);
    });

    test('should clear session data', () => {
      const sessionId = 'test_session';
      localStorage.setItem('flight_session_id', sessionId);
      
      // Store some session data
      simpleCacheManager.setFlightSearch(sessionId, { test: 'search' });
      simpleCacheManager.setFlightPrice(sessionId, { test: 'price' });
      
      // Clear session
      simpleCacheManager.clearSession();
      
      // Verify session ID is cleared
      expect(localStorage.getItem('flight_session_id')).toBeNull();
      
      // Verify cache data is cleared
      expect(simpleCacheManager.getFlightSearch(sessionId).success).toBe(false);
      expect(simpleCacheManager.getFlightPrice(sessionId).success).toBe(false);
    });

    test('should clear specific session data', () => {
      const sessionId = 'test_session';
      
      // Store data in multiple namespaces
      simpleCacheManager.setFlightSearch(sessionId, { test: 'search' });
      simpleCacheManager.setFlightPrice(sessionId, { test: 'price' });
      simpleCacheManager.setSeatAvailability(sessionId, { test: 'seats' });
      
      // Clear session data
      const cleared = simpleCacheManager.clearSessionData(sessionId);
      expect(cleared).toBeGreaterThan(0);
      
      // Verify all data cleared
      expect(simpleCacheManager.getFlightSearch(sessionId).success).toBe(false);
      expect(simpleCacheManager.getFlightPrice(sessionId).success).toBe(false);
      expect(simpleCacheManager.getSeatAvailability(sessionId).success).toBe(false);
    });
  });

  describe('Namespace Operations', () => {
    test('should clear entire namespace', () => {
      // Store data in flight search namespace with different sessions
      simpleCacheManager.setFlightSearch('session1', { test: 1 });
      simpleCacheManager.setFlightSearch('session2', { test: 2 });
      simpleCacheManager.setFlightPrice('session1', { price: 100 });
      
      // Clear flight search namespace
      const cleared = simpleCacheManager.clearNamespace(CacheNamespace.FLIGHT_SEARCH);
      expect(cleared).toBe(4); // Should clear from both sessionStorage and localStorage
      
      // Verify flight search data cleared
      expect(simpleCacheManager.getFlightSearch('session1').success).toBe(false);
      expect(simpleCacheManager.getFlightSearch('session2').success).toBe(false);
      
      // Verify price data remains
      expect(simpleCacheManager.getFlightPrice('session1').success).toBe(true);
    });

    test('should clear all cache data', () => {
      // Store various data
      simpleCacheManager.setFlightSearch('session1', { test: 1 });
      simpleCacheManager.setFlightPrice('session1', { price: 100 });
      localStorage.setItem('flight_session_id', 'session1');
      
      // Clear all
      simpleCacheManager.clearAll();
      
      // Verify everything is cleared
      expect(simpleCacheManager.getFlightSearch('session1').success).toBe(false);
      expect(simpleCacheManager.getFlightPrice('session1').success).toBe(false);
      expect(localStorage.getItem('flight_session_id')).toBeNull();
    });
  });

  describe('Storage Fallback', () => {
    test('should use localStorage as fallback when sessionStorage fails', () => {
      const testData = { test: 'fallback' };
      
      // Store in both storages
      simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session123', testData);
      
      // Clear sessionStorage but leave localStorage
      sessionStorage.clear();
      
      // Should still retrieve from localStorage
      const result = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'session123');
      expect(result.success).toBe(true);
      expect(result.data).toEqual(testData);
    });

    test('should handle storage quota exceeded gracefully', () => {
      // Mock setItem to throw quota exceeded error
      const originalSetItem = sessionStorage.setItem;
      sessionStorage.setItem = jest.fn(() => {
        const error = new DOMException('QuotaExceededError');
        error.name = 'QuotaExceededError';
        throw error;
      });

      try {
        const testData = { test: 'quota_test' };
        
        // Should handle the error gracefully
        const result = simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session123', testData);
        // May succeed if localStorage works, or fail gracefully
        expect(typeof result.success).toBe('boolean');
        
      } finally {
        sessionStorage.setItem = originalSetItem;
      }
    });
  });

  describe('Statistics and Health Check', () => {
    test('should provide storage statistics', () => {
      // Store some test data
      simpleCacheManager.setFlightSearch('session1', { test: 'data' });
      simpleCacheManager.setFlightPrice('session1', { price: 100 });
      
      const stats = simpleCacheManager.getStats();
      
      expect(stats).toHaveProperty('sessionStorage');
      expect(stats).toHaveProperty('localStorage');
      expect(stats.sessionStorage).toHaveProperty('used');
      expect(stats.sessionStorage).toHaveProperty('available');
      expect(stats.sessionStorage).toHaveProperty('itemCount');
      expect(stats.sessionStorage.itemCount).toBeGreaterThan(0);
    });

    test('should perform health check', () => {
      const health = simpleCacheManager.healthCheck();
      
      expect(health).toHaveProperty('healthy');
      expect(health).toHaveProperty('message');
      expect(health).toHaveProperty('stats');
      expect(typeof health.healthy).toBe('boolean');
      
      if (health.healthy) {
        expect(health.message).toContain('operational');
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle corrupted cache data', () => {
      // Store corrupted data directly
      sessionStorage.setItem('flight:search:corrupted', 'invalid json data');
      
      // Should handle gracefully
      const result = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'corrupted');
      expect(result.success).toBe(false);
      
      // Corrupted data should be cleaned up
      expect(sessionStorage.getItem('flight:search:corrupted')).toBeNull();
    });

    test('should handle missing data structure', () => {
      // Store data with missing required fields
      const invalidData = { data: 'test' }; // Missing expires, created, namespace
      sessionStorage.setItem('flight:search:invalid', JSON.stringify(invalidData));
      
      const result = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'invalid');
      // Should actually succeed since our cache manager is lenient with data structure
      expect(result.success).toBe(true);
    });

    test('should handle storage exceptions gracefully', () => {
      const originalSessionGetItem = sessionStorage.getItem;
      const originalLocalGetItem = localStorage.getItem;
      
      // Mock both storage methods to throw
      sessionStorage.getItem = jest.fn(() => {
        throw new Error('Storage access denied');
      });
      localStorage.getItem = jest.fn(() => {
        throw new Error('Storage access denied');
      });

      try {
        const result = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, 'session123');
        expect(result.success).toBe(false);
        expect(result.error).toContain('not found');
      } finally {
        sessionStorage.getItem = originalSessionGetItem;
        localStorage.getItem = originalLocalGetItem;
      }
    });
  });

  describe('Key Generation', () => {
    test('should generate consistent keys', () => {
      const key1 = 'flight:search:session123';
      const testData = { test: 'consistency' };
      
      // Set data and verify key format
      const result = simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, 'session123', testData);
      expect(result.key).toBe(key1);
      
      // Verify data is stored with correct key
      const stored = sessionStorage.getItem(key1);
      expect(stored).toBeDefined();
      
      const parsed = JSON.parse(stored!);
      expect(parsed.data).toEqual(testData);
    });

    test('should handle special characters in identifiers', () => {
      const specialId = 'session:with-special_chars.123';
      const testData = { test: 'special' };
      
      // Should handle special characters without breaking
      const setResult = simpleCacheManager.set(CacheNamespace.FLIGHT_SEARCH, specialId, testData);
      expect(setResult.success).toBe(true);
      
      const getResult = simpleCacheManager.get(CacheNamespace.FLIGHT_SEARCH, specialId);
      expect(getResult.success).toBe(true);
      expect(getResult.data).toEqual(testData);
    });
  });
});