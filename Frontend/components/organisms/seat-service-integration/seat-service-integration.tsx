"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { logger } from "@/utils/logger"
import { seatServiceCache } from "@/utils/seat-service-cache-manager"
import { simpleApiManager } from "@/utils/simple-api-manager"
import { 
  calculatePricingBreakdown, 
  calculateServiceFees, 
  extractFlightPricing,
  type SeatPrices 
} from "@/utils/pricing-calculator"
import { SeatSelection } from "@/components/molecules/seat-selection"
import { ServiceSelection } from "@/components/molecules/service-selection" 
import { OrderSummary } from "@/components/molecules/order-summary"

interface SeatServiceIntegrationProps {
  booking?: any
  onContinue?: () => void
  className?: string
}

export function SeatServiceIntegration({ 
  booking, 
  onContinue,
  className 
}: SeatServiceIntegrationProps) {
  const [selectedSeats, setSelectedSeats] = useState({
    outbound: [] as string[],
    return: [] as string[]
  })
  const [selectedServices, setSelectedServices] = useState<string[]>([])
  const [seatPrices, setSeatPrices] = useState<SeatPrices>({
    outbound: 0,
    return: 0
  })
  const [servicePrices, setServicePrices] = useState(0)
  const [flightPricing, setFlightPricing] = useState<{
    baseFare: number
    taxes: number
    total: number
    currency: string
  }>({ baseFare: 0, taxes: 0, total: 0, currency: 'USD' })
  const [services, setServices] = useState<any[]>([])
  const [flightPriceResponse, setFlightPriceResponse] = useState<any>(null)
  const [isRoundTrip, setIsRoundTrip] = useState(false)
  const [flightSegments, setFlightSegments] = useState<any[]>([])
  const [bookingState, setBookingState] = useState({
    step: 'seat-selection', // seat-selection, service-selection, review, complete
    isValid: false,
    errors: [] as string[],
    // 🚀 NEW: Store pricing ObjectKeys for OrderCreate mapping
    seatPricingRefs: {
      outbound: [] as string[],
      return: [] as string[]
    }
  })

  // Load flight price response from session storage and detect trip type
  useEffect(() => {
    try {
      const storedResponse = sessionStorage.getItem('flightPriceResponseForBooking')
      if (storedResponse) {
        const parsedResponse = JSON.parse(storedResponse)
        
        // 🚀 SIMPLIFIED: Let unified API manager handle cache key extraction
        // Just ensure session ID is available
        if (!localStorage.getItem('flight_session_id')) {
          const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
          localStorage.setItem('flight_session_id', sessionId)
          logger.info('✅ Generated new flight session ID:', sessionId)
        }
        
        // Merge metadata if available
        const storedMetadata = sessionStorage.getItem('flightPriceMetadata')
        if (storedMetadata) {
          try {
            const parsedMetadata = JSON.parse(storedMetadata)
            if (!parsedResponse.metadata) {
              parsedResponse.metadata = {}
            }
            Object.assign(parsedResponse.metadata, parsedMetadata)
            logger.info('✅ Successfully merged flight price metadata')
          } catch (metadataError) {
            logger.warn('⚠️ Failed to parse stored metadata:', metadataError)
          }
        }
        
        setFlightPriceResponse(parsedResponse)
        
        // Extract flight pricing information
        const pricingInfo = extractFlightPricing(parsedResponse)
        setFlightPricing(pricingInfo)
        logger.info('💰 Extracted flight pricing:', pricingInfo)
        
        // Trip type detection (simplified)
        const segments = parsedResponse?.flight_segments || []
        setFlightSegments(segments)
        
        const hasReturnFlight = !!(
          parsedResponse?.returnFlight ||
          parsedResponse?.return_segments ||
          (Array.isArray(segments) && segments.some((seg: any) => 
            seg?.direction === 'return' || seg?.type === 'return'
          ))
        )
        
        setIsRoundTrip(hasReturnFlight)
        
        logger.info('🔍 Flight data loaded:', {
          tripType: hasReturnFlight ? 'Round-trip' : 'One-way',
          segments: segments.length,
          hasMetadata: !!parsedResponse?.metadata
        })
        
        // Initialize booking state
        validateBookingState()
        
        // Pre-load seat and service data via unified manager
        seatServiceCache.preloadData(parsedResponse)
          .then(() => {
            logger.info('✅ Successfully pre-loaded seat/service data via unified manager')
          })
          .catch((preloadError) => {
            logger.warn('⚠️ Failed to pre-load seat/service data:', preloadError)
          })
        
        logger.info(`✅ Flight data loaded - ${hasReturnFlight ? 'Round-trip' : 'One-way'}, ${segments.length} segments`)
      } else {
        logger.warn('⚠️ No flight price response found in session storage')
        setBookingState(prev => ({ 
          ...prev, 
          errors: ['No flight data available. Please select a flight first.'] 
        }))
      }
    } catch (error) {
      logger.error('❌ Error loading flight price response:', error)
      setBookingState(prev => ({ 
        ...prev, 
        errors: ['Failed to load flight data. Please try again.'] 
      }))
    }
  }, [])

  // 🚀 Booking State Validation Function
  const validateBookingState = () => {
    const errors: string[] = []
    const passengers = booking?.passengers || [{ objectKey: 'pax1', name: 'Passenger 1', type: 'ADULT' }]
    const passengerCount = passengers.length

    // Check if all passengers have seats for outbound flight
    if (selectedSeats.outbound.length > 0 && selectedSeats.outbound.length < passengerCount) {
      errors.push(`${passengerCount - selectedSeats.outbound.length} passenger(s) need outbound seats`)
    }

    // Check if all passengers have seats for return flight (round-trip only)
    if (isRoundTrip && selectedSeats.return.length > 0 && selectedSeats.return.length < passengerCount) {
      errors.push(`${passengerCount - selectedSeats.return.length} passenger(s) need return seats`)
    }

    const isValid = errors.length === 0
    
    setBookingState(prev => ({
      ...prev,
      isValid,
      errors
    }))

    return isValid
  }

  // Handle seat selection changes with validation
  const handleSeatChange = (flightType: 'outbound' | 'return', updatedSeats: string[], pricingRefs?: string[]) => {
    setSelectedSeats(prev => ({
      ...prev,
      [flightType]: updatedSeats
    }))
    
    // 🚀 CRITICAL FIX: Store pricing ObjectKeys for OrderCreate
    // These are the actual ObjectKeys the backend needs for seat pricing
    if (pricingRefs) {
      logger.info(`🎯 Storing pricing ObjectKeys for ${flightType}: [${pricingRefs.join(', ')}]`)
      
      // Store pricing refs in booking state for OrderCreate
      setBookingState(prev => ({
        ...prev,
        seatPricingRefs: {
          ...prev.seatPricingRefs,
          [flightType]: pricingRefs
        }
      }))
    }
    
    // Calculate seat prices (this would come from actual seat data)
    // For now, using mock calculation
    const pricePerSeat = 2500 // INR
    const newPrice = updatedSeats.length * pricePerSeat
    
    setSeatPrices(prev => ({
      ...prev,
      [flightType]: newPrice
    }))

    // Validate booking state after seat change
    setTimeout(validateBookingState, 100)

    logger.info(`🪑 Updated ${flightType} seats:`, updatedSeats)
  }

  // Handle service selection changes with validation
  const handleServiceChange = (updatedServices: string[]) => {
    setSelectedServices(updatedServices)
    
    // Use unified pricing calculation
    const { total: totalPrice } = calculateServiceFees(updatedServices, services)
    setServicePrices(totalPrice)
    
    // Validate booking state after service change
    setTimeout(validateBookingState, 100)
    
    logger.info(`🛎️ Updated services:`, updatedServices, `Total: ${totalPrice}`)
  }
  
  // Handle services data update from ServiceSelection component
  const handleServicesUpdate = (servicesData: any[]) => {
    setServices(servicesData)
    logger.info(`🛎️ Services data updated: ${servicesData.length} services available`)
    
    // Recalculate service prices with new service data
    if (selectedServices.length > 0) {
      const { total: totalPrice } = calculateServiceFees(selectedServices, servicesData)
      setServicePrices(totalPrice)
    }
  }

  // Debug: Show cache status (simplified)
  const debugCacheStatus = () => {
    if (!flightPriceResponse) return null
    
    const seatCache = seatServiceCache.getCachedSeatAvailability(flightPriceResponse)
    const serviceCache = seatServiceCache.getCachedServiceList(flightPriceResponse)
    const cacheStatus = seatServiceCache.getCacheStatus()
    const simpleDebug = simpleApiManager.getDebugInfo()
    
    return (
      <div className="bg-gray-50 border rounded-lg p-4 mb-4 text-xs">
        <h4 className="font-semibold mb-2">🔍 Simple API Manager Debug Status</h4>
        <div className="space-y-1">
          <div>Seat Data: {seatCache.data ? '✅ Cached' : seatCache.isLoading ? '🔄 Loading' : '❌ Not Available'}</div>
          <div>Service Data: {serviceCache.data ? '✅ Cached' : serviceCache.isLoading ? '🔄 Loading' : '❌ Not Available'}</div>
          <div>Local Cache: {cacheStatus.totalEntries} entries, {cacheStatus.loadingEntries} loading</div>
          <div>Unified Cache: {simpleDebug.cacheEntries.length} entries, {simpleDebug.pendingRequests.length} pending</div>
          <div>Session ID: {simpleDebug.sessionData.sessionId?.slice(-8) || 'Missing'}</div>
          <div>Flight Price Cache Key: {simpleDebug.sessionData.flightPriceCacheKey?.slice(-12) || 'Missing'}</div>
          {seatCache.error && <div className="text-red-600">Seat Error: {seatCache.error}</div>}
          {serviceCache.error && <div className="text-red-600">Service Error: {serviceCache.error}</div>}
        </div>
      </div>
    )
  }

  if (!flightPriceResponse) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-gray-500 mb-2">No flight price data available</div>
          <div className="text-sm text-gray-400">
            Please select a flight first to access seat and service selection
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Debug Panel - Remove in production */}
      {process.env.NODE_ENV === 'development' && debugCacheStatus()}
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Seat and Service Selection */}
        <div className="lg:col-span-2 space-y-6">
          {/* Flight Trip Type Header */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                {isRoundTrip ? 'Round-trip Flight' : 'One-way Flight'} - Select Your Seats & Services
              </h3>
            </div>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              {isRoundTrip 
                ? `Choose seats for both your outbound and return flights (${flightSegments.length} segments total)`
                : 'Choose your preferred seat and add any additional services'
              }
            </p>
          </div>

          {/* Booking State Validation Indicator */}
          {bookingState.errors.length > 0 && (
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                <h4 className="font-semibold text-amber-800 dark:text-amber-200">Booking Validation</h4>
              </div>
              <div className="space-y-1">
                {bookingState.errors.map((error, index) => (
                  <p key={index} className="text-sm text-amber-700 dark:text-amber-300 flex items-center gap-1">
                    <span>⚠️</span> {error}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Outbound Seat Selection */}
          <SeatSelection
            flightPriceResponse={flightPriceResponse}
            flightType="outbound"
            selectedSeats={selectedSeats.outbound}
            onSeatChange={handleSeatChange}
            passengers={booking?.passengers || [{ objectKey: 'pax1', name: 'Passenger 1', type: 'ADULT' }]}
          />
          
          {/* Return Seat Selection - Only show for round-trip flights */}
          {isRoundTrip && (
            <SeatSelection
              flightPriceResponse={flightPriceResponse}
              flightType="return"
              selectedSeats={selectedSeats.return}
              onSeatChange={handleSeatChange}
              passengers={booking?.passengers || [{ objectKey: 'pax1', name: 'Passenger 1', type: 'ADULT' }]}
            />
          )}
          
          {/* Service Selection */}
          <ServiceSelection
            flightPriceResponse={flightPriceResponse}
            selectedServices={selectedServices}
            onServiceChange={handleServiceChange}
            onServicesUpdate={handleServicesUpdate}
            passengers={booking?.passengers || [{ objectKey: 'pax1', name: 'Passenger 1', type: 'ADULT' }]}
          />
        </div>

        {/* Sidebar - Booking Summary */}
        <div className="lg:col-span-1">
          <OrderSummary
            booking={{
              ...booking,
              flightOffer: flightPriceResponse,
              currency: flightPricing.currency
            }}
            selectedSeats={selectedSeats}
            selectedServices={selectedServices}
            seatPrices={seatPrices}
            servicePrices={servicePrices}
            services={services}
            onContinue={onContinue}
          />
        </div>
      </div>
    </div>
  )
}

export default SeatServiceIntegration