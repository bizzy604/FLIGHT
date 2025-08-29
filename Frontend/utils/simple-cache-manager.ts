/**
 * Simple Frontend Cache Manager - SOLID/KISS/DRY Compliant
 * Replaces 6+ cache managers with single, focused implementation
 * 
 * Single Responsibility: Handle browser storage caching
 * Open/Closed: Extensible without modification
 * DRY: Single implementation for all data types
 */

interface CacheItem {
  data: any;
  expires: number;
  created: number;
  namespace: string;
}

interface CacheResult {
  success: boolean;
  data?: any;
  error?: string;
  cacheHit?: boolean;
  key?: string;
}

enum CacheNamespace {
  FLIGHT_SEARCH = 'flight:search',
  FLIGHT_PRICE = 'flight:price',  
  SEAT_AVAILABILITY = 'seat:availability',
  SERVICE_LIST = 'service:list',
  BOOKING = 'booking',
  SESSION = 'session',
  NAVIGATION = 'navigation'
}

class SimpleCacheManager {
  private static instance: SimpleCacheManager;
  private readonly DEFAULT_TTL = 30 * 60 * 1000; // 30 minutes
  
  // TTL policies for different namespaces (in milliseconds)
  private readonly TTL_POLICIES: Record<string, number> = {
    [CacheNamespace.FLIGHT_SEARCH]: 30 * 60 * 1000,    // 30 minutes
    [CacheNamespace.FLIGHT_PRICE]: 30 * 60 * 1000,     // 30 minutes
    [CacheNamespace.SEAT_AVAILABILITY]: 15 * 60 * 1000, // 15 minutes
    [CacheNamespace.SERVICE_LIST]: 15 * 60 * 1000,      // 15 minutes
    [CacheNamespace.BOOKING]: 60 * 60 * 1000,           // 60 minutes
    [CacheNamespace.SESSION]: 2 * 60 * 60 * 1000,       // 2 hours
    [CacheNamespace.NAVIGATION]: 30 * 60 * 1000         // 30 minutes
  };

  private constructor() {}

  static getInstance(): SimpleCacheManager {
    if (!SimpleCacheManager.instance) {
      SimpleCacheManager.instance = new SimpleCacheManager();
    }
    return SimpleCacheManager.instance;
  }

  /**
   * Generate consistent cache key
   */
  private generateKey(namespace: CacheNamespace, identifier: string): string {
    return `${namespace}:${identifier}`;
  }

  /**
   * Get TTL for namespace
   */
  private getTTL(namespace: CacheNamespace): number {
    return this.TTL_POLICIES[namespace] || this.DEFAULT_TTL;
  }

  /**
   * Get item from storage with validation
   */
  private getFromStorage(storage: Storage, key: string): CacheItem | null {
    try {
      const item = storage.getItem(key);
      if (!item) return null;

      const parsed: CacheItem = JSON.parse(item);
      
      // Check expiration
      if (Date.now() > parsed.expires) {
        storage.removeItem(key);
        return null;
      }

      return parsed;
    } catch {
      // Clean up corrupted data
      storage.removeItem(key);
      return null;
    }
  }

  /**
   * Store item in storage with error handling
   */
  private storeInStorage(storage: Storage, key: string, item: CacheItem): boolean {
    try {
      storage.setItem(key, JSON.stringify(item));
      return true;
    } catch (error) {
      // Handle quota exceeded or other storage errors
      console.warn(`Failed to store in ${storage === sessionStorage ? 'session' : 'local'}Storage:`, error);
      
      // Try emergency cleanup and retry
      this.emergencyCleanup(storage);
      try {
        storage.setItem(key, JSON.stringify(item));
        return true;
      } catch {
        return false;
      }
    }
  }

  /**
   * Emergency cleanup when storage is full
   */
  private emergencyCleanup(storage: Storage): void {
    const items: Array<{key: string; created: number}> = [];
    
    // Collect all cache items with timestamps
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (key && key.includes(':')) {
        try {
          const item: CacheItem = JSON.parse(storage.getItem(key)!);
          items.push({key, created: item.created});
        } catch {
          // Remove corrupted items
          storage.removeItem(key);
        }
      }
    }

