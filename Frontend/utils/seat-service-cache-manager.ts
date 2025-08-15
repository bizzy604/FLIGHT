import { api } from "@/utils/api-client"
import { logger } from "@/utils/logger"

interface SeatAvailabilityData {
  flights: Array<{
    cabin: Array<{
      seatDisplay: {
        columns: Array<{
          value: string
          position: string
        }>
        rows: {
          first: number
          last: number
          upperDeckInd: boolean
        }
        component: Array<{
          locations: {
            location: Array<{
              row: { position: number }
              column: { position: string }
            }>
          }
          type: { code: string }
        }>
      }
    }>
  }>
  dataLists?: {
    seatList?: {
      seats: Array<{
        objectKey: string
        location: {
          column: string
          row: { number: { value: string } }
          characteristics?: {
            characteristic: Array<{
              code: string
              remarks?: {
                remark: Array<{ value: string }>
              }
            }>
          }
        }
        price?: {
          total?: {
            value: number
            code: string
          }
        }
        availability?: 'available' | 'occupied' | 'unavailable'
      }>
    }
  }
}

interface ServiceListData {
  services: {
    service: Array<{
      objectKey: string
      serviceId: {
        objectKey: string
        value: string
        owner: string
      }
      name: { value: string }
      descriptions?: {
        description: Array<{
          text: { value: string }
        }>
      }
      price: Array<{
        total: {
          value: number
          code: string
        }
      }>
      associations: Array<{
        traveler?: {
          travelerReferences: string[]
        }
        flight?: {
          originDestinationReferencesOrSegmentReferences: Array<{
            segmentReferences: {
              value: string[]
            }
          }>
        }
      }>
      pricedInd: boolean
      category?: string
      bookingInstructions?: {
        ssrCode?: string[]
        method?: string
      }
    }>
  }
  shoppingResponseId: {
    responseId: { value: string }
  }
}

interface CachedData {
  seatAvailability?: SeatAvailabilityData | null
  serviceList?: ServiceListData | null
  timestamp: number
  flightPriceResponseId: string
  error?: {
    seatAvailability?: string
    serviceList?: string
  }
}

class SeatServiceCacheManager {
  private cache: Map<string, CachedData> = new Map()
  private readonly CACHE_EXPIRY = 30 * 60 * 1000 // 30 minutes
  private loadingPromises: Map<string, Promise<void>> = new Map()
  private globalLoadingState: Map<string, boolean> = new Map() // Track global loading to prevent concurrent calls

  /**
   * Generate cache key from flight price response
   * 🚀 ROBUST CACHE KEY GENERATION - Uses flight_price_cache_key as primary source
   */
  private generateCacheKey(flightPriceResponse: any): string {
    // 🎯 PRIMARY METHOD: Use flight_price_cache_key directly for seat/service cache keys
    // This ensures consistency with backend cache keys and prevents multiple API calls
    
    let primaryCacheKey = null
    
    // Method 1: From metadata.flight_price_cache_key (preferred)
    if (flightPriceResponse?.metadata?.flight_price_cache_key) {
      primaryCacheKey = flightPriceResponse.metadata.flight_price_cache_key
    }
    // Method 2: From top-level flight_price_cache_key (backend guarantee)
    else if (flightPriceResponse?.flight_price_cache_key) {
      primaryCacheKey = flightPriceResponse.flight_price_cache_key
    }
    // Method 3: From data.metadata.flight_price_cache_key (nested structure)
    else if (flightPriceResponse?.data?.metadata?.flight_price_cache_key) {
      primaryCacheKey = flightPriceResponse.data.metadata.flight_price_cache_key
    }
    
    if (primaryCacheKey) {
      // Use the flight_price_cache_key as base for seat/service cache keys
      // This ensures perfect consistency with backend cache management
      const seatServiceCacheKey = `seat_service_${primaryCacheKey}`
      logger.info(`🔑 Generated cache key from flight_price_cache_key: ${seatServiceCacheKey}`)
      return seatServiceCacheKey
    }
    
    // 🚨 FALLBACK METHOD: Extract from available metadata (only if primary method fails)
    const offerId = flightPriceResponse?.offer_id || 
                    flightPriceResponse?.id || 
                    flightPriceResponse?.original_offer_id ||
                    'unknown'
    
    let shoppingResponseId = 'unknown'
    
    // Try to extract shopping response ID from various sources
    if (flightPriceResponse?.metadata?.shopping_response_id) {
      shoppingResponseId = flightPriceResponse.metadata.shopping_response_id
    } else if (flightPriceResponse?.metadata?.request_id) {
      shoppingResponseId = flightPriceResponse.metadata.request_id
    } else if (flightPriceResponse?.request_id) {
      shoppingResponseId = flightPriceResponse.request_id
    }
    
    const fallbackCacheKey = `${shoppingResponseId}_${offerId}`
    
    logger.warn(`⚠️ Using fallback cache key generation: ${fallbackCacheKey}`)
    logger.warn(`⚠️ flight_price_cache_key not found in:`, {
      metadata_keys: Object.keys(flightPriceResponse?.metadata || {}),
      top_level_keys: Object.keys(flightPriceResponse || {}).filter(k => k.includes('cache')),
      has_data: !!flightPriceResponse?.data
    })
    
    return fallbackCacheKey
  }

