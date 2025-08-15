"use client"

import * as React from "react"
import { useState, useEffect } from "react"

import { cn } from "@/utils/cn"
import { LoadingSpinner } from "@/components/atoms"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { api } from "@/utils/api-client"
import { seatServiceCache } from "@/utils/seat-service-cache-manager"
import { logger } from "@/utils/logger"
import { formatCurrency, formatCurrencyForDisplay, getCurrencyIndicator } from "@/utils/currency-formatter"
import { getSmartPriceDisplay, getUserPreferredCurrency, getCurrencyDisclaimer } from "@/utils/currency-converter"

interface Seat {
  objectKey: string
  location: {
    column: string
    row: {
      number: {
        value: string
      }
    }
    characteristics?: {
      characteristic: Array<{
        code: string
        remarks?: {
          remark: Array<{
            value: string
          }>
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
  type?: 'standard' | 'premium' | 'exit' | 'preferred'
}

interface SeatAvailabilityResponse {
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
              row: {
                position: number
              }
              column: {
                position: string
              }
            }>
          }
          type: {
            code: string
          }
        }>
      }
    }>
  }>
  dataLists?: {
    seatList?: {
      seats: Seat[]
    }
  }
}

// Comprehensive IATA Seat Characteristic Codes mapping (from IATA Codeset Directory v24.1)
const seatCodes = {
  // Basic restrictions and features
  '1': 'Restricted seat - General',
  '2': 'Leg rest available', 
  '3': 'Individual video screen - Choice of movies',
  '4': 'Not a window seat',
  '6': 'Near galley seat',
  '7': 'Near toilet seat',
  '8': 'No seat at this location',
  '9': 'Center seat (not window, not aisle)',
  
  // RBD designations
  '10': 'Seat designated for RBD "A"',
  '11': 'Seat designated for RBD "B"',
  '12': 'Seat designated for RBD "C"',
  '13': 'Seat designated for RBD "D"',
  '14': 'Seat designated for RBD "F"',
  '15': 'Seat designated for RBD "H"',
  '16': 'Seat designated for RBD "J"',
  '17': 'Seat designated for RBD "K"',
  '18': 'Seat designated for RBD "L"',
  '19': 'Seat designated for RBD "M"',
  '20': 'Seat designated for RBD "P"',
  '21': 'Seat designated for RBD "Q"',
  '22': 'Seat designated for RBD "R"',
  '23': 'Seat designated for RBD "S"',
  '24': 'Seat designated for RBD "T"',
  '25': 'Seat designated for RBD "V"',
  '26': 'Seat designated for RBD "W"',
  '27': 'Seat designated for RBD "Y"',
  
  // Seat conditions
  '28': 'Not fitted',
  '29': 'No recline seat',
  '30': 'Limited recline seat',
  
  // Primary codes
  'A': 'Aisle seat',
  'AA': 'All available aisle seats',
  'AB': 'Seat adjacent to bar',
  'AC': 'Seat adjacent to closet',
  'AG': 'Seat adjacent to galley',
  'AJ': 'Adjacent aisle seats',
  'AL': 'Seat adjacent to lavatory',
  'AM': 'Individual movie screen - No choice of movie selection',
  'AR': 'No seat - airphone',
  'AS': 'Individual airphone',
  'AT': 'Seat adjacent to table',
  'AU': 'Seat adjacent to stairs to upper deck',
  'AV': 'Only available seats',
  'AW': 'All available window seats',
  
  'B': 'Bassinet facility',
  'BA': 'No seat - bar',
  'BK': 'Blocked seat for preferred passenger in adjacent seat',
  'BC': 'Seat blocked for Codeshare Partner',
  'BE': 'Seat block designated for Basic Economy',
  'BR': 'Seat is broken - not available for use',
  'BS': 'Business Class Suite',
  
  'C': 'Crew seat',
  'CC': 'Center section seats',
  'CH': 'Chargeable seat',
  'CL': 'No seat - closet',
  'CS': 'Conditional seat - contact airline',
  
  'D': 'No seat - exit door',
  'DE': 'Deportee',
  
  'E': 'Exit and emergency exit',
  'EA': 'Not on exit seat',
  'EC': 'AC Power Outlet',
  'EK': 'Economy comfort seat',
  'ES': 'Suite',
  'EX': 'No seat - emergency Exit',
  
  'F': 'Added seat',
  'FC': 'Front of cabin class/compartment',
  'FS': 'First Class Suite',
  
  'G': 'Seat at forward end of cabin',
  'GF': 'General facility',
  'GN': 'No seat - galley',
  'GR': 'Group seat - offered to travelers belonging to a group',
  
  'H': 'Seat with facilities for handicapped/incapacitated passenger',
  
  'I': 'Seat suitable for adult with an infant',
  'IA': 'Inside aisle seats',
  'IE': 'Seat not suitable for child',
  'IF': 'Seat suitable for Child Restraint Forward-facing',
  'IK': 'Adjacent Seat Blocked for Infant',
  'IR': 'Seat suitable for Child Restraint Aft-facing',
  
  'J': 'Rear facing seat',
  'JS': 'Seat designated for additional Jumpseat',
  
  'K': 'Bulkhead seat',
  'KA': 'Bulkhead seat with movie screen',
  'KN': 'Bulkhead, no seat',
  
  'L': 'Extra leg space seat',
  'LA': 'No seat - lavatory',
  'LB': 'Rear facing lie flat seat',
  'LE': 'Left facing lie flat seat more left angle',
  'LF': 'Lie flat seat',
  'LG': 'No seat - luggage storage',
  'LH': 'Restricted seat - offered on long-haul segments',
  'LL': 'Left facing lie flat seat',
  'LR': 'Right facing lie flat seat',
  'LS': 'Left side of aircraft',
  'LT': 'Right facing lie flat seat more right angle',
  
  'M': 'Seat without a movie view',
  'MA': 'Medically OK to travel',
  'ML': 'Seat suitable for Musical Instrument - Large',
  'MS': 'Middle seat',
  'MX': 'Seat suitable for Musical Instrument - Extra Large',
  
  'N': 'No smoking seat',
  
  'O': 'Preferential seat',
  'OW': 'Overwing seat(s)',
  
  'P': 'Extra seat for comfort - arm rest can be raised',
  'PC': 'Pet cabin',
  'PE': 'Premium Economy Suite',
  
  'Q': 'Seat in a quiet zone',
  
  'RS': 'Right side of aircraft',
  
  'S': 'Smoking seat',
  'SC': 'Skycouch',
  'SO': 'No seat - storage space',
  'ST': 'No seat - stairs to upper deck',
  
  'T': 'Rear/Tail section of aircraft',
  'TA': 'No seat - table',
  
  'U': 'Seat suitable for unaccompanied minors',
  'UP': 'Upper deck',
  'US': 'USB Power Port',
  
  'V': 'Seat to be left vacant or offered last',
  
  'W': 'Window seat',
  'WA': 'Window and aisle together',
  
  'X': 'No facility seat (indifferent seat)',
  
  'Z': 'Buffer zone seat',
  
  // Extended codes
  '1A': 'Seat not allowed for infant',
  '1B': 'Seat not allowed for medical',
  '1C': 'Seat not allowed for unaccompanied minor',
  '1D': 'Restricted recline seat',
  '1E': 'Seat with Airbag in Seatbelt',
  '1M': 'Seat with movie view',
  '1W': 'Window seat without window',
  
  '3A': 'Individual video screen - No choice of movie',
  '3B': 'Individual video screen - Choice of movies, games, information, etc',
  
  '6A': 'In front of galley seat',
  '6B': 'Behind galley seat',
  
  '7A': 'In front of toilet seat',
  '7B': 'Behind toilet seat',
  
  // Tier and fare designations
  '33': 'Seat designated for Tier 1',
  '34': 'Seat designated for Tier 2',
  '35': 'Seat designated for Tier 3',
  '36': 'Seat designated for Tier 4',
  '37': 'Seat designated for Neighbor-Free Seat',
  '38': 'Seat block designated for Reservation Agents',
  '39': 'Seat block designated for Reservations or Airport',
  '40': 'Seat block designated for Airport Agents',
  
  '61': 'Seat designated for Fare 1',
  '62': 'Seat designated for Fare 2',
  '63': 'Seat designated for Fare 3',
  '64': 'Seat designated for Fare 4',
  '65': 'Seat designated for Fare 5',
  '66': 'Seat designated for Fare 6',
  
  // Additional features
  '70': 'Individual video screen - services unspecified',
  '71': 'No seat - access to handicapped lavatory',
  '72': 'Undesirable seat',
  '73': 'Conditional chargeable seat'
} as const