    // Sort by creation time (oldest first) and remove 25%
    items.sort((a, b) => a.created - b.created);
    const itemsToRemove = Math.floor(items.length * 0.25);
    
    for (let i = 0; i < itemsToRemove; i++) {
      storage.removeItem(items[i].key);
    }

    console.log(`Emergency cleanup: removed ${itemsToRemove} old cache items`);
  }

  // CORE OPERATIONS - Single implementation for all data types

  /**
   * Set cache item - works for all data types
   * Replaces all specific storage methods
   */
  set(namespace: CacheNamespace, identifier: string, data: any, ttl?: number): CacheResult {
    try {
      const key = this.generateKey(namespace, identifier);
      const ttlMs = ttl ? ttl * 1000 : this.getTTL(namespace);
      const now = Date.now();
      
      const item: CacheItem = {
        data,
        expires: now + ttlMs,
        created: now,
        namespace: namespace.toString()
      };

      // Try to store in both storages (redundancy)
      const sessionSuccess = this.storeInStorage(sessionStorage, key, item);
      const localSuccess = this.storeInStorage(localStorage, key, item);

      if (sessionSuccess || localSuccess) {
        return {
          success: true,
          data,
          key,
          cacheHit: false
        };
      } else {
        return {
          success: false,
          error: 'Failed to store in any storage location'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: `Cache set error: ${error}`
      };
    }
  }

  /**
   * Get cache item - works for all data types
   * Replaces all specific retrieval methods
   */
  get(namespace: CacheNamespace, identifier: string): CacheResult {
    try {
      const key = this.generateKey(namespace, identifier);
      
      // Try sessionStorage first (faster)
      let item = this.getFromStorage(sessionStorage, key);
      let source = 'session';
      
      if (!item) {
        // Fallback to localStorage
        item = this.getFromStorage(localStorage, key);
        source = 'local';
        
        // If found in localStorage, restore to sessionStorage for faster future access
        if (item) {
          this.storeInStorage(sessionStorage, key, item);
        }
      }

      if (item) {
        return {
          success: true,
          data: item.data,
          cacheHit: true,
          key
        };
      } else {
        return {
          success: false,
          error: 'Data not found or expired',
          cacheHit: false,
          key
        };
      }
    } catch (error) {
      return {
        success: false,
        error: `Cache get error: ${error}`,
        cacheHit: false
      };
    }
  }

  /**
   * Delete cache item
   */
  delete(namespace: CacheNamespace, identifier: string): boolean {
    try {
      const key = this.generateKey(namespace, identifier);
      sessionStorage.removeItem(key);
      localStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if item exists and is not expired
   */
  exists(namespace: CacheNamespace, identifier: string): boolean {
    const result = this.get(namespace, identifier);
    return result.success;
  }

  // CONVENIENCE METHODS - Maintain API compatibility

  setFlightSearch(sessionId: string, data: any, ttl?: number): CacheResult {
    return this.set(CacheNamespace.FLIGHT_SEARCH, sessionId, data, ttl);
  }

  getFlightSearch(sessionId: string): CacheResult {
    return this.get(CacheNamespace.FLIGHT_SEARCH, sessionId);
  }

  setFlightPrice(sessionId: string, data: any, ttl?: number): CacheResult {
    return this.set(CacheNamespace.FLIGHT_PRICE, sessionId, data, ttl);
  }

  getFlightPrice(sessionId: string): CacheResult {
    return this.get(CacheNamespace.FLIGHT_PRICE, sessionId);
  }

  setSeatAvailability(sessionId: string, data: any, ttl?: number): CacheResult {
    return this.set(CacheNamespace.SEAT_AVAILABILITY, sessionId, data, ttl);
  }

  getSeatAvailability(sessionId: string): CacheResult {
    return this.get(CacheNamespace.SEAT_AVAILABILITY, sessionId);
  }

  setServiceList(sessionId: string, data: any, ttl?: number): CacheResult {
    return this.set(CacheNamespace.SERVICE_LIST, sessionId, data, ttl);
  }

  getServiceList(sessionId: string): CacheResult {
    return this.get(CacheNamespace.SERVICE_LIST, sessionId);
  }

  setBooking(sessionId: string, data: any, ttl?: number): CacheResult {
    return this.set(CacheNamespace.BOOKING, sessionId, data, ttl);
  }

  getBooking(sessionId: string): CacheResult {
    return this.get(CacheNamespace.BOOKING, sessionId);
  }

  // SESSION MANAGEMENT - Simplified

  generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  getOrCreateSessionId(): string {
    let sessionId = localStorage.getItem('flight_session_id');
    
    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem('flight_session_id', sessionId);
      console.log('Created new session ID:', sessionId);
    }
    
    return sessionId;
  }

  getCurrentSessionId(): string | null {
    return localStorage.getItem('flight_session_id');
  }

  clearSession(): void {
    const sessionId = this.getCurrentSessionId();
    if (sessionId) {
      // Clear all session-related cache items
      this.clearSessionData(sessionId);
    }
    
    // Clear session ID
    localStorage.removeItem('flight_session_id');
    console.log('Session cleared');
  }

  clearSessionData(sessionId: string): number {
    let cleared = 0;
    const namespaces = Object.values(CacheNamespace);
    
    for (const namespace of namespaces) {
      if (this.delete(namespace, sessionId)) {
        cleared++;
      }
    }
    
    console.log(`Cleared ${cleared} cache items for session: ${sessionId}`);
    return cleared;
  }

  // UTILITY METHODS

  clearNamespace(namespace: CacheNamespace): number {
    let cleared = 0;
    const prefix = `${namespace}:`;
    
    // Clear from both storages
    [sessionStorage, localStorage].forEach(storage => {
      for (let i = storage.length - 1; i >= 0; i--) {
        const key = storage.key(i);
        if (key && key.startsWith(prefix)) {
          storage.removeItem(key);
          cleared++;
        }
      }
    });
    
    console.log(`Cleared ${cleared} items from namespace: ${namespace}`);
    return cleared;
  }

  clearAll(): void {
    sessionStorage.clear();
    localStorage.clear();
    console.log('All cache cleared');
  }

  getStats(): {
    sessionStorage: {used: number; available: number; itemCount: number};
    localStorage: {used: number; available: number; itemCount: number};
  } {
    const getStorageInfo = (storage: Storage) => {
      let used = 0;
      const items = [];
      
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key) {
          const value = storage.getItem(key);
          if (value) {
            used += key.length + value.length;
            items.push(key);
          }
        }
      }
      
      return {
        used,
        available: 5 * 1024 * 1024 - used, // Approximate 5MB limit
        itemCount: items.length
      };
    };

    return {
      sessionStorage: getStorageInfo(sessionStorage),
      localStorage: getStorageInfo(localStorage)
    };
  }

  healthCheck(): {healthy: boolean; message: string; stats: any} {
    try {
      const testKey = `health_check_${Date.now()}`;
      const testData = {test: true, timestamp: Date.now()};
      
      // Test set operation
      const setResult = this.set(CacheNamespace.SESSION, testKey, testData, 10);
      
      if (!setResult.success) {
        return {
          healthy: false,
          message: 'Cache set operation failed',
          stats: this.getStats()
        };
      }
      
      // Test get operation
      const getResult = this.get(CacheNamespace.SESSION, testKey);
      
      if (!getResult.success) {
        return {
          healthy: false,
          message: 'Cache get operation failed',
          stats: this.getStats()
        };
      }
      
      // Clean up
      this.delete(CacheNamespace.SESSION, testKey);
      
      return {
        healthy: true,
        message: 'Cache system operational',
        stats: this.getStats()
      };
    } catch (error) {
      return {
        healthy: false,
        message: `Health check failed: ${error}`,
        stats: this.getStats()
      };
    }
  }
}

// Export singleton instance and types
export const simpleCacheManager = SimpleCacheManager.getInstance();
export { CacheNamespace, type CacheResult };