  /**
   * Check if cached data is still valid
   */
  private isValidCache(cached: CachedData): boolean {
    return (Date.now() - cached.timestamp) < this.CACHE_EXPIRY
  }

  /**
   * Pre-load seat availability and service list data after flight price response
   * 🚀 ENHANCED: Prevents concurrent API calls from multiple component instances
   */
  async preloadData(flightPriceResponse: any): Promise<void> {
    const cacheKey = this.generateCacheKey(flightPriceResponse)
    
    // 🛡️ GLOBAL LOADING GUARD: Prevent multiple component instances from making concurrent calls
    if (this.globalLoadingState.get(cacheKey)) {
      logger.info(`🛡️ Global loading guard: ${cacheKey} already being loaded by another component instance`)
      
      // Wait for existing loading promise if available
      if (this.loadingPromises.has(cacheKey)) {
        logger.info(`🔄 Waiting for existing loading promise for ${cacheKey}`)
        return this.loadingPromises.get(cacheKey)!
      }
      
      // If no promise but global loading state is true, wait briefly and check cache
      await new Promise(resolve => setTimeout(resolve, 500))
      return
    }
    
    // Check if we already have valid cached data
    const existingCache = this.cache.get(cacheKey)
    if (existingCache && this.isValidCache(existingCache)) {
      logger.info(`✅ Using existing valid cache for ${cacheKey}`)
      return
    }

    // Check if we're already loading this data (additional safety check)
    if (this.loadingPromises.has(cacheKey)) {
      logger.info(`🔄 Already loading seat/service data for ${cacheKey}, waiting...`)
      return this.loadingPromises.get(cacheKey)!
    }

    logger.info(`🚀 Pre-loading seat availability and service list for flight... (Cache key: ${cacheKey})`)

    // 🔒 SET GLOBAL LOADING STATE
    this.globalLoadingState.set(cacheKey, true)

    // Create loading promise
    const loadingPromise = this.performDataLoad(cacheKey, flightPriceResponse)
    this.loadingPromises.set(cacheKey, loadingPromise)

    try {
      await loadingPromise
      logger.info(`✅ Successfully completed preload for ${cacheKey}`)
    } catch (error) {
      logger.error(`❌ Failed to preload data for ${cacheKey}:`, error)
      throw error
    } finally {
      // 🔓 CLEAR GLOBAL LOADING STATE
      this.globalLoadingState.delete(cacheKey)
      this.loadingPromises.delete(cacheKey)
    }
  }

  /**
   * Perform the actual data loading
   */
  private async performDataLoad(cacheKey: string, flightPriceResponse: any): Promise<void> {
    const cachedData: CachedData = {
      timestamp: Date.now(),
      flightPriceResponseId: cacheKey,
      error: {}
    }

    // Load seat availability and service list in parallel
    const [seatResult, serviceResult] = await Promise.allSettled([
      this.loadSeatAvailability(flightPriceResponse),
      this.loadServiceList(flightPriceResponse)
    ])

    // Process seat availability result
    if (seatResult.status === 'fulfilled') {
      cachedData.seatAvailability = seatResult.value
      logger.info(`✅ Seat availability data loaded successfully`)
    } else {
      cachedData.seatAvailability = null
      cachedData.error!.seatAvailability = seatResult.reason?.message || 'Failed to load seat availability'
      logger.error(`❌ Failed to load seat availability:`, seatResult.reason)
    }

    // Process service list result
    if (serviceResult.status === 'fulfilled') {
      cachedData.serviceList = serviceResult.value
      logger.info(`✅ Service list data loaded successfully`)
    } else {
      cachedData.serviceList = null
      cachedData.error!.serviceList = serviceResult.reason?.message || 'Failed to load service list'
      logger.error(`❌ Failed to load service list:`, serviceResult.reason)
    }

    // Store in cache
    this.cache.set(cacheKey, cachedData)
    logger.info(`💾 Cached seat/service data for key: ${cacheKey}`)
  }

