import { logger } from './logger';
import { sessionManager } from './session-manager';

interface ApiResponse<T = any> {
  data: T;
  success?: boolean;  // Make optional since backend might not send this
  status?: string;    // Backend might send status instead
  cache_hit?: boolean;
  storage_key?: string;
  metadata?: any;
}

interface SessionData {
  sessionId: string | null;
  flightPriceCacheKey: string | null;
  seatAvailabilityStorageKey: string | null;
  serviceListStorageKey: string | null;
  seatAvailabilityCacheKey: string | null;
  serviceListCacheKey: string | null;
}

class UnifiedApiManager {
  private pendingRequests: Map<string, Promise<any>> = new Map();
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  
  /**
   * KISS Principle: Single method to handle all API calls consistently
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
    logger.info(`API ${method} ${url}`, { status: response.status });
    
    if (!response.ok) {
      throw new Error(data.message || `API request failed: ${response.status}`);
    }
    
    // Backend response received successfully
    logger.info(`✅ ${method} ${url} completed`, { status: response.status });
    
    // Normalize the response - backend sends 'status' field, not 'success'
    // Backend format: { status: 'success'|'error', data: {...}, request_id: '...' }
    if (data.status === 'success') {
      data.success = true;
    } else if (data.status === 'error') {
      data.success = false;
    } else if (data.status) {
      // Any other status value defaults to false
      data.success = false;
    }
    
    return data;
  }
  
  /**
   * DRY Principle: Unified request deduplication logic
   */
  private async executeWithDeduplication<T>(
    requestKey: string,
    requestFn: () => Promise<T>
  ): Promise<T> {
    // Check if same request is already pending
    if (this.pendingRequests.has(requestKey)) {
      logger.info(`🔄 Deduplicating request: ${requestKey}`);
      return this.pendingRequests.get(requestKey)!;
    }
    
    // Check cache first
    const cached = this.cache.get(requestKey);
    if (cached && (Date.now() - cached.timestamp) < this.CACHE_DURATION) {
      logger.info(`✅ Using cached response: ${requestKey}`);
      return cached.data;
    }
    
    // Execute request
    const promise = requestFn();
    this.pendingRequests.set(requestKey, promise);
    
    try {
      const result = await promise;
      this.cache.set(requestKey, { data: result, timestamp: Date.now() });
      return result;
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }
  
  /**
   * KISS Principle: Standardized session data management
   */
  private getSessionData(): SessionData {
    // 🔍 DEBUG: Check what's actually in sessionStorage
    const seatCacheKey = sessionStorage.getItem('seat_availability_cache_key');
    const serviceCacheKey = sessionStorage.getItem('service_list_cache_key');
    
    // 🚨 CRITICAL DEBUG: Check ALL sessionStorage contents
    const allSessionKeys: { [key: string]: string | null } = {};
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key) {
        allSessionKeys[key] = sessionStorage.getItem(key);
      }
    }
    
    logger.error('🚨 CRITICAL DEBUG: Complete sessionStorage contents during getSessionData:', {
      seat_availability_cache_key: seatCacheKey,
      service_list_cache_key: serviceCacheKey,
      all_session_keys: Object.keys(sessionStorage).filter(key => key.includes('cache_key') || key.includes('storage_key')),
      complete_session_storage: allSessionKeys
    });
    
