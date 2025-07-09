/**
 * React Hook for Navigation Cache Management
 * 
 * Provides easy-to-use React hooks for managing navigation state and cache validation
 */

import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { navigationCacheManager, NavigationState } from '@/utils/navigation-cache-manager';
import { logger } from '@/utils/logger';

export interface UseNavigationCacheOptions {
  page: NavigationState['currentPage'];
  flightId?: string;
  searchParams?: Record<string, string>;
  onCacheHit?: (data: any) => void;
  onCacheMiss?: () => void;
}

/**
 * Hook for managing navigation cache state
 */
export function useNavigationCache(options: UseNavigationCacheOptions) {
  const { page, flightId, searchParams, onCacheHit, onCacheMiss } = options;

  // Update navigation state when component mounts or parameters change
  useEffect(() => {
    navigationCacheManager.updateNavigationState(page, {
      flightId,
      searchParams
    });
  }, [page, flightId, JSON.stringify(searchParams)]);

  /**
   * Check if current navigation should use cached data
   */
  const shouldUseCache = useCallback(async (): Promise<boolean> => {
    try {
      // Check if we should skip API call based on navigation context
      if (navigationCacheManager.shouldSkipApiCall(page)) {
        logger.info(`[NavigationCache] ⚡ Using cache for ${page} page`);
        return true;
      }

      // Validate cache based on page type
      if (page === 'search' && searchParams) {
        const validation = await navigationCacheManager.validateFlightSearchCache(searchParams);
        if (validation.isValid) {
          onCacheHit?.(validation.data);
          return true;
        } else {
          logger.info(`[NavigationCache] Cache invalid for search: ${validation.reason}`);
        }
      }

      if (page === 'details' && flightId) {
        const validation = await navigationCacheManager.validateFlightPriceCache(flightId);
        if (validation.isValid) {
          onCacheHit?.(validation.data);
          return true;
        } else {
          logger.info(`[NavigationCache] Cache invalid for details: ${validation.reason}`);
        }
      }

      onCacheMiss?.();
      return false;

    } catch (error) {
      logger.error('[NavigationCache] Error checking cache:', error);
      onCacheMiss?.();
      return false;
    }
  }, [page, flightId, searchParams, onCacheHit, onCacheMiss]);

  /**
   * Get current navigation state
   */
  const getNavigationState = useCallback(() => {
    return navigationCacheManager.getNavigationState();
  }, []);

  /**
   * Check if current navigation is a back navigation
   */
  const isBackNavigation = useCallback(() => {
    return navigationCacheManager.isBackNavigation(page);
  }, [page]);

  /**
   * Clear navigation cache
   */
  const clearCache = useCallback(() => {
    navigationCacheManager.clearCache();
  }, []);

  /**
   * Get cache status for debugging
   */
  const getCacheStatus = useCallback(() => {
    return navigationCacheManager.getCacheStatus();
  }, []);

  return {
    shouldUseCache,
    getNavigationState,
    isBackNavigation,
    clearCache,
    getCacheStatus
  };
}

/**
 * Hook for flight search page navigation cache
 */
export function useFlightSearchCache(searchParams: Record<string, string>) {
  return useNavigationCache({
    page: 'search',
    searchParams
  });
}

/**
 * Hook for flight details page navigation cache
 */
export function useFlightDetailsCache(flightId: string) {
  return useNavigationCache({
    page: 'details',
    flightId
  });
}

/**
 * Hook for payment page navigation cache
 */
export function usePaymentCache(flightId: string) {
  return useNavigationCache({
    page: 'payment',
    flightId
  });
}

/**
 * Hook for confirmation page navigation cache
 */
export function useConfirmationCache() {
  return useNavigationCache({
    page: 'confirmation'
  });
}

/**
 * Hook to detect and handle back navigation with smart caching
 */
export function useSmartBackNavigation() {
  const router = useRouter();

  const handleBackNavigation = useCallback((targetPage: string, fallbackUrl?: string) => {
    const state = navigationCacheManager.getNavigationState();
    
    if (state && navigationCacheManager.isBackNavigation(targetPage as NavigationState['currentPage'])) {
      // We're going back, data should be cached
      logger.info(`[NavigationCache] 🔙 Smart back navigation to ${targetPage}`);
      
      if (fallbackUrl) {
        router.push(fallbackUrl);
      } else {
        router.back();
      }
    } else {
      // New navigation, clear cache if needed
      if (targetPage === 'search') {
        navigationCacheManager.clearCache();
      }
      
      if (fallbackUrl) {
        router.push(fallbackUrl);
      } else {
        router.back();
      }
    }
  }, [router]);

  return { handleBackNavigation };
}
