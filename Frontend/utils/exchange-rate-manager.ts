/**
 * Exchange Rate Management System
 * Handles real-time currency conversion with caching and fallbacks
 */

interface ExchangeRate {
  from: string
  to: string
  rate: number
  timestamp: number
  source: string
}

interface CachedRates {
  [key: string]: {
    rate: number
    timestamp: number
    expires: number
  }
}

class ExchangeRateManager {
  private cache: CachedRates = {}
  private readonly CACHE_DURATION = 15 * 60 * 1000 // 15 minutes
  private readonly STALE_THRESHOLD = 60 * 60 * 1000 // 1 hour (show warning if older)
  private readonly MAX_RETRIES = 3
  private readonly API_ENDPOINTS = [
    'https://api.exchangerate-api.com/v4/latest',
    'https://api.fixer.io/latest', 
    'https://api.currencylayer.com/live',
    // Add more fallback APIs
  ]
  
  private activeFetches: Map<string, Promise<number | null>> = new Map()

  /**
   * Get exchange rate with intelligent caching and fallbacks
   */
  async getExchangeRate(fromCurrency: string, toCurrency: string): Promise<number | null> {
    if (fromCurrency === toCurrency) return 1.0

    const cacheKey = `${fromCurrency}_${toCurrency}`
    
    // Check cache first
    const cached = this.getCachedRate(cacheKey)
    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached.rate
    }

    // Avoid duplicate API calls for the same currency pair
    if (this.activeFetches.has(cacheKey)) {
      return await this.activeFetches.get(cacheKey)!
    }

    // Fetch new rate
    const fetchPromise = this.fetchExchangeRate(fromCurrency, toCurrency)
    this.activeFetches.set(cacheKey, fetchPromise)