    return {
      sessionId: sessionManager.getOrCreateSessionId(),
      flightPriceCacheKey: sessionStorage.getItem('flight_price_cache_key'),
      seatAvailabilityStorageKey: sessionStorage.getItem('seat_availability_storage_key'),
      serviceListStorageKey: sessionStorage.getItem('service_list_storage_key'),
      seatAvailabilityCacheKey: seatCacheKey,
      serviceListCacheKey: serviceCacheKey,
    };
  }
  
  /**
   * KISS Principle: Single method to extract cache key consistently
   */
  private extractCacheKey(flightPriceResponse: any): string {
    return flightPriceResponse?.metadata?.flight_price_cache_key ||
           flightPriceResponse?.flight_price_cache_key ||
           flightPriceResponse?.data?.metadata?.flight_price_cache_key ||
           sessionStorage.getItem('flight_price_cache_key') ||
           '';
  }
  
  /**
   * Unified flight price API with proper session management
   */
  async getFlightPrice(
    flightIndex: number, 
    shoppingResponseId: string, 
    airShoppingResponse: any
  ): Promise<ApiResponse> {
    const requestKey = `flight_price_${flightIndex}_${shoppingResponseId}`;
    
    return this.executeWithDeduplication(requestKey, async () => {
      const session = this.getSessionData();
      
      const payload = {
        offer_id: flightIndex.toString(),
        shopping_response_id: shoppingResponseId,
        air_shopping_response: airShoppingResponse,
        session_id: session.sessionId, // Ensure session is included
      };
      
      const response = await this.makeRequest('/api/verteil/flight-price', payload);
      
      // Log success for monitoring
      logger.info('✅ Flight price request completed', {
        success: response.success,
        status: response.status,
        hasData: !!response.data
      });
      
      // Store session data consistently
      if (response.metadata?.flight_price_cache_key) {
        sessionStorage.setItem('flight_price_cache_key', response.metadata.flight_price_cache_key);
      }
      
      // 🚀 PROACTIVE LOADING: Immediately load seat/service data for one-way flight to prevent duplicate calls
      if (response.success && response.data) {
        logger.info('🚀 Starting proactive seat/service loading for one-way flight...');
        
        // Load seat availability and service list in parallel (fire and forget)
        Promise.allSettled([
          this.loadSeatAvailabilityProactive(response),
          this.loadServiceListProactive(response)
        ]).then(([seatResult, serviceResult]) => {
          if (seatResult.status === 'fulfilled') {
            logger.info('✅ Proactive seat availability loading completed for one-way flight');
          } else {
            logger.warn('⚠️ Proactive seat availability loading failed:', seatResult.reason);
          }
          
          if (serviceResult.status === 'fulfilled') {
            logger.info('✅ Proactive service list loading completed');
          } else {
            logger.warn('⚠️ Proactive service list loading failed:', serviceResult.reason);
          }
        });
      }
      
      return response;
    });
  }
  
  /**
   * Unified seat availability with proactive caching (NO cache checks)
   */
  async getSeatAvailability(flightPriceResponse: any, segmentKey?: string): Promise<ApiResponse> {
    const cacheKey = this.extractCacheKey(flightPriceResponse);
    if (!cacheKey) {
      throw new Error('flight_price_cache_key is required for seat availability');
    }
    
    // For one-way flights, ignore segmentKey and use base cache key
    const requestKey = `seat_availability_${cacheKey}`;
    
    // Check if we have cached data from proactive loading first
    const cached = this.cache.get(requestKey);
    if (cached && (Date.now() - cached.timestamp) < this.CACHE_DURATION) {
      logger.info('✅ Using proactively cached seat availability data (one-way flight)');
      
      // 🚀 CRITICAL FIX: Ensure cache keys are preserved when returning cached data
      const cachedData = cached.data;
      if (cachedData && (!cachedData.cache_key || !cachedData.storage_key)) {
        // Try to restore cache keys from sessionStorage or generate them
        const storedCacheKey = sessionStorage.getItem('seat_availability_cache_key');
        const storedStorageKey = sessionStorage.getItem('seat_availability_storage_key');
        
        logger.info('🔧 FIXING cached seat data - restoring missing keys:', {
          hadCacheKey: !!cachedData.cache_key,
          hadStorageKey: !!cachedData.storage_key,
          storedCacheKey,
          storedStorageKey
        });
        
        if (storedCacheKey) cachedData.cache_key = storedCacheKey;
        if (storedStorageKey) cachedData.storage_key = storedStorageKey;
      }
      
      return cachedData;
    }
    
    return this.executeWithDeduplication(requestKey, async () => {
      // BYPASS cache check - go directly to API (eliminates duplicate calls)
      logger.info('🚀 Fetching seat availability directly (no cache check)');
      const response = await this.makeRequest('/api/verteil/seat-availability', {
        flight_price_cache_key: cacheKey
        // No segment_key needed for one-way flights
      });
      
      // Store both storage key and cache key for future use
      logger.info('🔍 Seat availability response keys:', {
        hasStorageKey: !!response.storage_key,
        hasCacheKey: !!response.cache_key,
        storageKey: response.storage_key,
        cacheKey: response.cache_key,
        responseKeys: Object.keys(response || {})
      });
      
      if (response.storage_key) {
        sessionStorage.setItem('seat_availability_storage_key', response.storage_key);
        logger.info('✅ Stored seat_availability_storage_key:', response.storage_key);
      }
      if (response.cache_key) {
        sessionStorage.setItem('seat_availability_cache_key', response.cache_key);
        logger.info('✅ Stored seat_availability_cache_key:', response.cache_key);
        
        // 🔍 VERIFY: Check if storage actually worked
        const storedValue = sessionStorage.getItem('seat_availability_cache_key');
        if (storedValue !== response.cache_key) {
          logger.error('🚨 STORAGE VERIFICATION FAILED: seat_availability_cache_key not properly stored!', {
            attempted: response.cache_key,
            actuallyStored: storedValue
          });
        } else {
          logger.info('✅ VERIFIED: seat_availability_cache_key correctly stored');
        }
      } else {
        logger.warn('⚠️ No cache_key found in seat availability response');
      }
      
      return response;
    });
  }
  
  /**
   * Unified service list with proactive caching (NO cache checks)
   */
  async getServiceList(flightPriceResponse: any): Promise<ApiResponse> {
    const cacheKey = this.extractCacheKey(flightPriceResponse);
    if (!cacheKey) {
      throw new Error('flight_price_cache_key is required for service list');
    }
    
    const requestKey = `service_list_${cacheKey}`;
    
    // Check if we have cached data from proactive loading first
    const cached = this.cache.get(requestKey);
    if (cached && (Date.now() - cached.timestamp) < this.CACHE_DURATION) {
      logger.info('✅ Using proactively cached service list data');
      
      // 🚀 CRITICAL FIX: Ensure cache keys are preserved when returning cached data
      const cachedData = cached.data;
      if (cachedData && (!cachedData.cache_key || !cachedData.storage_key)) {
        // Try to restore cache keys from sessionStorage or generate them
        const storedCacheKey = sessionStorage.getItem('service_list_cache_key');
        const storedStorageKey = sessionStorage.getItem('service_list_storage_key');
        
        logger.info('🔧 FIXING cached service data - restoring missing keys:', {
          hadCacheKey: !!cachedData.cache_key,
          hadStorageKey: !!cachedData.storage_key,
          storedCacheKey,
          storedStorageKey
        });
        
        if (storedCacheKey) cachedData.cache_key = storedCacheKey;
        if (storedStorageKey) cachedData.storage_key = storedStorageKey;
      }
      
      return cachedData;
    }
    
    return this.executeWithDeduplication(requestKey, async () => {
      // BYPASS cache check - go directly to API (eliminates duplicate calls)
      logger.info('🚀 Fetching service list directly (no cache check)');
      const response = await this.makeRequest('/api/verteil/service-list', {
        flight_price_cache_key: cacheKey,
      });
      
      // Store storage key for future use
      // Store both storage key and cache key for future use
      logger.info('🔍 Service list response keys:', {
        hasStorageKey: !!response.storage_key,
        hasCacheKey: !!response.cache_key,
        storageKey: response.storage_key,
        cacheKey: response.cache_key,
        responseKeys: Object.keys(response || {})
      });
      
      if (response.storage_key) {
        sessionStorage.setItem('service_list_storage_key', response.storage_key);
        logger.info('✅ Stored service_list_storage_key:', response.storage_key);
      }
      if (response.cache_key) {
        sessionStorage.setItem('service_list_cache_key', response.cache_key);
        logger.info('✅ Stored service_list_cache_key:', response.cache_key);
        
        // 🔍 VERIFY: Check if storage actually worked
        const storedValue = sessionStorage.getItem('service_list_cache_key');
        if (storedValue !== response.cache_key) {
          logger.error('🚨 STORAGE VERIFICATION FAILED: service_list_cache_key not properly stored!', {
            attempted: response.cache_key,
            actuallyStored: storedValue
          });
        } else {
          logger.info('✅ VERIFIED: service_list_cache_key correctly stored');
        }
      } else {
        logger.warn('⚠️ No cache_key found in service list response');
      }
      
      return response;
    });
  }
  
  /**
   * Unified booking creation with proper session and data handling
   */
  async createBooking(
    flightOffer: any, 
    passengers: any[], 
    payment: any, 
    contactInfo: any, 
    extras?: any
  ): Promise<ApiResponse> {
    const session = this.getSessionData();
    
    // Ensure session ID exists (handled by session manager)
    session.sessionId = sessionManager.getOrCreateSessionId();
    
    // Ensure flight offer has required cache key
    if (!flightOffer.flight_price_cache_key && session.flightPriceCacheKey) {
      flightOffer.flight_price_cache_key = session.flightPriceCacheKey;
    }
    
    // 🚀 CRITICAL FIX: If seat/service cache keys are missing, load them before booking
    logger.info('🔍 DEBUG: Initial session cache keys check:', {
      hasSeats: !!session.seatAvailabilityCacheKey,
      hasServices: !!session.serviceListCacheKey,
      seatKey: session.seatAvailabilityCacheKey,
      serviceKey: session.serviceListCacheKey
    });
    
    if (!session.seatAvailabilityCacheKey || !session.serviceListCacheKey) {
      logger.warn('⚠️ Missing seat/service cache keys, loading them before booking...');
      logger.warn('🔍 Missing keys details:', {
        seatMissing: !session.seatAvailabilityCacheKey,
        serviceMissing: !session.serviceListCacheKey
      });
      
      try {
        // Load seat availability and service list to ensure cache keys are available
        const [seatResponse, serviceResponse] = await Promise.allSettled([
          this.getSeatAvailability(flightOffer),
          this.getServiceList(flightOffer)
        ]);
        
        if (seatResponse.status === 'fulfilled') {
          logger.info('✅ Loaded seat availability before booking');
          // 🔍 DEBUG: Check what cache keys were returned
          const seatData = seatResponse.value;
          logger.info('🔍 DEBUG: Seat availability response structure:', {
            hasData: !!seatData,
            hasCacheKey: !!(seatData && seatData.cache_key),
            hasStorageKey: !!(seatData && seatData.storage_key),
            cacheKey: seatData?.cache_key,
            storageKey: seatData?.storage_key,
            responseKeys: seatData ? Object.keys(seatData) : []
          });
        } else {
          logger.warn('⚠️ Failed to load seat availability before booking:', seatResponse.reason);
        }
        
        if (serviceResponse.status === 'fulfilled') {
          logger.info('✅ Loaded service list before booking');
          // 🔍 DEBUG: Check what cache keys were returned  
          const serviceData = serviceResponse.value;
          logger.info('🔍 DEBUG: Service list response structure:', {
            hasData: !!serviceData,
            hasCacheKey: !!(serviceData && serviceData.cache_key),
            hasStorageKey: !!(serviceData && serviceData.storage_key),
            cacheKey: serviceData?.cache_key,
            storageKey: serviceData?.storage_key,
            responseKeys: serviceData ? Object.keys(serviceData) : []
          });
        } else {
          logger.warn('⚠️ Failed to load service list before booking:', serviceResponse.reason);
        }
        
        // Refresh session data to get newly stored cache keys
        const updatedSession = this.getSessionData();
        session.seatAvailabilityCacheKey = updatedSession.seatAvailabilityCacheKey;
        session.serviceListCacheKey = updatedSession.serviceListCacheKey;
        
        logger.info('🔍 DEBUG: After fallback loading, updated cache keys:', {
          seatCacheKey: session.seatAvailabilityCacheKey,
          serviceCacheKey: session.serviceListCacheKey,
        });
        
      } catch (error) {
        logger.warn('⚠️ Failed to preload seat/service data before booking:', error);
        // Continue with booking anyway - backend can handle missing seat/service data
      }
    }
    
    const payload = {
      flight_offer: flightOffer,
      passengers,
      payment,
      contact_info: contactInfo,
      session_id: session.sessionId,
      extras,
      // Include cache keys for seat and service retrieval by backend
      seat_availability_cache_key: session.seatAvailabilityCacheKey,
      service_list_cache_key: session.serviceListCacheKey,
    };
    
    logger.info('🔍 Creating booking with unified manager:', {
      sessionId: session.sessionId,
      hasFlightOffer: !!flightOffer,
      hasPassengers: passengers.length > 0,
      hasExtras: !!extras,
      seatCacheKey: session.seatAvailabilityCacheKey,
      serviceCacheKey: session.serviceListCacheKey,
    });
    
    // 🔍 DEBUG: Log exact payload being sent to backend
    logger.info('🚀 PAYLOAD DEBUG - Exact data being sent to /api/verteil/order-create:', {
      seat_availability_cache_key: payload.seat_availability_cache_key,
      service_list_cache_key: payload.service_list_cache_key,
      session_id: payload.session_id,
      payloadKeys: Object.keys(payload)
    });
    
    // 🚨 CRITICAL CHECK: Verify cache keys are not null/undefined before sending
    if (!payload.seat_availability_cache_key || !payload.service_list_cache_key) {
      logger.error('🚨 CRITICAL ERROR: Cache keys are still null before sending to backend!', {
        seat_availability_cache_key: payload.seat_availability_cache_key,
        service_list_cache_key: payload.service_list_cache_key,
        sessionStorage_contents: {
          seat_key: sessionStorage.getItem('seat_availability_cache_key'),
          service_key: sessionStorage.getItem('service_list_cache_key'),
          all_keys: Object.keys(sessionStorage).filter(k => k.includes('cache') || k.includes('storage'))
        }
      });
      
      // 🔥 LAST RESORT: Try to get cache keys directly from sessionStorage one more time
      const lastResortSeatKey = sessionStorage.getItem('seat_availability_cache_key');
      const lastResortServiceKey = sessionStorage.getItem('service_list_cache_key');
      
      if (lastResortSeatKey) {
        payload.seat_availability_cache_key = lastResortSeatKey;
        logger.info('✅ RECOVERED seat cache key from sessionStorage:', lastResortSeatKey);
      }
      if (lastResortServiceKey) {
        payload.service_list_cache_key = lastResortServiceKey;
        logger.info('✅ RECOVERED service cache key from sessionStorage:', lastResortServiceKey);
      }
    }
    
    // 🔍 FINAL DEBUG: Log the exact JSON that will be sent
    logger.error('🚨 FINAL PAYLOAD BEFORE SENDING:', {
      payloadStringified: JSON.stringify(payload),
      payloadKeys: Object.keys(payload),
      seatCacheKey: payload.seat_availability_cache_key,
      serviceCacheKey: payload.service_list_cache_key
    });
    
    return this.makeRequest('/api/verteil/order-create', payload);
  }
  
  /**
   * Proactively load seat availability for one-way flights (fire and forget)
   */
  private async loadSeatAvailabilityProactive(flightPriceResponse: ApiResponse): Promise<void> {
    try {
      const cacheKey = this.extractCacheKey(flightPriceResponse);
      if (!cacheKey) {
        logger.warn('⚠️ Cannot load seat availability proactively - no cache key');
        return;
      }
      
      const requestKey = `seat_availability_${cacheKey}`;
      
      // Skip if already being loaded
      if (this.pendingRequests.has(requestKey)) {
        return;
      }
      
      const payload = {
        flight_price_cache_key: cacheKey
        // No segment_key needed for one-way flights
      };
      
      const response = await this.makeRequest('/api/verteil/seat-availability', payload);
      
      // 🚀 CRITICAL FIX: Store cache keys in sessionStorage during proactive loading
      if (response.storage_key) {
        sessionStorage.setItem('seat_availability_storage_key', response.storage_key);
        logger.info('✅ PROACTIVE: Stored seat_availability_storage_key:', response.storage_key);
      }
      if (response.cache_key) {
        sessionStorage.setItem('seat_availability_cache_key', response.cache_key);
        logger.info('✅ PROACTIVE: Stored seat_availability_cache_key:', response.cache_key);
      }
      
      // Store in cache for immediate use (one-way flights)
      this.cache.set(requestKey, { data: response, timestamp: Date.now() });
      
      logger.info('✅ Proactive seat availability loaded for one-way flight');
    } catch (error) {
      logger.warn('⚠️ Proactive seat availability loading failed:', error);
      // Don't throw - this is fire-and-forget
    }
  }
  
  /**
   * Proactively load service list (fire and forget)
   */
  private async loadServiceListProactive(flightPriceResponse: ApiResponse): Promise<void> {
    try {
      const cacheKey = this.extractCacheKey(flightPriceResponse);
      if (!cacheKey) {
        logger.warn('⚠️ Cannot load service list proactively - no cache key');
        return;
      }
      
      const requestKey = `service_list_${cacheKey}`;
      
      // Skip if already being loaded
      if (this.pendingRequests.has(requestKey)) {
        return;
      }
      
      const payload = {
        flight_price_cache_key: cacheKey
      };
      
      const response = await this.makeRequest('/api/verteil/service-list', payload);
      
      // 🚀 CRITICAL FIX: Store cache keys in sessionStorage during proactive loading
      if (response.storage_key) {
        sessionStorage.setItem('service_list_storage_key', response.storage_key);
        logger.info('✅ PROACTIVE: Stored service_list_storage_key:', response.storage_key);
      }
      if (response.cache_key) {
        sessionStorage.setItem('service_list_cache_key', response.cache_key);
        logger.info('✅ PROACTIVE: Stored service_list_cache_key:', response.cache_key);
      }
      
      // Store in cache for immediate use
      this.cache.set(requestKey, { data: response, timestamp: Date.now() });
      
      logger.info('✅ Proactive service list loaded and cached');
    } catch (error) {
      logger.warn('⚠️ Proactive service list loading failed:', error);
      // Don't throw - this is fire-and-forget
    }
  }
  
  /**
   * Clear all caches and pending requests
   */
  clearCache(): void {
    this.cache.clear();
    this.pendingRequests.clear();
    logger.info('🗑️ Cleared unified API manager cache');
  }
  
  
  /**
   * Get debug information
   */
  getDebugInfo() {
    return {
      pendingRequests: Array.from(this.pendingRequests.keys()),
      cacheEntries: Array.from(this.cache.keys()),
      sessionData: sessionManager.getSessionDebugInfo(),
    };
  }
}

// Export singleton instance
export const unifiedApiManager = new UnifiedApiManager();