/**
 * Navigation Cache Manager
 * 
 * Manages intelligent caching and navigation state to prevent unnecessary API calls
 * when users navigate between flight search, details, payment, and confirmation pages.
 */

import { logger } from './logger';
import { redisFlightStorage } from './redis-flight-storage';

export interface NavigationState {
  currentPage: 'search' | 'details' | 'payment' | 'confirmation';
  lastPage?: string;
  searchParams?: Record<string, string>;
  flightId?: string;
  sessionId?: string;
  timestamp: number;
}

export interface CacheValidationResult {
  isValid: boolean;
  reason?: string;
  data?: any;
}

class NavigationCacheManager {
  private static instance: NavigationCacheManager;
  private navigationState: NavigationState | null = null;
  private readonly CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

  static getInstance(): NavigationCacheManager {
    if (!NavigationCacheManager.instance) {
      NavigationCacheManager.instance = new NavigationCacheManager();
    }
    return NavigationCacheManager.instance;
  }

  /**
   * Update navigation state when user moves between pages
   */
  updateNavigationState(page: NavigationState['currentPage'], params?: {
    searchParams?: Record<string, string>;
    flightId?: string;
  }) {
    const previousState = this.navigationState;
    
    this.navigationState = {
      currentPage: page,
      lastPage: previousState?.currentPage,
      searchParams: params?.searchParams || previousState?.searchParams,
      flightId: params?.flightId || previousState?.flightId,
      sessionId: localStorage.getItem('flight_session_id') || undefined,
      timestamp: Date.now()
    };

    // Store in sessionStorage for persistence across page reloads
    sessionStorage.setItem('navigation_state', JSON.stringify(this.navigationState));
    
    logger.info(`[NavigationCache] Updated state: ${previousState?.currentPage} → ${page}`, {
      flightId: this.navigationState.flightId,
      sessionId: this.navigationState.sessionId
    });
  }

  /**
   * Get current navigation state
   */
  getNavigationState(): NavigationState | null {
    if (!this.navigationState) {
      // Try to restore from sessionStorage
      const stored = sessionStorage.getItem('navigation_state');
      if (stored) {
        try {
          this.navigationState = JSON.parse(stored);
        } catch (e) {
          logger.warn('[NavigationCache] Failed to parse stored navigation state');
        }
      }
    }
    return this.navigationState;
  }

  /**
   * Check if we're navigating back to a previous page
   */
  isBackNavigation(currentPage: NavigationState['currentPage']): boolean {
    const state = this.getNavigationState();
    if (!state) return false;

    const navigationFlow = ['search', 'details', 'payment', 'confirmation'];
    const currentIndex = navigationFlow.indexOf(currentPage);
    const lastIndex = navigationFlow.indexOf(state.currentPage);

    return currentIndex < lastIndex;
  }

  /**
   * Validate if cached flight search data is still valid for current search parameters
   */
  async validateFlightSearchCache(searchParams: Record<string, string>): Promise<CacheValidationResult> {
    try {
      const state = this.getNavigationState();
      
      // Check if we have cached search data
      const cachedResult = await redisFlightStorage.getFlightSearch();
      
      if (!cachedResult.success || !cachedResult.data) {
        return { isValid: false, reason: 'No cached data found' };
      }

      const cachedData = cachedResult.data;
      const cachedParams = cachedData.searchParams;

      // Check if search parameters match
      const criticalParams = ['origin', 'destination', 'departDate', 'returnDate', 'tripType', 'adults', 'children', 'infants', 'cabinClass'];
      
      for (const param of criticalParams) {
        if (searchParams[param] !== cachedParams[param]) {
          return { 
            isValid: false, 
            reason: `Parameter mismatch: ${param} (${searchParams[param]} vs ${cachedParams[param]})` 
          };
        }
      }

      // Check if data is still within expiration time
      const now = Date.now();
      if (cachedData.expiresAt && now > cachedData.expiresAt) {
        return { isValid: false, reason: 'Cache expired' };
      }

      // Check if we're in a back navigation scenario
      if (this.isBackNavigation('search') && state?.searchParams) {
        const stateParamsMatch = criticalParams.every(param => 
          searchParams[param] === state.searchParams![param]
        );
        
        if (stateParamsMatch) {
          logger.info('[NavigationCache] ✅ Back navigation detected, using cached search data');
          return { isValid: true, data: cachedData };
        }
      }

      return { isValid: true, data: cachedData };

    } catch (error) {
      logger.error('[NavigationCache] Error validating flight search cache:', error);
      return { isValid: false, reason: 'Cache validation error' };
    }
  }

  /**
   * Validate if cached flight price data is still valid
   */
  async validateFlightPriceCache(flightId: string): Promise<CacheValidationResult> {
    try {
      const state = this.getNavigationState();
      
      // Check if we have cached price data
      const cachedResult = await redisFlightStorage.getFlightPrice();
      
      if (!cachedResult.success || !cachedResult.data) {
        return { isValid: false, reason: 'No cached price data found' };
      }

      const cachedData = cachedResult.data;

      // Check if flight ID matches
      if (cachedData.flightId !== flightId) {
        return { 
          isValid: false, 
          reason: `Flight ID mismatch: ${flightId} vs ${cachedData.flightId}` 
        };
      }

      // Check if data is still within expiration time
      const now = Date.now();
      if (cachedData.expiresAt && now > cachedData.expiresAt) {
        return { isValid: false, reason: 'Price cache expired' };
      }

      // If we're navigating back from payment/confirmation, definitely use cache
      if (this.isBackNavigation('details') && state?.flightId === flightId) {
        logger.info('[NavigationCache] ✅ Back navigation detected, using cached price data');
        return { isValid: true, data: cachedData };
      }

      return { isValid: true, data: cachedData };

    } catch (error) {
      logger.error('[NavigationCache] Error validating flight price cache:', error);
      return { isValid: false, reason: 'Price cache validation error' };
    }
  }

  /**
   * Check if we should skip API call based on navigation context
   */
  shouldSkipApiCall(page: NavigationState['currentPage'], params?: any): boolean {
    const state = this.getNavigationState();
    
    if (!state) return false;

    // Always skip if we're navigating back and have valid session
    if (this.isBackNavigation(page) && state.sessionId) {
      const sessionAge = Date.now() - state.timestamp;
      if (sessionAge < this.CACHE_DURATION) {
        logger.info(`[NavigationCache] ⚡ Skipping API call for back navigation to ${page}`);
        return true;
      }
    }

    return false;
  }

  /**
   * Clear navigation cache (useful for new searches)
   */
  clearCache() {
    this.navigationState = null;
    sessionStorage.removeItem('navigation_state');
    logger.info('[NavigationCache] Cache cleared');
  }

  /**
   * Get cache status for debugging
   */
  getCacheStatus() {
    const state = this.getNavigationState();
    return {
      hasNavigationState: !!state,
      currentPage: state?.currentPage,
      lastPage: state?.lastPage,
      sessionId: state?.sessionId,
      age: state ? Date.now() - state.timestamp : 0,
      isWithinCacheDuration: state ? (Date.now() - state.timestamp) < this.CACHE_DURATION : false
    };
  }
}

export const navigationCacheManager = NavigationCacheManager.getInstance();
