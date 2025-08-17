import { logger } from './logger';

class SessionManager {
  private static instance: SessionManager;
  
  private constructor() {}
  
  static getInstance(): SessionManager {
    if (!SessionManager.instance) {
      SessionManager.instance = new SessionManager();
    }
    return SessionManager.instance;
  }
  
  /**
   * KISS Principle: Simple session ID management
   */
  getOrCreateSessionId(): string {
    let sessionId = localStorage.getItem('flight_session_id');
    
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('flight_session_id', sessionId);
      logger.info('✅ Created new flight session ID:', sessionId);
    }
    
    return sessionId;
  }
  
  /**
   * Get current session ID without creating new one
   */
  getCurrentSessionId(): string | null {
    return localStorage.getItem('flight_session_id');
  }
  
  /**
   * Clear session data
   */
  clearSession(): void {
    localStorage.removeItem('flight_session_id');
    sessionStorage.removeItem('flight_price_cache_key');
    sessionStorage.removeItem('seat_availability_storage_key');
    sessionStorage.removeItem('service_list_storage_key');
    sessionStorage.removeItem('flightPriceResponseForBooking');
    sessionStorage.removeItem('flightPriceMetadata');
    
    logger.info('🗑️ Cleared flight session data');
  }
  
  /**
   * Get all session data for debugging
   */
  getSessionDebugInfo() {
    return {
      sessionId: this.getCurrentSessionId(),
      flightPriceCacheKey: sessionStorage.getItem('flight_price_cache_key'),
      seatStorageKey: sessionStorage.getItem('seat_availability_storage_key'),
      serviceStorageKey: sessionStorage.getItem('service_list_storage_key'),
      hasFlightData: !!sessionStorage.getItem('flightPriceResponseForBooking'),
      hasMetadata: !!sessionStorage.getItem('flightPriceMetadata'),
    };
  }
}

// Export singleton instance
export const sessionManager = SessionManager.getInstance();