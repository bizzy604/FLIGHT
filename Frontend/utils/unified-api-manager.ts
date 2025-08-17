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
    return {
      sessionId: sessionManager.getOrCreateSessionId(),
      flightPriceCacheKey: sessionStorage.getItem('flight_price_cache_key'),
      seatAvailabilityStorageKey: sessionStorage.getItem('seat_availability_storage_key'),
      serviceListStorageKey: sessionStorage.getItem('service_list_storage_key'),
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
      return cached.data;
    }
    
    return this.executeWithDeduplication(requestKey, async () => {
      // BYPASS cache check - go directly to API (eliminates duplicate calls)
      logger.info('🚀 Fetching seat availability directly (no cache check)');
      const response = await this.makeRequest('/api/verteil/seat-availability', {
        flight_price_cache_key: cacheKey
        // No segment_key needed for one-way flights
      });
      
      // Store storage key for future use
      if (response.storage_key) {
        sessionStorage.setItem('seat_availability_storage_key', response.storage_key);
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
      return cached.data;
    }
    
    return this.executeWithDeduplication(requestKey, async () => {
      // BYPASS cache check - go directly to API (eliminates duplicate calls)
      logger.info('🚀 Fetching service list directly (no cache check)');
      const response = await this.makeRequest('/api/verteil/service-list', {
        flight_price_cache_key: cacheKey,
      });
      
      // Store storage key for future use
      if (response.storage_key) {
        sessionStorage.setItem('service_list_storage_key', response.storage_key);
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
    
    const payload = {
      flight_offer: flightOffer,
      passengers,
      payment,
      contact_info: contactInfo,
      session_id: session.sessionId,
      extras,
    };
    
    logger.info('🔍 Creating booking with unified manager:', {
      sessionId: session.sessionId,
      hasFlightOffer: !!flightOffer,
      hasPassengers: passengers.length > 0,
      hasExtras: !!extras,
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