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

      // 🚀 PRIORITY FIX: Always make fresh API calls, cache is just for storage
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
      // 🚀 PRIORITY FIX: Always make fresh API calls, cache is just for storage
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
        
        // 🚀 FIXED: Backend doesn't send storage_key, use the cache key we generated
        const backendStorageKey = response.storage_key || cacheKey;
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
        storage_key: response.storage_key || cacheKey // Use cache key if no storage key
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
      // 🚀 PRIORITY FIX: Always make fresh API calls, cache is just for storage
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
        
        // 🚀 FIXED: Backend doesn't send storage_key, use the cache key we generated
        const backendStorageKey = response.storage_key || cacheKey;
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
        storage_key: response.storage_key || cacheKey // Use cache key if no storage key
      };
    });
  }

  /**
   * Create booking
   *
   * Why:
   * - OrderCreate needs previously materialized SeatAvailability and ServiceList artifacts; we pass their storage keys so
   *   the backend can reuse cached NDC data instead of recomputing, keeping payment flow fast and reliable.
   * - In production, raw flight price response may be absent in sessionStorage; this method is designed to proceed using
   *   stable cache keys derived during pricing/selection (see extractCacheKey for fallbacks).
   *
   * Assumptions:
   * - The provided flightOffer (possibly transformed) contains enough identity to derive or relate to
   *   flight_price_cache_key via prior steps, even if raw_response is missing.
   * - Seat/service data may or may not exist; ensureCacheKeysExist will idempotently hydrate missing caches and persist
   *   backend storage keys in this.cacheKeys for the current session.
   *
   * Edge cases:
   * - Missing rawFlightPriceResponse: non-blocking. We fall back to metadata.flight_price_cache_key, then offer IDs, then
   *   NDC ResponseID, finally sessionId.
   * - Backend might return its own storage_key; we persist that to guarantee subsequent OrderCreate joins exact cache rows.
   *
   * Related components:
   * - booking-form.tsx/payment page: prepares selected offer + metadata and triggers booking.
   * - proactive loaders: populate seat/service cache and record backend storage keys used here.
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
   * Extract a stable cache key from any flight price response or transformed offer object.
   *
   * Why:
   * - Seat availability, service list, and booking must reference the same cached artifacts in Redis/backend.
   * - The raw NDC price response may not be available client-side; this function provides resilient fallbacks.
   *
   * Fallback order (strongest to weakest):
   * 1) metadata.flight_price_cache_key
   * 2) flight_price_cache_key (direct field)
   * 3) original_offer_id → offer_id (transformed shapes)
   * 4) NDC OfferID or ShoppingResponseID.ResponseID
   * 5) Current sessionId (last resort)
   *
   * Edge cases:
   * - If input lacks all identity fields, we log and return sessionId to keep flows unblocked.
   * - Accepts both transformed frontend objects and raw NDC-like shapes.
   */
  private extractCacheKey(flightPriceResponse: any): string {
    // 🚀 PRIORITY: Check for flight_price_cache_key in metadata (stored after flight price API call)
    if (flightPriceResponse?.metadata?.flight_price_cache_key) {
      console.log('🔑 Using metadata flight_price_cache_key:', flightPriceResponse.metadata.flight_price_cache_key)
      return flightPriceResponse.metadata.flight_price_cache_key
    }
    
    // Check for direct cache key field
    if (flightPriceResponse?.flight_price_cache_key) {
      console.log('🔑 Using direct flight_price_cache_key:', flightPriceResponse.flight_price_cache_key)
      return flightPriceResponse.flight_price_cache_key
    }
    
    // Try original offer_id from transformed response
    if (flightPriceResponse?.original_offer_id) {
      console.log('🔑 Using original_offer_id as cache key:', flightPriceResponse.original_offer_id)
      return flightPriceResponse.original_offer_id
    }
    
    // Try offer_id from transformed response
    if (flightPriceResponse?.offer_id) {
      console.log('🔑 Using offer_id as cache key:', flightPriceResponse.offer_id)
      return flightPriceResponse.offer_id
    }
    
    // Fallback: extract from raw NDC response structure
    const offerId = flightPriceResponse?.OfferID?.value || 
                   flightPriceResponse?.data?.OfferID?.value
    
    const responseId = flightPriceResponse?.ShoppingResponseID?.ResponseID?.value ||
                      flightPriceResponse?.shopping_response_id ||
                      flightPriceResponse?.data?.ShoppingResponseID?.ResponseID?.value
    
    if (offerId) {
      console.log('🔑 Using NDC OfferID as cache key:', offerId)
      return offerId
    }
    
    if (responseId) {
      console.log('🔑 Using NDC ResponseID as cache key:', responseId)
      return responseId
    }
    
    // Last resort: use session ID
    const sessionId = this.getSessionId()
    console.warn('⚠️ No valid cache key found, using session ID:', sessionId)
    console.warn('Available response keys:', Object.keys(flightPriceResponse || {}))
    return sessionId
  }

  /**
   * Proactively load seat and service data in the background to prevent duplicate synchronous calls later.
   *
   * Why:
   * - Improves UX by warming the cache between pricing and payment. Prevents blocking calls in payment flow.
   * - Persists backend storage keys that are later required by OrderCreate.
   *
   * Behavior:
   * - Fire-and-forget concurrent loaders; logs results; never throws upstream.
   * - Idempotent: loaders short-circuit if cached data already exists.
   */
  private proactivelyLoadSeatAndService(sessionId: string, flightPriceResponse: any): void {
    // 🚀 OPTIMIZATION: Use dedicated proactive loading methods that store in cache
    // Don't use getSeatAvailability/getServiceList as they now always make fresh API calls
    
    console.log('🚀 Starting proactive seat/service loading in background...');
    
    // Fire and forget - load seat and service data in background
    Promise.allSettled([
      this.proactiveLoadSeatAvailability(sessionId, flightPriceResponse),
      this.proactiveLoadServiceList(sessionId, flightPriceResponse)
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
   * Proactive seat availability loading (stores in cache; does not return data to caller).
   *
   * Assumptions:
   * - extractCacheKey can resolve a stable key even when raw flight price response is missing.
   * - Backend may return a storage_key; if absent, we reuse the derived cacheKey.
   *
   * Edge cases:
   * - If cache already exists for this session, we skip to avoid redundant network calls.
   */
  private async proactiveLoadSeatAvailability(sessionId: string, flightPriceResponse: any): Promise<void> {
    // Check if we already have cached data
    const existingData = simpleCacheManager.getSeatAvailability(sessionId);
    if (existingData.success) {
      console.log('✅ Seat availability already cached, skipping proactive load');
      return;
    }

    // Extract cache key and make API call
    const cacheKey = this.extractCacheKey(flightPriceResponse);
    if (!cacheKey) {
      throw new Error('flight_price_cache_key is required for proactive seat loading');
    }

    const response = await this.makeRequest('/api/verteil/seat-availability', {
      flight_price_cache_key: cacheKey
    });

    // Store in cache for later use
    if (response.success && response.data) {
      simpleCacheManager.setSeatAvailability(sessionId, response.data);
      
      // Store backend storage key
      const backendStorageKey = response.storage_key || cacheKey;
      const sessionKeys = this.cacheKeys.get(sessionId) || {};
      sessionKeys.seatAvailability = backendStorageKey;
      this.cacheKeys.set(sessionId, sessionKeys);
      console.log('🔑 Proactively stored seat availability cache key:', backendStorageKey);
    }
  }

  /**
   * Proactive service list loading (stores in cache; does not return data to caller).
   *
   * Mirrors proactiveLoadSeatAvailability assumptions and behavior; uses the same cache key derivation and
   * persists backend storage_key when provided so OrderCreate can reference the exact cache slot.
   */
  private async proactiveLoadServiceList(sessionId: string, flightPriceResponse: any): Promise<void> {
    // Check if we already have cached data
    const existingData = simpleCacheManager.getServiceList(sessionId);
    if (existingData.success) {
      console.log('✅ Service list already cached, skipping proactive load');
      return;
    }

    // Extract cache key and make API call
    const cacheKey = this.extractCacheKey(flightPriceResponse);
    if (!cacheKey) {
      throw new Error('flight_price_cache_key is required for proactive service loading');
    }

    const response = await this.makeRequest('/api/verteil/service-list', {
      flight_price_cache_key: cacheKey
    });

    // Store in cache for later use
    if (response.success && response.data) {
      simpleCacheManager.setServiceList(sessionId, response.data);
      
      // Store backend storage key
      const backendStorageKey = response.storage_key || cacheKey;
      const sessionKeys = this.cacheKeys.get(sessionId) || {};
      sessionKeys.serviceList = backendStorageKey;
      this.cacheKeys.set(sessionId, sessionKeys);
      console.log('🔑 Proactively stored service list cache key:', backendStorageKey);
    }
  }

  /**
   * Ensure we have cached seat/service data AND the backend storage keys before booking.
   *
   * Why:
   * - OrderCreate joins precomputed seat and service artifacts via storage keys. This step backfills cache when missing.
   *
   * Behavior:
   * - Checks session-scoped presence; if missing, calls getSeatAvailability/getServiceList (which derive cache key from offer)
   *   to hydrate cache and persist storage_key values into this.cacheKeys.
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