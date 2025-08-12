import { useState, useCallback } from 'react'
import { logger } from "@/utils/logger"
import { flightStorageManager } from "@/utils/flight-storage-manager"
import { redisFlightStorage } from "@/utils/redis-flight-storage"
import { api } from "@/utils/api-client"
import type { FlightOffer } from "@/types/flight-api"

interface UseFlightSelectionProps {
  flight: FlightOffer
  searchParams?: {
    adults?: number
    children?: number
    infants?: number
    tripType?: string
    origin?: string
    destination?: string
    departDate?: string
    returnDate?: string
    cabinClass?: string
  }
}

interface OfferExpirationStatus {
  status: 'expired' | 'expiring' | 'warning'
  message: string
}

export function useFlightSelection({ flight, searchParams }: UseFlightSelectionProps) {
  const [isSelecting, setIsSelecting] = useState(false)

  // Check if offer is expiring soon (within 10 minutes)
  const getOfferExpirationStatus = useCallback((): OfferExpirationStatus | null => {
    if (!flight.time_limits?.offer_expiration) return null

    try {
      const expirationTime = new Date(flight.time_limits.offer_expiration)
      const currentTime = new Date()
      const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime()
      const minutesUntilExpiration = Math.floor(timeUntilExpiration / (1000 * 60))

      if (timeUntilExpiration <= 0) {
        return { status: 'expired', message: 'Offer expired' }
      } else if (minutesUntilExpiration <= 10) {
        return { status: 'expiring', message: `Expires in ${minutesUntilExpiration}m` }
      } else if (minutesUntilExpiration <= 30) {
        return { status: 'warning', message: `Expires in ${minutesUntilExpiration}m` }
      }
    } catch (error) {
      // Silent error handling
    }

    return null
  }, [flight.time_limits?.offer_expiration])

  // Build flight URL with search parameters
  const buildFlightUrl = useCallback(() => {
    const params = new URLSearchParams({ from: 'search' })

    if (searchParams) {
      if (searchParams.adults) params.set('adults', searchParams.adults.toString())
      if (searchParams.children) params.set('children', searchParams.children.toString())
      if (searchParams.infants) params.set('infants', searchParams.infants.toString())
      if (searchParams.tripType) params.set('tripType', searchParams.tripType)
      if (searchParams.origin) params.set('origin', searchParams.origin)
      if (searchParams.destination) params.set('destination', searchParams.destination)
      if (searchParams.departDate) params.set('departDate', searchParams.departDate)
      if (searchParams.returnDate) params.set('returnDate', searchParams.returnDate)
      if (searchParams.cabinClass) params.set('cabinClass', searchParams.cabinClass)
    }

    if (!flight.id) {
      return '/flights/error'
    }

    return `/flights/${encodeURIComponent(flight.id)}?${params.toString()}`
  }, [flight.id, searchParams])

  // Handle flight selection with storage and API calls
  const handleFlightSelect = useCallback(async (e: React.MouseEvent) => {
    setIsSelecting(true)

    try {
      // Store the complete flight data with a timestamp
      const flightData = {
        flight,
        timestamp: new Date().toISOString(),
        expiresAt: Date.now() + (30 * 60 * 1000), // 30 minutes expiry
        searchParams: searchParams || {}
      }

      // Store selected flight data using robust storage manager
      const storeResult = await flightStorageManager.storeSelectedFlight(flightData)

      if (!storeResult.success) {
        logger.warn('⚠️ Failed to store selected flight data:', storeResult.error)
        // Continue anyway - don't block user flow
      } else {
        logger.info('✅ Selected flight data stored successfully')
      }

      // If this is a roundtrip, store the return flight data as well
      if (flight.returnFlight) {
        const returnFlightData = {
          flight: flight.returnFlight,
          timestamp: new Date().toISOString(),
          expiresAt: Date.now() + (30 * 60 * 1000), // 30 minutes expiry
          searchParams: searchParams || {}
        }

        const returnStoreResult = await flightStorageManager.storeSelectedFlight(returnFlightData)
        if (!returnStoreResult.success) {
          logger.warn('⚠️ Failed to store return flight data:', returnStoreResult.error)
        }
      }

      // Try to get flight pricing from cache first
      logger.info('🔍 Checking flight pricing cache...')

      const flightIndex = parseInt(flight.id) // flight.id is the index
      const shoppingResponseId = 'BACKEND_WILL_EXTRACT'
      
      try {
        // Check cache first
        const cacheCheckResponse = await api.checkFlightPriceCache(flightIndex.toString(), shoppingResponseId)
        
        if (cacheCheckResponse.data.status === 'success' && cacheCheckResponse.data.source === 'cache') {
          logger.info('🚀 Flight price cache hit! Using cached pricing data')
          
          const cachedPricingData = cacheCheckResponse.data.data
          
          // Extract the priced offer from cached response
          const firstPricedOffer = cachedPricingData.priced_offers ? cachedPricingData.priced_offers[0] : cachedPricingData
          
          if (firstPricedOffer) {
            // Add metadata if available
            if (cachedPricingData.metadata) {
              firstPricedOffer.metadata = cachedPricingData.metadata
            }

            // Store priced offer in session storage for immediate access
            sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(firstPricedOffer))
            
            if (cachedPricingData.metadata) {
              sessionStorage.setItem('flightPriceMetadata', JSON.stringify(cachedPricingData.metadata))
              logger.info('✅ Using cached flight pricing data')
            }
            
            // Skip API call, we have cached data
            return
          }
        }
      } catch (cacheError) {
        logger.warn('⚠️ Flight price cache check failed, falling back to API:', cacheError)
      }

      // Cache miss - Call flight pricing API
      logger.info('🔄 Cache miss - calling flight pricing API for selected flight...')

      // Get flight search data from new cache-first system by checking with current search params
      let airShoppingData = {}

      // Build search parameters to check cache (same as used in flights page)
      if (searchParams) {
        const flightSearchParams = {
          tripType: searchParams.tripType === 'round-trip' ? 'ROUND_TRIP' : 'ONE_WAY',
          odSegments: [{
            origin: searchParams.origin,
            destination: searchParams.destination,
            departureDate: searchParams.departDate,
            ...(searchParams.tripType === 'round-trip' && searchParams.returnDate ? { returnDate: searchParams.returnDate } : {})
          }],
          numAdults: searchParams.adults || 1,
          numChildren: searchParams.children || 0,
          numInfants: searchParams.infants || 0,
          cabinPreference: searchParams.cabinClass || 'ECONOMY',
          directOnly: false
        };

        try {
          // Check the new cache-first system for flight search data
          const cacheCheckResponse = await api.checkFlightSearchCache(flightSearchParams);
          
          if (cacheCheckResponse.data.status === 'success' && cacheCheckResponse.data.source === 'cache') {
            logger.info('✅ Found flight search data in new cache system');
            
            const cachedFlightData = cacheCheckResponse.data.data;
            
            // Extract metadata if available
            if (cachedFlightData?.metadata) {
              airShoppingData = cachedFlightData.metadata;
              logger.info('✅ Using metadata from new cache system');
            } else if (cachedFlightData?.raw_response) {
              // Use raw response if metadata not available
              airShoppingData = cachedFlightData.raw_response;
              logger.info('✅ Using raw response from new cache system');
            } else {
              // Fallback to the whole cached data
              airShoppingData = cachedFlightData;
              logger.info('✅ Using full cached data from new cache system');
            }
          } else {
            logger.warn('⚠️ No flight search data found in new cache system, backend will handle cache retrieval');
          }
        } catch (cacheError) {
          logger.warn('⚠️ Failed to check new cache system, backend will handle cache retrieval:', cacheError);
        }
      } else {
        logger.warn('⚠️ No search parameters available, backend will handle cache retrieval');
      }

      // Call flight pricing API
      const response = await api.getFlightPrice(
        flightIndex,
        shoppingResponseId,
        airShoppingData
      )

      // Handle expired offers error specifically
      if (response.data?.status === 'expired_offer_error') {
        logger.warn('⚠️ Flight offers have expired, need to refresh search results')
        
        // Show user-friendly message about expired offers
        if (onError) {
          onError('Flight offers have expired. Please search again for current prices and availability.')
        } else {
          alert('Flight offers have expired. The page will refresh to show current flights.')
          // Auto-refresh the page to trigger a new search
          window.location.reload()
        }
        return
      }

      if (!response.data || response.data.status !== 'success') {
        throw new Error(response.data?.error || 'Failed to get flight pricing')
      }

      // Extract the priced offer from the response
      const firstPricedOffer = response.data.data.priced_offers[0]
      if (!firstPricedOffer) {
        throw new Error("No valid offer found in the pricing response")
      }

      // Add metadata to the priced offer for order creation
      firstPricedOffer.metadata = response.data.data.metadata

      // Add raw response if available (fallback when caching fails)
      if (response.data.data.raw_response) {
        firstPricedOffer.raw_flight_price_response = response.data.data.raw_response
      }

      logger.info('✅ Flight pricing API call successful')

      // Note: Flight pricing data is now automatically cached by the backend Redis system
      // No need for client-side storage as backend handles caching with the new Redis implementation
      logger.info('✅ Flight pricing data will be automatically cached by backend')

      // Store metadata for order creation if available
      if (response.data.data.metadata) {
        sessionStorage.setItem('flightPriceMetadata', JSON.stringify(response.data.data.metadata))
        logger.info('✅ Stored flight price metadata for order creation')
      }

      // Store priced offer in session storage for immediate access
      sessionStorage.setItem('flightPriceResponseForBooking', JSON.stringify(firstPricedOffer))

      // Store raw flight price response for order creation
      if (response.data.data.raw_response) {
        sessionStorage.setItem('rawFlightPriceResponse', JSON.stringify(response.data.data.raw_response))
        logger.info('✅ Stored raw flight price response for order creation')
      }

      // Add a small delay to show the loading state
      await new Promise(resolve => setTimeout(resolve, 500))

    } catch (error) {
      console.error('❌ Error during flight selection:', error)

      // Show user-friendly error message
      const errorMessage = error instanceof Error ? error.message : 'Failed to get flight pricing'
      alert(`Unable to select flight: ${errorMessage}. Please try again or select a different flight.`)

      setIsSelecting(false)
      return // Don't navigate if there's an error
    } finally {
      setIsSelecting(false)
    }
  }, [flight, searchParams])

  return {
    isSelecting,
    getOfferExpirationStatus,
    buildFlightUrl,
    handleFlightSelect
  }
}