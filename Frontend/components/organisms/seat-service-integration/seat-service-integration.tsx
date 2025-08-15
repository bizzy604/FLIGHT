"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { logger } from "@/utils/logger"
import { seatServiceCache } from "@/utils/seat-service-cache-manager"
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
  const [seatPrices, setSeatPrices] = useState({
    outbound: 0,
    return: 0
  })
  const [servicePrices, setServicePrices] = useState(0)
  const [services, setServices] = useState<any[]>([])
  const [flightPriceResponse, setFlightPriceResponse] = useState<any>(null)
  const [isRoundTrip, setIsRoundTrip] = useState(false)
  const [flightSegments, setFlightSegments] = useState<any[]>([])
  const [bookingState, setBookingState] = useState({
    step: 'seat-selection', // seat-selection, service-selection, review, complete
    isValid: false,
    errors: [] as string[]
  })

  // Load flight price response from session storage and detect trip type
  useEffect(() => {
    try {
      const storedResponse = sessionStorage.getItem('flightPriceResponseForBooking')
      if (storedResponse) {
        const parsedResponse = JSON.parse(storedResponse)
        
        // 🚀 CRITICAL FIX: Merge metadata from separate session storage
        const storedMetadata = sessionStorage.getItem('flightPriceMetadata')
        if (storedMetadata) {
          try {
            const parsedMetadata = JSON.parse(storedMetadata)
            // Ensure metadata structure exists
            if (!parsedResponse.metadata) {
              parsedResponse.metadata = {}
            }
            // Merge the stored metadata
            Object.assign(parsedResponse.metadata, parsedMetadata)
            logger.info('✅ Successfully merged flight price metadata with response data')
          } catch (metadataError) {
            logger.warn('⚠️ Failed to parse stored metadata:', metadataError)
          }
        } else {
          logger.warn('⚠️ No flight price metadata found in session storage')
        }
        
        setFlightPriceResponse(parsedResponse)
        
        // 🚀 Dynamic Trip Type Detection
        const segments = parsedResponse?.flight_segments || []
        setFlightSegments(segments)
        
        // Detect if round-trip based on explicit return flight data (not connecting segments)
        // One-way flights can have multiple segments (connecting flights), so check for actual return flight
        
        // 🚨 TEMPORARY FIX: Force one-way until we debug the response structure
        // TODO: Remove this once we identify the correct return flight detection logic
        const hasReturnFlight = false // !!(parsedResponse?.returnFlight || parsedResponse?.return_segments)
        setIsRoundTrip(hasReturnFlight)
        
        // 🔍 Enhanced debugging for trip type detection
        logger.info('🔍 TRIP TYPE DEBUG:', {
          hasReturnFlight,
          returnFlight: !!parsedResponse?.returnFlight,
          return_segments: !!parsedResponse?.return_segments,
          segments_length: segments.length,
          parsedResponse_keys: Object.keys(parsedResponse || {}),
          first_few_keys: Object.keys(parsedResponse || {}).slice(0, 10)
        })
        
        // 🔍 Enhanced debugging for flight price cache key
        logger.info('🔍 FLIGHT PRICE CACHE KEY DEBUG:', {
          has_metadata: !!parsedResponse?.metadata,
          metadata_keys: Object.keys(parsedResponse?.metadata || {}),
          flight_price_cache_key: parsedResponse?.metadata?.flight_price_cache_key,
          offer_id: parsedResponse?.offer_id,
          original_offer_id: parsedResponse?.original_offer_id,
          shopping_response_id: parsedResponse?.shopping_response_id
        })
        
        // 🚀 Initialize booking state
        validateBookingState()
        
        // 🚀 Pre-load seat and service data to prevent redundant API calls (async)
        seatServiceCache.preloadData(parsedResponse)
          .then(() => {
            logger.info(`✅ Successfully pre-loaded seat/service data for flight`)
          })
          .catch((preloadError) => {
            logger.warn(`⚠️ Failed to pre-load seat/service data:`, preloadError)
          })
        
        logger.info(`✅ Loaded flight data - Trip Type: ${hasReturnFlight ? 'Round-trip' : 'One-way'}, Segments: ${segments.length}`)
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
  const handleSeatChange = (flightType: 'outbound' | 'return', updatedSeats: string[]) => {
    setSelectedSeats(prev => ({
      ...prev,
      [flightType]: updatedSeats
    }))
    
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
    
    // Calculate service prices from actual service data
    const totalPrice = updatedServices.reduce((total, serviceKey) => {
      const service = services.find(s => s.objectKey === serviceKey)
      return total + (service?.price?.[0]?.total?.value || 0)
    }, 0)
    
    setServicePrices(totalPrice)
    
    // Validate booking state after service change
    setTimeout(validateBookingState, 100)
    
    logger.info(`🛎️ Updated services:`, updatedServices)
  }

  // Debug: Show cache status
  const debugCacheStatus = () => {
    if (!flightPriceResponse) return null
    
    const seatCache = seatServiceCache.getCachedSeatAvailability(flightPriceResponse)
    const serviceCache = seatServiceCache.getCachedServiceList(flightPriceResponse)
    const cacheStatus = seatServiceCache.getCacheStatus()
    
    return (
      <div className="bg-gray-50 border rounded-lg p-4 mb-4 text-xs">
        <h4 className="font-semibold mb-2">🔍 Enhanced Cache Debug Status</h4>
        <div className="space-y-1">
          <div>Seat Data: {seatCache.data ? '✅ Cached' : seatCache.isLoading ? '🔄 Loading' : '❌ Not Available'}</div>
          <div>Service Data: {serviceCache.data ? '✅ Cached' : serviceCache.isLoading ? '🔄 Loading' : '❌ Not Available'}</div>
          <div>Cache Entries: {cacheStatus.totalEntries}, Loading: {cacheStatus.loadingEntries}, Global Loading: {cacheStatus.globalLoadingStates}</div>
          {cacheStatus.cacheKeys.length > 0 && (
            <div>Cache Keys: {cacheStatus.cacheKeys.join(', ')}</div>
          )}
          {cacheStatus.globalLoadingKeys.length > 0 && (
            <div className="text-blue-600">Global Loading: {cacheStatus.globalLoadingKeys.join(', ')}</div>
          )}
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
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <h3 className="font-semibold text-blue-900">
                {isRoundTrip ? 'Round-trip Flight' : 'One-way Flight'} - Select Your Seats & Services
              </h3>
            </div>
            <p className="text-sm text-blue-700 mt-1">
              {isRoundTrip 
                ? `Choose seats for both your outbound and return flights (${flightSegments.length} segments total)`
                : 'Choose your preferred seat and add any additional services'
              }
            </p>
          </div>

          {/* Booking State Validation Indicator */}
          {bookingState.errors.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                <h4 className="font-semibold text-amber-800">Booking Validation</h4>
              </div>
              <div className="space-y-1">
                {bookingState.errors.map((error, index) => (
                  <p key={index} className="text-sm text-amber-700 flex items-center gap-1">
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
            passengers={booking?.passengers || [{ objectKey: 'pax1', name: 'Passenger 1', type: 'ADULT' }]}
          />
        </div>

        {/* Sidebar - Booking Summary */}
        <div className="lg:col-span-1">
          <OrderSummary
            booking={booking}
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