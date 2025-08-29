import { api } from "@/utils/api-client"
import { simpleApiManager } from "@/utils/simple-api-manager"
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
  // 🚀 NEW: Store actual backend storage keys
  storageKeys?: {
    seatAvailability?: string
    serviceList?: string
  }
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
   * Generate cache key from flight price response (SIMPLIFIED)
   * Unified API manager handles complex extraction internally
   */
  private generateCacheKey(flightPriceResponse: any): string {
    // Use offer_id + timestamp for local cache key
    const offerId = flightPriceResponse?.offer_id || flightPriceResponse?.original_offer_id || 'unknown'
    const timestamp = flightPriceResponse?.metadata?.timestamp || Date.now()
    
    const localCacheKey = `${offerId}_${Math.floor(timestamp / 1000)}`
    logger.info(`🔑 Generated local cache key: ${localCacheKey}`)
    
    return localCacheKey
  }

  /**
   * Simple hash function to match backend behavior
   */
  private generateSimpleHash(str: string): string {
    let hash = 0
    if (str.length === 0) return hash.toString()
    
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16) // Return as hex string
  }

  /**
   * Check if cached data is still valid
   */
  private isValidCache(cached: CachedData): boolean {
    return (Date.now() - cached.timestamp) < this.CACHE_EXPIRY
  }

  /**
   * Pre-load seat availability and service list data
   * This method triggers the actual data loading via the unified API manager
   */
  async preloadData(flightPriceResponse: any): Promise<void> {
    const cacheKey = this.generateCacheKey(flightPriceResponse)
    
    logger.info(`🚀 Preload requested for ${cacheKey} - Loading seat and service data`)
    
    try {
      // Load both seat availability and service list in parallel
      const [seatResult, serviceResult] = await Promise.allSettled([
        this.loadSeatAvailability(flightPriceResponse),
        this.loadServiceList(flightPriceResponse)
      ])
      
      // Process results
      if (seatResult.status === 'fulfilled') {
        logger.info('✅ Seat availability preloaded successfully')
      } else {
        logger.warn('⚠️ Seat availability preload failed:', seatResult.reason)
      }
      
      if (serviceResult.status === 'fulfilled') {
        logger.info('✅ Service list preloaded successfully')
      } else {
        logger.warn('⚠️ Service list preload failed:', serviceResult.reason)
      }
      
      logger.info(`✅ Preload completed for ${cacheKey}`)
    } catch (error) {
      logger.error('❌ Error during preload:', error)
      throw error
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
   * Load seat availability data using simple API manager
   */
  private async loadSeatAvailability(flightPriceResponse: any): Promise<SeatAvailabilityData> {
    try {
      logger.info("🚀 Loading seat availability via simple API manager")
      
      const response = await simpleApiManager.getSeatAvailability(flightPriceResponse)
      
      if (response.cache_hit) {
        logger.info("🎯 Seat availability cache hit via simple manager")
      } else {
        logger.info("🔄 Seat availability loaded fresh via simple manager")
      }
      
      return response.data
    } catch (error) {
      logger.error("❌ Error loading seat availability via simple manager:", error)
      throw error
    }
  }

  /**
   * Load service list data using simple API manager
   */
  private async loadServiceList(flightPriceResponse: any): Promise<ServiceListData> {
    try {
      logger.info("🚀 Loading service list via simple API manager")
      
      const response = await simpleApiManager.getServiceList(flightPriceResponse)
      
      if (response.cache_hit) {
        logger.info("🎯 Service list cache hit via simple manager")
      } else {
        logger.info("🔄 Service list loaded fresh via simple manager")
      }
      
      return response.data
    } catch (error) {
      logger.error("❌ Error loading service list via simple manager:", error)
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

    for (const [key, cached] of Array.from(this.cache.entries())) {
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
   * 🚀 ENHANCED: Include global loading state information and storage keys
   */
  getCacheStatus(): {
    totalEntries: number
    loadingEntries: number
    expiredEntries: number
    globalLoadingStates: number
    cacheKeys: string[]
    loadingKeys: string[]
    globalLoadingKeys: string[]
    storageKeys: { [key: string]: { seatAvailability?: string, serviceList?: string } }
  } {
    const now = Date.now()
    let expiredCount = 0
    const storageKeys: { [key: string]: { seatAvailability?: string, serviceList?: string } } = {}

    for (const [key, cached] of Array.from(this.cache.entries())) {
      if ((now - cached.timestamp) >= this.CACHE_EXPIRY) {
        expiredCount++
      }
      
      // Track storage keys for debugging
      if (cached.storageKeys) {
        storageKeys[key] = cached.storageKeys
      }
    }

    return {
      totalEntries: this.cache.size,
      loadingEntries: this.loadingPromises.size,
      expiredEntries: expiredCount,
      globalLoadingStates: this.globalLoadingState.size,
      cacheKeys: Array.from(this.cache.keys()),
      loadingKeys: Array.from(this.loadingPromises.keys()),
      globalLoadingKeys: Array.from(this.globalLoadingState.keys()),
      storageKeys
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