    try {
      const rate = await fetchPromise
      this.activeFetches.delete(cacheKey)
      
      if (rate !== null) {
        this.cacheRate(cacheKey, rate)
        return rate
      }

      // If fetch failed but we have stale cache, use it with warning
      if (cached) {
        console.warn(`Using stale exchange rate for ${cacheKey}:`, cached)
        return cached.rate
      }

      return null
    } catch (error) {
      this.activeFetches.delete(cacheKey)
      console.error(`Failed to get exchange rate for ${cacheKey}:`, error)
      
      // Return stale cache as last resort
      return cached?.rate || null
    }
  }

  /**
   * Fetch rate from multiple API sources with fallbacks
   */
  private async fetchExchangeRate(from: string, to: string): Promise<number | null> {
    for (let i = 0; i < this.API_ENDPOINTS.length; i++) {
      try {
        const rate = await this.fetchFromAPI(this.API_ENDPOINTS[i], from, to)
        if (rate !== null) {
          return rate
        }
      } catch (error) {
        console.warn(`API ${i + 1} failed for ${from}→${to}:`, error)
        if (i === this.API_ENDPOINTS.length - 1) {
          throw error
        }
      }
    }
    return null
  }

  /**
   * Fetch from specific API endpoint
   */
  private async fetchFromAPI(endpoint: string, from: string, to: string): Promise<number | null> {
    try {
      // ExchangeRate-API format
      if (endpoint.includes('exchangerate-api.com')) {
        const response = await fetch(`${endpoint}/${from}`, {
          headers: { 'Accept': 'application/json' }
        })
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        
        const data = await response.json()
        return data.rates?.[to] || null
      }

      // Fixer.io format  
      if (endpoint.includes('fixer.io')) {
        const API_KEY = process.env.NEXT_PUBLIC_FIXER_API_KEY
        if (!API_KEY) throw new Error('Fixer API key not configured')
        
        const response = await fetch(`${endpoint}?access_key=${API_KEY}&base=${from}&symbols=${to}`)
        const data = await response.json()
        
        if (!data.success) throw new Error(data.error?.info || 'API error')
        return data.rates?.[to] || null
      }

      // CurrencyLayer format
      if (endpoint.includes('currencylayer.com')) {
        const API_KEY = process.env.NEXT_PUBLIC_CURRENCYLAYER_API_KEY
        if (!API_KEY) throw new Error('CurrencyLayer API key not configured')
        
        const response = await fetch(`${endpoint}?access_key=${API_KEY}&source=${from}&currencies=${to}`)
        const data = await response.json()
        
        if (!data.success) throw new Error(data.error?.info || 'API error')
        const rateKey = `${from}${to}`
        return data.quotes?.[rateKey] || null
      }

      throw new Error('Unknown API endpoint format')
      
    } catch (error) {
      console.error(`Failed to fetch from ${endpoint}:`, error)
      throw error
    }
  }

  /**
   * Cache management
   */
  private getCachedRate(cacheKey: string): { rate: number; timestamp: number } | null {
    const cached = this.cache[cacheKey]
    return cached ? { rate: cached.rate, timestamp: cached.timestamp } : null
  }

  private cacheRate(cacheKey: string, rate: number): void {
    const now = Date.now()
    this.cache[cacheKey] = {
      rate,
      timestamp: now,
      expires: now + this.CACHE_DURATION
    }
  }

  private isCacheValid(timestamp: number): boolean {
    return Date.now() - timestamp < this.CACHE_DURATION
  }

  /**
   * Batch fetch multiple rates efficiently
   */
  async getBatchExchangeRates(pairs: Array<{ from: string; to: string }>): Promise<Map<string, number>> {
    const results = new Map<string, number>()
    
    // Group by base currency for efficient API calls
    const groupedByBase = new Map<string, string[]>()
    pairs.forEach(({ from, to }) => {
      if (!groupedByBase.has(from)) {
        groupedByBase.set(from, [])
      }
      groupedByBase.get(from)!.push(to)
    })

    // Fetch rates for each base currency
    const promises = Array.from(groupedByBase.entries()).map(async ([base, targets]) => {
      try {
        const response = await fetch(`${this.API_ENDPOINTS[0]}/${base}`)
        const data = await response.json()
        
        targets.forEach(target => {
          const rate = data.rates?.[target]
          if (rate) {
            const cacheKey = `${base}_${target}`
            results.set(cacheKey, rate)
            this.cacheRate(cacheKey, rate)
          }
        })
      } catch (error) {
        console.error(`Batch fetch failed for base ${base}:`, error)
      }
    })

    await Promise.allSettled(promises)
    return results
  }

  /**
   * Preload common currency pairs
   */
  async preloadCommonRates(): Promise<void> {
    const commonPairs = [
      { from: 'USD', to: 'EUR' }, { from: 'USD', to: 'GBP' },
      { from: 'USD', to: 'KES' }, { from: 'USD', to: 'INR' },
      { from: 'EUR', to: 'USD' }, { from: 'EUR', to: 'KES' },
      { from: 'KES', to: 'USD' }, { from: 'KES', to: 'EUR' },
      { from: 'INR', to: 'USD' }, { from: 'INR', to: 'EUR' }
    ]

    await this.getBatchExchangeRates(commonPairs)
  }

  /**
   * Get rate age and status
   */
  getRateInfo(from: string, to: string): {
    hasRate: boolean
    isStale: boolean
    ageMinutes: number
    lastUpdated: Date | null
  } {
    const cacheKey = `${from}_${to}`
    const cached = this.getCachedRate(cacheKey)
    
    if (!cached) {
      return { hasRate: false, isStale: true, ageMinutes: Infinity, lastUpdated: null }
    }

    const ageMs = Date.now() - cached.timestamp
    const ageMinutes = Math.floor(ageMs / (60 * 1000))
    const isStale = ageMs > this.STALE_THRESHOLD

    return {
      hasRate: true,
      isStale,
      ageMinutes,
      lastUpdated: new Date(cached.timestamp)
    }
  }

  /**
   * Force refresh specific rate
   */
  async refreshRate(from: string, to: string): Promise<number | null> {
    const cacheKey = `${from}_${to}`
    delete this.cache[cacheKey] // Clear cache
    return await this.getExchangeRate(from, to)
  }

  /**
   * Clear all cached rates
   */
  clearCache(): void {
    this.cache = {}
  }

  /**
   * Get fallback rates (hardcoded as emergency backup)
   */
  private getFallbackRate(from: string, to: string): number | null {
    const EMERGENCY_RATES: { [key: string]: { [key: string]: number } } = {
      'USD': { 'EUR': 0.91, 'GBP': 0.79, 'KES': 129.87, 'INR': 83.12 },
      'EUR': { 'USD': 1.10, 'GBP': 0.87, 'KES': 142.86, 'INR': 91.43 },
      'GBP': { 'USD': 1.27, 'EUR': 1.15, 'KES': 164.84, 'INR': 105.56 },
      'KES': { 'USD': 0.0077, 'EUR': 0.0070, 'GBP': 0.0061, 'INR': 0.64 },
      'INR': { 'USD': 0.012, 'EUR': 0.011, 'GBP': 0.0095, 'KES': 1.56 }
    }

    return EMERGENCY_RATES[from]?.[to] || null
  }
}

// Singleton instance
const exchangeRateManager = new ExchangeRateManager()

// Public API
export async function getExchangeRate(from: string, to: string): Promise<number | null> {
  return exchangeRateManager.getExchangeRate(from, to)
}

export async function convertCurrencyRealTime(
  amount: number, 
  from: string, 
  to: string
): Promise<{ convertedAmount: number | null; rate: number | null; error?: string }> {
  try {
    const rate = await exchangeRateManager.getExchangeRate(from, to)
    
    if (rate === null) {
      return { 
        convertedAmount: null, 
        rate: null, 
        error: 'Exchange rate not available' 
      }
    }

    const convertedAmount = Math.round(amount * rate * 100) / 100
    return { convertedAmount, rate }
  } catch (error) {
    return { 
      convertedAmount: null, 
      rate: null, 
      error: error instanceof Error ? error.message : 'Conversion failed' 
    }
  }
}

export async function preloadExchangeRates(): Promise<void> {
  return exchangeRateManager.preloadCommonRates()
}

export function getExchangeRateInfo(from: string, to: string) {
  return exchangeRateManager.getRateInfo(from, to)
}

export async function refreshExchangeRate(from: string, to: string): Promise<number | null> {
  return exchangeRateManager.refreshRate(from, to)
}

// Auto-preload rates when module loads
if (typeof window !== 'undefined') {
  preloadExchangeRates().catch(console.error)
}