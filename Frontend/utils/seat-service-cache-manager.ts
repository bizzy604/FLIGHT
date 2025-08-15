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
   * Generate cache key from flight price response
   * 🚀 FIXED: Use backend-compatible cache key format
   */
  private generateCacheKey(flightPriceResponse: any): string {
    // 🎯 CRITICAL FIX: Extract the flight_price_cache_key hash only (without prefix)
    // Backend stores with format: seat_availability:{hash} and service_list:{hash}
    // We need just the {hash} part to be consistent
    
    let cacheKeyHash = null
    
    // Method 1: From metadata.flight_price_cache_key (preferred)
    if (flightPriceResponse?.metadata?.flight_price_cache_key) {
      const fullKey = flightPriceResponse.metadata.flight_price_cache_key
      // Extract hash from flight_price:{hash} format
      cacheKeyHash = fullKey.includes(':') ? fullKey.split(':')[1] : fullKey
    }
    // Method 2: From top-level flight_price_cache_key
    else if (flightPriceResponse?.flight_price_cache_key) {
      const fullKey = flightPriceResponse.flight_price_cache_key
      cacheKeyHash = fullKey.includes(':') ? fullKey.split(':')[1] : fullKey
    }
    // Method 3: From data.metadata.flight_price_cache_key
    else if (flightPriceResponse?.data?.metadata?.flight_price_cache_key) {
      const fullKey = flightPriceResponse.data.metadata.flight_price_cache_key
      cacheKeyHash = fullKey.includes(':') ? fullKey.split(':')[1] : fullKey
    }
    
    if (cacheKeyHash) {
      // Return just the hash part - this will be used to build seat_availability:{hash} and service_list:{hash}
      logger.info(`🔑 Generated cache hash from flight_price_cache_key: ${cacheKeyHash}`)
      return cacheKeyHash
    }
    
    // 🚨 FALLBACK: Generate hash from flight data (must match backend logic)
    try {
      const dataToHash = {
        offer_id: flightPriceResponse?.offer_id || flightPriceResponse?.original_offer_id,
        shopping_response_id: flightPriceResponse?.metadata?.shopping_response_id || 
                             flightPriceResponse?.metadata?.request_id ||
                             flightPriceResponse?.request_id,
        timestamp: Math.floor((flightPriceResponse?.metadata?.timestamp || Date.now()) / 1000) // Round to seconds
      }
      
      // Simple hash generation (this should match backend hash logic)
      const hashString = JSON.stringify(dataToHash)
      const hash = this.generateSimpleHash(hashString)
      
      logger.warn(`⚠️ Using fallback hash generation: ${hash}`)
      logger.warn(`⚠️ Hash input data:`, dataToHash)
      
      return hash
    } catch (error) {
      logger.error(`❌ Failed to generate fallback hash:`, error)
      return 'fallback_' + Date.now()
    }
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
        
        // 🚀 STORE the backend storage key for future cache operations
        if (response.data && response.storage_key) {
          const cacheKey = this.generateCacheKey(flightPriceResponse)
          const existingCache = this.cache.get(cacheKey) || {
            timestamp: Date.now(),
            flightPriceResponseId: cacheKey,
            storageKeys: {}
          }
          
          if (!existingCache.storageKeys) {
            existingCache.storageKeys = {}
          }
          existingCache.storageKeys.seatAvailability = response.storage_key
          this.cache.set(cacheKey, existingCache)
          
          logger.info(`🔑 Stored seat availability storage key: ${response.storage_key}`)
        }
        
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
        
        // 🚀 STORE the backend storage key for future cache operations
        if (response.data && response.storage_key) {
          const cacheKey = this.generateCacheKey(flightPriceResponse)
          const existingCache = this.cache.get(cacheKey) || {
            timestamp: Date.now(),
            flightPriceResponseId: cacheKey,
            storageKeys: {}
          }
          
          if (!existingCache.storageKeys) {
            existingCache.storageKeys = {}
          }
          existingCache.storageKeys.serviceList = response.storage_key
          this.cache.set(cacheKey, existingCache)
          
          logger.info(`🔑 Stored service list storage key: ${response.storage_key}`)
        }
        
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

    for (const [key, cached] of this.cache.entries()) {
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