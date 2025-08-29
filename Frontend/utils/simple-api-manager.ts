/**
 * Simple API Manager - SOLID/KISS/DRY Compliant
 * Replaces complex unified-api-manager with clean, focused implementation
 * 
 * Single Responsibility: Handle API calls with caching
 * DRY: Single implementation for all API operations
 * KISS: Simple, understandable code
 */

import { simpleCacheManager, CacheNamespace, CacheResult } from './simple-cache-manager';

interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  status?: string;
  cache_hit?: boolean;
  cache_key?: string;
  storage_key?: string;
  metadata?: any;
}

interface ApiError {
  success: false;
  error: string;
  message: string;
}

class SimpleApiManager {
  private static instance: SimpleApiManager;
  private pendingRequests = new Map<string, Promise<any>>();
  private cacheKeys = new Map<string, {
    seatAvailability?: string;
    serviceList?: string;
  }>();

  private constructor() {}

  static getInstance(): SimpleApiManager {
    if (!SimpleApiManager.instance) {
      SimpleApiManager.instance = new SimpleApiManager();
    }
    return SimpleApiManager.instance;
  }

  /**
   * Make HTTP request with proper error handling
   */
  private async makeRequest<T>(
    url: string,
    payload: any,
    method: 'GET' | 'POST' = 'POST'
  ): Promise<ApiResponse<T>> {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: method === 'POST' ? JSON.stringify(payload) : undefined,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || `API request failed: ${response.status}`);
    }

    // Normalize response format
    return {
      ...data,
      success: data.status === 'success' || data.success === true
    };
  }

  /**
   * Execute request with deduplication to prevent duplicate calls
   */
  private async executeWithDeduplication<T>(
    requestKey: string,
    requestFn: () => Promise<T>
  ): Promise<T> {
    // Check if same request is already pending
    if (this.pendingRequests.has(requestKey)) {
      console.log(`🔄 Deduplicating request: ${requestKey}`);
      return this.pendingRequests.get(requestKey)!;
    }

    // Execute request
    const promise = requestFn();
    this.pendingRequests.set(requestKey, promise);

    try {
      const result = await promise;
      return result;
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }

  /**
   * Get or create session ID
   */
  private getSessionId(): string {
    return simpleCacheManager.getOrCreateSessionId();
  }

  // FLIGHT OPERATIONS - Simplified and DRY

  /**
   * Get flight price with intelligent caching
   */
  async getFlightPrice(
    flightIndex: number,
    shoppingResponseId: string,
    airShoppingResponse: any
  ): Promise<ApiResponse> {
    const requestKey = `flight_price_${flightIndex}_${shoppingResponseId}`;

    return this.executeWithDeduplication(requestKey, async () => {
      const sessionId = this.getSessionId();

      // Check cache first
      const cachedResult = simpleCacheManager.getFlightPrice(sessionId);
      if (cachedResult.success) {
        console.log('✅ Using cached flight price data');
        return {
          data: cachedResult.data,
          success: true,
          cache_hit: true,
          cache_key: sessionId
        };
      }

      // Make API call
      const payload = {
        offer_id: flightIndex.toString(),
        shopping_response_id: shoppingResponseId,
        air_shopping_response: airShoppingResponse,
        session_id: sessionId,
      };

      const response = await this.makeRequest('/api/verteil/flight-price', payload);

      // Cache the response
      if (response.success && response.data) {
        simpleCacheManager.setFlightPrice(sessionId, response.data);
        
        // Proactively load seat and service data
        this.proactivelyLoadSeatAndService(sessionId, response);
      }

      return response;
    });
  }

  /**
   * Get seat availability with caching
   */
  async getSeatAvailability(flightPriceResponse: any): Promise<ApiResponse> {
    const sessionId = this.getSessionId();
    const requestKey = `seat_availability_${sessionId}`;

    return this.executeWithDeduplication(requestKey, async () => {
      // Check cache first
      const cachedResult = simpleCacheManager.getSeatAvailability(sessionId);
      if (cachedResult.success) {
        console.log('✅ Using cached seat availability data');
        return {
          data: cachedResult.data,
          success: true,
          cache_hit: true,
          cache_key: sessionId,
          storage_key: sessionId
        };
      }

      // Extract cache key from response
      const cacheKey = this.extractCacheKey(flightPriceResponse);
      if (!cacheKey) {
        throw new Error('flight_price_cache_key is required for seat availability');
      }

      // Make API call
      const response = await this.makeRequest('/api/verteil/seat-availability', {
        flight_price_cache_key: cacheKey
      });

      // Cache the response and store the backend storage key
      if (response.success && response.data) {
        simpleCacheManager.setSeatAvailability(sessionId, response.data);
        
        // Store the actual storage key returned from backend
        const backendStorageKey = response.storage_key;
        if (backendStorageKey) {
          const sessionKeys = this.cacheKeys.get(sessionId) || {};
          sessionKeys.seatAvailability = backendStorageKey;
          this.cacheKeys.set(sessionId, sessionKeys);
          console.log('🔑 Stored seat availability storage key:', backendStorageKey);
        }
      }

      return {
        ...response,
        cache_key: sessionId,
        storage_key: response.storage_key // Use actual backend storage key
      };
    });
  }

  /**
   * Get service list with caching
   */
  async getServiceList(flightPriceResponse: any): Promise<ApiResponse> {
    const sessionId = this.getSessionId();
    const requestKey = `service_list_${sessionId}`;

    return this.executeWithDeduplication(requestKey, async () => {
      // Check cache first
      const cachedResult = simpleCacheManager.getServiceList(sessionId);
      if (cachedResult.success) {
        console.log('✅ Using cached service list data');
        return {
          data: cachedResult.data,
          success: true,
          cache_hit: true,
          cache_key: sessionId,
          storage_key: sessionId
        };
      }

      // Extract cache key from response
      const cacheKey = this.extractCacheKey(flightPriceResponse);
      if (!cacheKey) {
        throw new Error('flight_price_cache_key is required for service list');
      }

      // Make API call
      const response = await this.makeRequest('/api/verteil/service-list', {
        flight_price_cache_key: cacheKey
      });

      // Cache the response and store the backend storage key
      if (response.success && response.data) {
        simpleCacheManager.setServiceList(sessionId, response.data);
        
        // Store the actual storage key returned from backend
        const backendStorageKey = response.storage_key;
        if (backendStorageKey) {
          const sessionKeys = this.cacheKeys.get(sessionId) || {};
          sessionKeys.serviceList = backendStorageKey;
          this.cacheKeys.set(sessionId, sessionKeys);
          console.log('🔑 Stored service list storage key:', backendStorageKey);
        }
      }

      return {
        ...response,
        cache_key: sessionId,
        storage_key: response.storage_key // Use actual backend storage key
      };
    });
  }

  /**
   * Create booking with proper data handling
   */
  async createBooking(
    flightOffer: any,
    passengers: any[],
    payment: any,
    contactInfo: any,
    extras?: any
  ): Promise<ApiResponse> {
    const sessionId = this.getSessionId();

    // Ensure we have required cache keys by loading seat/service data if needed
    await this.ensureCacheKeysExist(flightOffer);

    // Get the actual storage keys returned from seat/service endpoints
    const storedKeys = this.cacheKeys.get(sessionId) || {};
    const seatKey = storedKeys.seatAvailability;
    const serviceKey = storedKeys.serviceList;

    console.log('🔑 Using cache keys for order creation:', {
      sessionId,
      seatKey: seatKey ? seatKey.slice(-12) : 'None',
      serviceKey: serviceKey ? serviceKey.slice(-12) : 'None'
    });

    const payload = {
      flight_offer: flightOffer,
      passengers,
      payment,
      contact_info: contactInfo,
      session_id: sessionId,
      extras,
      // Include actual storage keys from seat/service endpoints
      seat_availability_cache_key: seatKey,
      service_list_cache_key: serviceKey,
    };

    console.log('🚀 Creating booking with simple API manager:', {
      sessionId,
      hasFlightOffer: !!flightOffer,
      hasPassengers: passengers.length > 0,
      hasExtras: !!extras,
    });

    const response = await this.makeRequest('/api/verteil/order-create', payload);

    // Cache booking data if successful
    if (response.success && response.data) {
      simpleCacheManager.setBooking(sessionId, response.data);
    }

    return response;
  }

  // UTILITY METHODS

  /**
   * Extract cache key from flight price response
   */
  private extractCacheKey(flightPriceResponse: any): string {
    return flightPriceResponse?.metadata?.flight_price_cache_key ||
           flightPriceResponse?.flight_price_cache_key ||
           flightPriceResponse?.data?.metadata?.flight_price_cache_key ||
           this.getSessionId();
  }

  /**
   * Proactively load seat and service data to prevent duplicate calls
   */
  private proactivelyLoadSeatAndService(sessionId: string, flightPriceResponse: any): void {
    // Fire and forget - load seat and service data in background
    Promise.allSettled([
      this.getSeatAvailability(flightPriceResponse),
      this.getServiceList(flightPriceResponse)
    ]).then(([seatResult, serviceResult]) => {
      if (seatResult.status === 'fulfilled') {
        console.log('✅ Proactively loaded seat availability');
      } else {
        console.warn('⚠️ Proactive seat loading failed:', seatResult.reason);
      }

      if (serviceResult.status === 'fulfilled') {
        console.log('✅ Proactively loaded service list');
      } else {
        console.warn('⚠️ Proactive service loading failed:', serviceResult.reason);
      }
    });
  }

  /**
   * Ensure cache keys exist before booking
   */
  private async ensureCacheKeysExist(flightOffer: any): Promise<void> {
    const sessionId = this.getSessionId();
    
    // Check if we have cached seat/service data AND storage keys
    const seatExists = simpleCacheManager.exists(CacheNamespace.SEAT_AVAILABILITY, sessionId);
    const serviceExists = simpleCacheManager.exists(CacheNamespace.SERVICE_LIST, sessionId);
    const storedKeys = this.cacheKeys.get(sessionId) || {};
    const hasStorageKeys = storedKeys.seatAvailability && storedKeys.serviceList;

    if (!seatExists || !serviceExists || !hasStorageKeys) {
      console.log('⚠️ Missing cached seat/service data or storage keys, loading before booking...', {
        seatExists,
        serviceExists,
        hasStorageKeys,
        seatKey: storedKeys.seatAvailability ? '✅' : '❌',
        serviceKey: storedKeys.serviceList ? '✅' : '❌'
      });

      try {
        const promises = [];
        if (!seatExists || !storedKeys.seatAvailability) {
          promises.push(this.getSeatAvailability(flightOffer));
        }
        if (!serviceExists || !storedKeys.serviceList) {
          promises.push(this.getServiceList(flightOffer));
        }

        await Promise.allSettled(promises);
        console.log('✅ Loaded missing seat/service data and storage keys');
      } catch (error) {
        console.warn('⚠️ Failed to preload seat/service data:', error);
      }
    } else {
      console.log('✅ All cache keys already available for booking');
    }
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.pendingRequests.clear();
    simpleCacheManager.clearSession();
    console.log('🗑️ Cleared all caches');
  }

  /**
   * Get debug information
   */
  getDebugInfo() {
    return {
      pendingRequests: Array.from(this.pendingRequests.keys()),
      cacheStats: simpleCacheManager.getStats(),
      sessionId: simpleCacheManager.getCurrentSessionId(),
      cacheHealth: simpleCacheManager.healthCheck()
    };
  }
}

// Export singleton instance
export const simpleApiManager = SimpleApiManager.getInstance();