  /**
   * Load seat availability data
   */
  private async loadSeatAvailability(flightPriceResponse: any): Promise<SeatAvailabilityData> {
    try {
      // Check cache first
      const cacheResponse = await api.checkSeatAvailabilityCache(flightPriceResponse)
      
      if (cacheResponse.data?.cache_hit) {
        logger.info("🎯 Seat availability cache hit")
        return cacheResponse.data.data
      } else {
        logger.info("🔄 Seat availability cache miss, fetching from API")
        const response = await api.getSeatAvailability(flightPriceResponse)
        return response.data
      }
    } catch (error) {
      logger.error("❌ Error loading seat availability:", error)
      throw error
    }
  }

  /**
   * Load service list data
   */
  private async loadServiceList(flightPriceResponse: any): Promise<ServiceListData> {
    try {
      // Check cache first
      const cacheResponse = await api.checkServiceListCache(flightPriceResponse)
      
      if (cacheResponse.data?.cache_hit) {
        logger.info("🎯 Service list cache hit")
        return cacheResponse.data.data
      } else {
        logger.info("🔄 Service list cache miss, fetching from API")
        const response = await api.getServiceList(flightPriceResponse)
        return response.data
      }
    } catch (error) {
      logger.error("❌ Error loading service list:", error)
      throw error
    }
  }

  /**
   * Get cached seat availability data
   */
  getCachedSeatAvailability(flightPriceResponse: any): {
    data: SeatAvailabilityData | null
    isLoading: boolean
    error?: string
  } {
    const cacheKey = this.generateCacheKey(flightPriceResponse)
    const cached = this.cache.get(cacheKey)
    const isLoading = this.loadingPromises.has(cacheKey)

    if (!cached) {
      return { data: null, isLoading }
    }

    if (!this.isValidCache(cached)) {
      logger.warn(`⚠️ Cache expired for ${cacheKey}, will need to reload`)
      return { data: null, isLoading: false }
    }

    return {
      data: cached.seatAvailability || null,
      isLoading,
      error: cached.error?.seatAvailability
    }
  }

  /**
   * Get cached service list data
   */
  getCachedServiceList(flightPriceResponse: any): {
    data: ServiceListData | null
    isLoading: boolean
    error?: string
  } {
    const cacheKey = this.generateCacheKey(flightPriceResponse)
    const cached = this.cache.get(cacheKey)
    const isLoading = this.loadingPromises.has(cacheKey)

    if (!cached) {
      return { data: null, isLoading }
    }

    if (!this.isValidCache(cached)) {
      logger.warn(`⚠️ Cache expired for ${cacheKey}, will need to reload`)
      return { data: null, isLoading: false }
    }

    return {
      data: cached.serviceList || null,
      isLoading,
      error: cached.error?.serviceList
    }
  }

  /**
   * Clear expired cache entries
   */
  cleanupExpiredCache(): void {
    const now = Date.now()
    let cleanedCount = 0

    for (const [key, cached] of this.cache.entries()) {
      if ((now - cached.timestamp) >= this.CACHE_EXPIRY) {
        this.cache.delete(key)
        cleanedCount++
      }
    }

    if (cleanedCount > 0) {
      logger.info(`🧹 Cleaned up ${cleanedCount} expired cache entries`)
    }
  }

  /**
   * Clear all cache data
   */
  clearCache(): void {
    this.cache.clear()
    this.loadingPromises.clear()
    logger.info(`🗑️ Cleared all seat/service cache data`)
  }

  /**
   * Get cache status for debugging
   * 🚀 ENHANCED: Include global loading state information
   */
  getCacheStatus(): {
    totalEntries: number
    loadingEntries: number
    expiredEntries: number
    globalLoadingStates: number
    cacheKeys: string[]
    loadingKeys: string[]
    globalLoadingKeys: string[]
  } {
    const now = Date.now()
    let expiredCount = 0

    for (const cached of this.cache.values()) {
      if ((now - cached.timestamp) >= this.CACHE_EXPIRY) {
        expiredCount++
      }
    }

    return {
      totalEntries: this.cache.size,
      loadingEntries: this.loadingPromises.size,
      expiredEntries: expiredCount,
      globalLoadingStates: this.globalLoadingState.size,
      cacheKeys: Array.from(this.cache.keys()),
      loadingKeys: Array.from(this.loadingPromises.keys()),
      globalLoadingKeys: Array.from(this.globalLoadingState.keys())
    }
  }
}

// Export singleton instance
export const seatServiceCache = new SeatServiceCacheManager()

// Cleanup expired cache every 10 minutes
if (typeof window !== 'undefined') {
  setInterval(() => {
    seatServiceCache.cleanupExpiredCache()
  }, 10 * 60 * 1000)
}