interface SeatSelectionProps {
  flightPriceResponse: any
  flightType: 'outbound' | 'return'
  segmentKey?: string
  selectedSeats: string[]
  onSeatChange: (flightType: 'outbound' | 'return', updatedSeats: string[]) => void
  passengers: Array<{
    objectKey: string
    name: string
    type: string
  }>
  className?: string
}

export function SeatSelection({ 
  flightPriceResponse, 
  flightType, 
  segmentKey,
  selectedSeats, 
  onSeatChange,
  passengers,
  className 
}: SeatSelectionProps) {
  const [seats, setSeats] = useState<Seat[]>([])
  const [seatMap, setSeatMap] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load seat availability from backend with intelligent caching
  useEffect(() => {
    const loadSeatAvailability = async () => {
      if (!flightPriceResponse) return

      setLoading(true)
      setError(null)

      try {
        logger.info('🪑 Loading seat availability data...')
        
        // 🔍 DEBUG: Check what flight price response we're receiving
        logger.info('🔍 SEAT SELECTION - Flight Price Response Debug:', {
          response_type: typeof flightPriceResponse,
          response_keys: Object.keys(flightPriceResponse || {}),
          has_metadata: !!flightPriceResponse?.metadata,
          metadata_keys: Object.keys(flightPriceResponse?.metadata || {}),
          flight_price_cache_key: flightPriceResponse?.metadata?.flight_price_cache_key,
          offer_id: flightPriceResponse?.offer_id,
          original_offer_id: flightPriceResponse?.original_offer_id
        })
        
        // 🚀 STEP 1: Check our pre-loaded cache first
        const cachedResult = seatServiceCache.getCachedSeatAvailability(flightPriceResponse)
        
        if (cachedResult.data) {
          logger.info('⚡ Using pre-loaded seat availability data from cache!')
          const seatData = cachedResult.data
          
          // Process cached data
          processSeatAvailabilityData(seatData)
          setLoading(false)
          return
        } 
        
        if (cachedResult.isLoading) {
          logger.info('🔄 Seat availability data is still loading in background, waiting with exponential backoff...')
          // Use exponential backoff to wait for global preloading to complete
          await waitForCacheWithBackoff(flightPriceResponse, 5, 1000) // 5 retries, starting with 1 second
          return
        }

        if (cachedResult.error) {
          logger.warn('⚠️ Pre-loading failed with error:', cachedResult.error)
        }

        // 🚀 STEP 2: Fall back to direct API call
        logger.info('💻 No pre-loaded data available, using direct API call')
        await fallbackToApiCall()

      } catch (err) {
        logger.error("❌ Error loading seat availability:", err)
        setError("Failed to load seat map. Using simplified layout.")
        // Use fallback data
        setSeatMap({
          columns: ["A", "B", "C", "", "D", "E", "F"],
          rows: { first: 1, last: 30 },
          components: []
        })
        setSeats([])
      } finally {
        setLoading(false)
      }
    }

    // 🚀 ENHANCED: Wait for cache with exponential backoff to prevent redundant API calls
    const waitForCacheWithBackoff = async (flightPriceResponse: any, maxRetries: number, initialDelay: number) => {
      let delay = initialDelay
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        logger.info(`🔄 Cache wait attempt ${attempt}/${maxRetries}, delay: ${delay}ms`)
        
        await new Promise(resolve => setTimeout(resolve, delay))
        
        const retryResult = seatServiceCache.getCachedSeatAvailability(flightPriceResponse)
        
        if (retryResult.data) {
          logger.info(`✅ Got pre-loaded seat availability data after ${attempt} attempts!`)
          processSeatAvailabilityData(retryResult.data)
          setLoading(false)
          return
        }
        
        if (!retryResult.isLoading) {
          logger.info(`🚫 Global loading completed but no data available after ${attempt} attempts`)
          break
        }
        
        // Exponential backoff with jitter
        delay = Math.min(delay * 2, 10000) + Math.random() * 1000
      }
      
      // If we reach here, fall back to API call as last resort
      logger.warn(`⚠️ Cache wait timeout after ${maxRetries} attempts, falling back to API call`)
      await fallbackToApiCall()
      setLoading(false)
    }

    // Helper function to process seat availability data
    const processSeatAvailabilityData = (seatData: any) => {
      logger.info('🔍 Processing seat availability data structure:', Object.keys(seatData || {}))
      
      // Handle the backend transformer response structure
      let actualData = seatData
      
      // If it's wrapped in a status response, extract the data
      if (seatData?.status === 'success' && seatData?.data) {
        actualData = seatData.data
        logger.info('✅ Extracted data from status wrapper')
      }
      
      // Set seat display configuration
      if (actualData?.flights?.[0]?.cabin?.[0]?.seatDisplay) {
        const seatDisplay = actualData.flights[0].cabin[0].seatDisplay
        const seatMapConfig = {
          columns: seatDisplay.columns?.map((col: any) => col.value) || [],
          rows: seatDisplay.rows || { first: 1, last: 30 },
          components: seatDisplay.component || []
        }
        setSeatMap(seatMapConfig)
        logger.info('✅ Set seat map configuration from response:', {
          columns_count: seatMapConfig.columns.length,
          row_range: seatMapConfig.rows,
          total_expected_positions: (seatMapConfig.rows.last - seatMapConfig.rows.first + 1) * seatMapConfig.columns.length
        })
      } else {
        logger.warn('⚠️ No seatDisplay found, using fallback configuration')
        setSeatMap({
          columns: ["A", "B", "C", "", "D", "E", "F", "", "H", "J", "K"],
          rows: { first: 1, last: 50 },
          components: []
        })
      }

      // Set seats data - check multiple possible locations
      let seatsArray = null
      
      if (actualData?.dataLists?.seatList?.seats) {
        seatsArray = actualData.dataLists.seatList.seats
        logger.info(`✅ Found ${seatsArray.length} seats in dataLists.seatList.seats`)
      } else if (actualData?.dataLists?.seats) {
        seatsArray = actualData.dataLists.seats
        logger.info(`✅ Found ${seatsArray.length} seats in dataLists.seats`)
      } else if (actualData?.seats) {
        seatsArray = actualData.seats
        logger.info(`✅ Found ${seatsArray.length} seats in top-level seats`)
      }
      
      if (seatsArray && seatsArray.length > 0) {
        setSeats(seatsArray)
        
        // 🔍 Debug: Analyze seat distribution across rows
        const rowDistribution = seatsArray.reduce((acc: any, seat: any) => {
          const row = seat.location?.row?.number?.value
          if (row) {
            acc[row] = (acc[row] || 0) + 1
          }
          return acc
        }, {})
        
        const rows = Object.keys(rowDistribution).map(r => parseInt(r)).sort((a, b) => a - b)
        const minRow = Math.min(...rows)
        const maxRow = Math.max(...rows)
        
        // 🚀 CRITICAL FIX: Update seat map rows based on actual seat data
        if (rows.length > 0) {
          setSeatMap(prevMap => ({
            ...prevMap,
            rows: {
              first: minRow,
              last: maxRow,
              upperDeckInd: false
            }
          }))
          logger.info('🔧 Updated seat map rows based on actual seat data:', {
            previous_fallback: { first: 1, last: 30 },
            updated_to: { first: minRow, last: maxRow }
          })
        }
        
        logger.info(`✅ Successfully loaded ${seatsArray.length} seats for selection`, {
          seat_count: seatsArray.length,
          rows_with_seats: rows.length,
          min_row: minRow,
          max_row: maxRow,
          first_5_rows: rows.slice(0, 5),
          last_5_rows: rows.slice(-5),
          sample_seat_locations: seatsArray.slice(0, 3).map((s: any) => ({
            row: s.location?.row?.number?.value,
            column: s.location?.column
          }))
        })
      } else {
        logger.warn('⚠️ No seats found in response, using fallback')
        // Create fallback data
        setSeats([])
        setSeatMap({
          columns: ["A", "B", "C", "", "D", "E", "F"],
          rows: { first: 1, last: 30 },
          components: []
        })
      }
    }

    // Fallback function for direct API calls (original logic)
    const fallbackToApiCall = async () => {
      try {
        // Check backend cache first
        const cacheResponse = await api.checkSeatAvailabilityCache(flightPriceResponse, segmentKey)
        
        let seatData = null
        
        if (cacheResponse.data?.cache_hit) {
          logger.info("🎯 Backend seat availability cache hit")
          seatData = cacheResponse.data.data
        } else {
          logger.info("📞 Backend cache miss, making fresh API call")
          const response = await api.getSeatAvailability(flightPriceResponse, segmentKey)
          seatData = response.data
        }

        processSeatAvailabilityData(seatData)
      } catch (apiError) {
        logger.error("❌ API fallback failed:", apiError)
        throw apiError
      }
    }

    loadSeatAvailability()
  }, [flightPriceResponse, segmentKey])

  const getSeatInfo = (seatId: string): Seat | null => {
    const seatInfo = seats.find(seat => {
      const row = seat.location.row.number.value
      const column = seat.location.column
      return `${row}${column}` === seatId
    }) || null
    
    // Debug logging for first few seat lookups
    if (seats.length > 0 && Math.random() < 0.1) { // Log 10% of lookups to avoid spam
      logger.info(`🔍 Seat lookup for ${seatId}: found=${!!seatInfo}, total_seats=${seats.length}`)
    }
    
    return seatInfo
  }

  const getSeatType = (seat: Seat): 'standard' | 'premium' | 'exit' | 'preferred' => {
    if (!seat.location.characteristics?.characteristic) return 'standard'
    
    const codes = seat.location.characteristics.characteristic.map(c => c.code)
    
    // Priority classification based on IATA codes (order matters for user experience)
    
    // 1. EMERGENCY EXIT (Highest priority - special safety requirements)
    if (codes.includes('E')) return 'exit' 
    
    // 2. PREMIUM EXPERIENCE (Extra comfort, space, or amenities)
    if (codes.includes('FC') ||    // Front of cabin
        codes.includes('K') ||     // Bulkhead seat (extra space)
        codes.includes('L') ||     // Extra leg space seat
        codes.includes('LF') ||    // Lie flat seat
        codes.includes('BS') ||    // Business Class Suite
        codes.includes('FS') ||    // First Class Suite
        codes.includes('ES') ||    // Suite
        codes.includes('PE') ||    // Premium Economy Suite
        codes.includes('EK') ||    // Economy comfort seat
        codes.includes('2') ||     // Leg rest available
        codes.includes('EC') ||    // AC Power Outlet
        codes.includes('US')) {    // USB Power Port
      return 'premium'
    }
    
    // 3. PREFERRED LOCATION (Airline charges extra for better location)
    if (codes.includes('CH') ||    // Chargeable seat
        codes.includes('73') ||    // Conditional chargeable seat
        codes.includes('O')) {     // Preferential seat
      return 'preferred'
    }
    
    // 4. STANDARD (Regular economy seats)
    return 'standard'
  }

  const getSeatFeatures = (seat: Seat): string[] => {
    if (!seat.location.characteristics?.characteristic) return []
    
    const codes = seat.location.characteristics.characteristic.map(c => c.code)
    const features: string[] = []
    
    codes.forEach(code => {
      if (seatCodes[code as keyof typeof seatCodes]) {
        features.push(seatCodes[code as keyof typeof seatCodes])
      }
    })
    
    return features
  }

  const getSeatRestrictions = (seat: Seat): string[] => {
    if (!seat.location.characteristics?.characteristic) return []
    
    const codes = seat.location.characteristics.characteristic.map(c => c.code)
    const restrictions: string[] = []
    
    if (codes.includes('1A')) restrictions.push('No infants')
    if (codes.includes('1B')) restrictions.push('No medical passengers')
    if (codes.includes('1C')) restrictions.push('No unaccompanied minors')
    if (codes.includes('IE')) restrictions.push('Not suitable for children')
    if (codes.includes('1D')) restrictions.push('Restricted recline')
    
    return restrictions
  }

  const getSeatIcons = (seat: Seat): string[] => {
    if (!seat.location.characteristics?.characteristic) return []
    
    const codes = seat.location.characteristics.characteristic.map(c => c.code)
    const icons: string[] = []
    
    // Essential icons for quick recognition
    if (codes.includes('B')) icons.push('🚼') // Bassinet
    if (codes.includes('H')) icons.push('♿') // Accessibility/Handicapped
    if (codes.includes('AL') || codes.includes('7A') || codes.includes('7B')) icons.push('🚽') // Near lavatory
    if (codes.includes('AG') || codes.includes('6A') || codes.includes('6B')) icons.push('🍽️') // Near galley
    if (codes.includes('OW')) icons.push('✈️') // Overwing
    if (codes.includes('E')) icons.push('🚪') // Emergency exit
    if (codes.includes('W')) icons.push('🪟') // Window seat
    if (codes.includes('EC')) icons.push('🔌') // AC Power
    if (codes.includes('US')) icons.push('🔌') // USB Power
    if (codes.includes('3') || codes.includes('3A') || codes.includes('3B') || codes.includes('70')) icons.push('📺') // Video screen
    if (codes.includes('2')) icons.push('🦶') // Leg rest
    if (codes.includes('PC')) icons.push('🐕') // Pet cabin
    if (codes.includes('ML') || codes.includes('MX')) icons.push('🎵') // Musical instrument
    
    // Restriction warnings
    if (codes.includes('1A') || codes.includes('1B') || codes.includes('1C') || codes.includes('IE') || 
        codes.includes('1D') || codes.includes('29') || codes.includes('30')) {
      icons.push('⚠️')
    }
    
    return icons.slice(0, 3) // Limit to 3 icons max for display
  }

  const getSeatPrice = (seatId: string): number => {
    const seat = getSeatInfo(seatId)
    if (!seat?.price?.total) return 0
    return seat.price.total.value
  }

  const getSeatCurrency = (): string => {
    const firstSeatWithPrice = seats.find(s => s.price?.total?.code)
    return firstSeatWithPrice?.price?.total?.code || 'USD'
  }

  const isSeatAvailable = (seatId: string): boolean => {
    const seat = getSeatInfo(seatId)
    if (!seat) return false
    return seat.availability !== 'unavailable' && seat.availability !== 'occupied'
  }

  const isSeatPremium = (seatId: string): boolean => {
    const seat = getSeatInfo(seatId)
    if (!seat) return false
    return getSeatType(seat) === 'premium'
  }

  const isSeatExitRow = (seatId: string): boolean => {
    const seat = getSeatInfo(seatId)
    if (!seat) return false
    return getSeatType(seat) === 'exit'
  }

  const handleSeatSelect = (seatId: string) => {
    logger.info(`🪑 Seat ${seatId} clicked`)
    
    const seatInfo = getSeatInfo(seatId)
    const isAvailable = isSeatAvailable(seatId)
    
    logger.info(`🪑 Seat ${seatId} - Available: ${isAvailable}, SeatInfo exists: ${!!seatInfo}`)
    
    if (!isAvailable) {
      logger.warn(`⚠️ Seat ${seatId} is not available - availability: ${seatInfo?.availability}`)
      return
    }

    const currentlySelected = selectedSeats.includes(seatId)
    let newSelectedSeats: string[]
    const maxPassengers = passengers.length

    if (currentlySelected) {
      // Deselect: Remove the seat from the array
      newSelectedSeats = selectedSeats.filter(s => s !== seatId)
      logger.info(`✅ Deselected seat ${seatId}`)
    } else {
      // Select: Add the seat to the array, but limit to passenger count
      if (selectedSeats.length < maxPassengers) {
        newSelectedSeats = [...selectedSeats, seatId]
        logger.info(`✅ Selected seat ${seatId}`)
      } else {
        // Replace oldest selection with new selection (FIFO)
        newSelectedSeats = [...selectedSeats.slice(1), seatId]
        logger.info(`✅ Replaced oldest selection with seat ${seatId}`)
      }
    }
    
    logger.info(`🪑 Seat selection changed from [${selectedSeats.join(', ')}] to [${newSelectedSeats.join(', ')}]`)
    onSeatChange(flightType, newSelectedSeats)
  }

  const getTotalPrice = (): number => {
    return selectedSeats.reduce((total, seatId) => {
      return total + getSeatPrice(seatId)
    }, 0)
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Seat Selection - {flightType}</CardTitle>
          <CardDescription>Loading seat map...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner className="h-6 w-6" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error && !seatMap) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Seat Selection - {flightType}</CardTitle>
          <CardDescription className="text-red-600">{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Button 
              variant="outline" 
              onClick={() => window.location.reload()}
            >
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!seatMap) return null

  const columns = seatMap.columns || []
  const rowRange = seatMap.rows || { first: 1, last: 30 }
  const totalRows = rowRange.last - rowRange.first + 1

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-6 bg-purple-600 rounded-full"></div>
          <h2 className="text-xl font-bold text-gray-900">Complete Seat Map - {flightType}</h2>
        </div>
        <div className="text-sm text-gray-600 mb-4">
          All seats are shown for your reference. Choose any available seat that fits your needs and budget.
        </div>
        {error && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm text-yellow-800">
            ⚠️ {error}
          </div>
        )}

        {/* Enhanced Seat Type Guide Banner with IATA Code Explanations */}
        <div className="bg-gradient-to-r from-blue-50 via-yellow-50 to-green-50 border border-blue-200 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4 text-center">🪑 Seat Types Guide</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            
            {/* Standard Seats */}
            <div className="flex flex-col items-center gap-2 p-3 bg-white rounded-lg shadow-sm">
              <div className="w-8 h-8 bg-white border-2 border-green-500 rounded-lg flex items-center justify-center text-sm font-bold text-green-600">A</div>
              <div className="text-center">
                <div className="font-semibold text-green-600">STANDARD</div>
                <div className="text-xs text-gray-600">Free Economy</div>
                <div className="text-xs text-gray-500 mt-1">Regular seats with basic comfort</div>
              </div>
            </div>

            {/* Premium Seats */}
            <div className="flex flex-col items-center gap-2 p-3 bg-white rounded-lg shadow-sm">
              <div className="w-8 h-8 bg-white border-2 border-blue-500 rounded-lg flex items-center justify-center text-sm font-bold text-blue-600 relative">
                B
                <span className="absolute bottom-0 right-0 text-xs text-blue-500">+</span>
              </div>
              <div className="text-center">
                <div className="font-semibold text-blue-600">PREMIUM</div>
                <div className="text-xs text-gray-600">Extra Comfort</div>
                <div className="text-xs text-gray-500 mt-1">
                  Extra leg space (L), Power outlets (EC/US), Front cabin (FC)
                </div>
              </div>
            </div>

            {/* Preferred Seats */}
            <div className="flex flex-col items-center gap-2 p-3 bg-white rounded-lg shadow-sm">
              <div className="w-8 h-8 bg-white border-2 border-amber-500 rounded-lg flex items-center justify-center text-sm font-bold text-amber-600 relative">
                C
                <span className="absolute top-0 right-0 text-xs text-amber-500">₹</span>
              </div>
              <div className="text-center">
                <div className="font-semibold text-amber-600">PREFERRED</div>
                <div className="text-xs text-gray-600">Chargeable</div>
                <div className="text-xs text-gray-500 mt-1">
                  Better location seats (CH code) - Airlines charge extra
                </div>
              </div>
            </div>

            {/* Emergency Exit */}
            <div className="flex flex-col items-center gap-2 p-3 bg-white rounded-lg shadow-sm">
              <div className="w-8 h-8 bg-white border-2 border-red-500 rounded-lg flex items-center justify-center text-sm font-bold text-red-600 relative">
                D
                <span className="absolute top-0 left-0 text-xs text-red-500">⚠️</span>
              </div>
              <div className="text-center">
                <div className="font-semibold text-red-600">EMERGENCY EXIT</div>
                <div className="text-xs text-gray-600">Special Requirements</div>
                <div className="text-xs text-gray-500 mt-1">
                  Must assist in emergency (E code) - Age/fitness restrictions
                </div>
              </div>
            </div>

            {/* Selected/Unavailable */}
            <div className="flex flex-col items-center gap-2 p-3 bg-white rounded-lg shadow-sm">
              <div className="flex gap-1">
                <div className="w-6 h-6 bg-gradient-to-br from-green-400 to-green-600 border-2 border-green-500 rounded text-xs text-white flex items-center justify-center">✓</div>
                <div className="w-6 h-6 bg-gray-300 border-2 border-gray-400 rounded text-xs text-gray-600 flex items-center justify-center opacity-60">✕</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-gray-700">STATUS</div>
                <div className="text-xs text-gray-600">Selected / Taken</div>
                <div className="text-xs text-gray-500 mt-1">
                  Your picks or unavailable seats
                </div>
              </div>
            </div>
          </div>

          {/* IATA Code Explanation */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-xs text-gray-600 text-center">
              <strong>How we categorize:</strong> Based on official IATA airline codes - 
              <span className="text-blue-600">L/FC/EC = Premium</span>, 
              <span className="text-amber-600">CH = Preferred</span>, 
              <span className="text-red-600">E = Emergency Exit</span>, 
              <span className="text-green-600">Others = Standard</span>
            </div>
          </div>
        </div>

        {/* Comprehensive Feature legend */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-xs bg-yellow-50 p-3 rounded-lg">
          <div className="flex items-center gap-1">
            <span>🚼</span> Bassinet
          </div>
          <div className="flex items-center gap-1">
            <span>♿</span> Accessible
          </div>
          <div className="flex items-center gap-1">
            <span>🚪</span> Emergency Exit
          </div>
          <div className="flex items-center gap-1">
            <span>🪟</span> Window
          </div>
          <div className="flex items-center gap-1">
            <span>🔌</span> Power Outlet
          </div>
          <div className="flex items-center gap-1">
            <span>📺</span> Entertainment
          </div>
          <div className="flex items-center gap-1">
            <span>🦶</span> Leg Rest
          </div>
          <div className="flex items-center gap-1">
            <span>🚽</span> Near Lavatory
          </div>
          <div className="flex items-center gap-1">
            <span>🍽️</span> Near Galley
          </div>
          <div className="flex items-center gap-1">
            <span>✈️</span> Overwing
          </div>
          <div className="flex items-center gap-1">
            <span>🐕</span> Pet Friendly
          </div>
          <div className="flex items-center gap-1">
            <span>⚠️</span> Restrictions
          </div>
        </div>
      </div>

      {/* Aircraft Seat Map */}
      <div className="bg-white/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <div className="max-w-2xl mx-auto">
          {/* Aircraft container */}
          <div className="bg-gradient-to-b from-gray-100 to-white rounded-t-full rounded-b-lg p-8 relative">
            {/* Aircraft nose */}
            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 w-20 h-16 bg-gradient-to-b from-gray-400 to-gray-100 rounded-t-full"></div>
            
            {/* Seat rows */}
            <div className="space-y-2 pt-6">
              {Array.from({ length: totalRows }).map((_, rowIndex) => {
                const rowNum = rowRange.first + rowIndex
                const isExitRow = rowNum === 30 // Assuming row 30 is exit row
                
                return (
                  <div key={rowNum} className={cn(
                    "grid gap-1 items-center justify-center",
                    isExitRow && "bg-blue-50 border-2 border-dashed border-blue-400 rounded-lg p-2 my-2"
                  )} style={{ gridTemplateColumns: '30px repeat(3, 40px) 60px repeat(3, 40px) 60px repeat(3, 40px) 30px' }}>
                    {/* Row number left */}
                    <div className="text-center text-sm font-semibold text-gray-600">{rowNum}</div>
                    
                    {/* Seats with proper spacing */}
                    {['A', 'B', 'C', '', 'D', 'E', 'F', '', 'H', 'J', 'K'].map((col, colIndex) => {
                      if (col === '') return <div key={`aisle-${colIndex}`} className="w-15"></div>
                      
                      const seatId = `${rowNum}${col}`
                      const seatInfo = getSeatInfo(seatId)
                      const isAvailable = isSeatAvailable(seatId)
                      const seatType = seatInfo ? getSeatType(seatInfo) : 'standard'
                      const isSelected = selectedSeats.includes(seatId)
                      const price = getSeatPrice(seatId)
                      const features = seatInfo ? getSeatFeatures(seatInfo) : []
                      const restrictions = seatInfo ? getSeatRestrictions(seatInfo) : []
                      const icons = seatInfo ? getSeatIcons(seatInfo) : []
                      
                      let seatClasses = "w-10 h-10 rounded-lg border-2 cursor-pointer transition-all duration-300 relative flex items-center justify-center text-xs font-semibold hover:scale-110"
                      
                      if (!isAvailable || !seatInfo) {
                        seatClasses += " bg-gray-300 border-gray-400 cursor-not-allowed opacity-60"
                      } else if (isSelected) {
                        seatClasses += " bg-gradient-to-br from-green-400 to-green-600 border-green-500 text-white shadow-lg scale-105"
                      } else {
                        switch (seatType) {
                          case 'premium':
                            seatClasses += " bg-white border-blue-500 text-blue-600 hover:bg-blue-50"
                            break
                          case 'preferred':
                            seatClasses += " bg-white border-amber-500 text-amber-600 hover:bg-amber-50"
                            break
                          case 'exit':
                            seatClasses += " bg-white border-red-500 text-red-600 hover:bg-red-50"
                            break
                          default: // standard
                            seatClasses += " bg-white border-green-500 text-green-600 hover:bg-green-50"
                        }
                      }

                      return (
                        <div key={seatId} className="relative">
                          <button
                            className={cn(seatClasses, "group")}
                            onClick={() => handleSeatSelect(seatId)}
                            disabled={!isAvailable || !seatInfo}
                          >
                            {col}
                            {/* Price indicator */}
                            {seatType === 'preferred' && !isSelected && (
                              <span className="absolute top-0 right-0 text-xs text-amber-500">{getCurrencyIndicator(getSeatCurrency())}</span>
                            )}
                            {seatType === 'premium' && !isSelected && (
                              <span className="absolute bottom-0 right-0 text-xs text-blue-500">+</span>
                            )}
                            {seatType === 'exit' && !isSelected && (
                              <span className="absolute top-0 left-0 text-xs text-red-500">⚠️</span>
                            )}
                            {/* Icons */}
                            {icons.length > 0 && (
                              <div className="absolute -top-1 -right-1 flex gap-1">
                                {icons.slice(0, 2).map((icon, i) => (
                                  <span key={i} className="text-xs">{icon}</span>
                                ))}
                              </div>
                            )}
                            
                            {/* Tooltip - Now attached directly to button with group-hover */}
                            {(isAvailable && seatInfo) && (
                              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                                <div className="bg-gray-900 text-white text-xs rounded-lg p-3 whitespace-nowrap min-w-36 shadow-lg">
                                  <div className="font-bold mb-1 pb-1 border-b border-gray-600">
                                    Seat {seatId} - {formatCurrencyForDisplay(price, getSeatCurrency())}
                                  </div>
                                  <div className="space-y-1">
                                    {features.slice(0, 3).map((feature, i) => (
                                      <div key={i}>• {feature}</div>
                                    ))}
                                  </div>
                                  {restrictions.length > 0 && (
                                    <div className="mt-2 pt-2 border-t border-gray-600 text-yellow-400">
                                      ⚠️ {restrictions.join(', ')}
                                    </div>
                                  )}
                                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-6 border-transparent border-t-gray-900"></div>
                                </div>
                              </div>
                            )}
                          </button>
                        </div>
                      )
                    })}
                    
                    {/* Row number right */}
                    <div className="text-center text-sm font-semibold text-gray-600">{rowNum}</div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Selected seats summary with passenger assignments */}
      {selectedSeats.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h4 className="font-semibold text-green-800">
                Selected Seats ({selectedSeats.length}/{passengers.length})
              </h4>
            </div>
            <div className="text-right">
              <div className="text-sm text-green-600">Total Seat Fees</div>
              <div className="font-bold text-xl text-green-800">
                {formatCurrency(getTotalPrice(), getSeatCurrency())}
              </div>
            </div>
          </div>
          
          {/* Passenger-Seat Assignment */}
          <div className="space-y-2">
            {passengers.map((passenger, index) => {
              const assignedSeat = selectedSeats[index]
              const seatPrice = assignedSeat ? getSeatPrice(assignedSeat) : 0
              
              return (
                <div key={passenger.objectKey} className="flex items-center justify-between bg-white rounded-lg p-2 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                    <span className="font-medium text-gray-900">
                      {passenger.name || `Passenger ${index + 1}`}
                    </span>
                  </div>
                  <div className="text-right">
                    {assignedSeat ? (
                      <div>
                        <div className="font-semibold text-green-700">Seat {assignedSeat}</div>
                        <div className="text-xs text-green-600">
                          {formatCurrencyForDisplay(seatPrice, getSeatCurrency())}
                        </div>
                      </div>
                    ) : (
                      <div className="text-gray-500">No seat selected</div>
                    )}
                  </div>
                </div>
              )
            })}
            
            {/* Selection Status */}
            <div className="flex items-center justify-center pt-2">
              {selectedSeats.length === passengers.length ? (
                <div className="text-green-600 text-sm font-medium">✅ All passengers have seats</div>
              ) : (
                <div className="text-amber-600 text-sm font-medium">
                  ⚠️ {passengers.length - selectedSeats.length} passenger(s) need seats
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
