"use client"

import * as React from "react"
import { useState, useEffect, useMemo, useCallback } from "react"

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
  pricingRefs?: string[]  // 🚀 NEW: Pricing ObjectKeys for OrderCreate mapping
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

interface CabinSection {
  index: number
  seatDisplay?: {
    columns?: Array<{
      value: string
      position: string
    }>
    rows?: {
      first: number
      last: number
      upperDeckInd: boolean
    }
    component?: Array<{
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
  code?: string
  cabinLayout?: any
  separationType?: string
}

interface SeatMap {
  cabinSections: CabinSection[]
  columns?: Array<{
    value: string
    position: string
  }>
  rows?: {
    first: number
    last: number
    upperDeckInd: boolean
  }
  component?: Array<{
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
  onSeatChange: (flightType: 'outbound' | 'return', updatedSeats: string[], pricingRefs: string[], totalPrice?: number) => void
  passengers: Array<{
    objectKey: string
    name: string
    type: string
  }>
  className?: string
  // 🚀 NEW: Preloaded data from parent component
  preloadedData?: any
  loading?: boolean
  error?: string | null
}

// 🧠 INTELLIGENT CABIN SEPARATION HELPERS
const getSectionDisplayName = (cabin: any): string => {
  const separationType = cabin.separationType
  const isUpperDeck = cabin.seatDisplay?.rows?.upperDeckInd
  const cabinIndex = cabin.index

  // Priority-based naming logic
  if (isUpperDeck) {
    return separationType === 'upper_deck_start' ? '🔼 Upper Deck' : `🔼 Upper Deck ${cabinIndex}`
  }

  switch (separationType) {
    case 'aircraft_nose':
      return '✈️ Front Section'
    case 'front_section':
      return '🎭 Premium Section'
    case 'forward_section':
      return '⬆️ Forward Cabin'
    case 'mid_section':
      return '🎯 Mid Cabin'
    case 'rear_section':
      return '⬇️ Rear Cabin'
    case 'tail_section':
      return '🔚 Tail Section'
    case 'exit_row_section':
      return '🚪 Exit Row Area'
    case 'major_separation':
      return `🛫 Section ${cabinIndex}`
    case 'significant_gap':
      return `🏢 Cabin ${cabinIndex}`
    case 'minor_gap':
      return `📍 Area ${cabinIndex}`
    case 'wider_section':
      return `📐 Wide Section`
    case 'narrower_section':
      return `📐 Narrow Section`
    default:
      return `Cabin ${cabinIndex}`
  }
}

const getCabinClassName = (code: string): string => {
  const classMap: Record<string, string> = {
    'F': 'First Class',
    'J': 'Business Class',
    'W': 'Premium Economy',
    'Y': 'Economy Class',
    'C': 'Business Class'
  }
  return classMap[code] || 'Economy Class'
}

const getSeparationDescription = (separationType: string): string => {
  const descriptions: Record<string, string> = {
    'aircraft_nose': 'Nose',
    'upper_deck_start': 'Upper Deck',
    'upper_deck_continue': 'Upper Deck',
    'upper_deck_end': 'Main Deck',
    'class_change_F_to_J': 'First → Business',
    'class_change_J_to_W': 'Business → Premium Economy',
    'class_change_W_to_Y': 'Premium Economy → Economy',
    'class_change_J_to_Y': 'Business → Economy',
    'major_separation': 'Major Gap',
    'significant_gap': 'Service Area',
    'minor_gap': 'Small Gap',
    'exit_row_section': 'Emergency Exit',
    'front_section': 'Front',
    'forward_section': 'Forward',
    'mid_section': 'Mid',
    'rear_section': 'Rear',
    'tail_section': 'Tail',
    'wider_section': 'Wider Body',
    'narrower_section': 'Narrower Body'
  }
  return descriptions[separationType] || 'Standard'
}

const getSeparationStyling = (separationType: string): string => {
  // Color coding based on separation significance
  if (separationType.includes('upper_deck')) {
    return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
  }
  if (separationType.includes('class_change')) {
    return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
  }
  if (separationType === 'major_separation') {
    return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
  }
  if (separationType.includes('exit')) {
    return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
  }
  if (separationType === 'aircraft_nose') {
    return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
  }
  // Default styling for minor gaps and standard sections
  return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
}

export function SeatSelection({ 
  flightPriceResponse, 
  flightType, 
  segmentKey,
  selectedSeats, 
  onSeatChange,
  passengers,
  className,
  preloadedData,
  loading = false,
  error = null
}: SeatSelectionProps) {
  const [seats, setSeats] = useState<Seat[]>([])
  const [seatMap, setSeatMap] = useState<SeatMap | null>(null)
  const [internalError, setInternalError] = useState<string | null>(null)
  
  // Use external loading/error states when preloaded data is provided
  const isLoading = preloadedData ? loading : false
  const displayError = preloadedData ? error : internalError
  
  // 🎯 NEW: Seat filtering state
  const [activeFilter, setActiveFilter] = useState<'standard' | 'premium' | 'preferred' | 'exit' | null>(null)
  const [highlightedSeats, setHighlightedSeats] = useState<string[]>([])
  const [filterCount, setFilterCount] = useState<number>(0)

  // 🚀 HELPER FUNCTIONS: Moved before useMemo to fix hoisting issue
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

  // 🚀 NEW: Get pricing ObjectKeys for a seat position (for OrderCreate)
  const getSeatPricingRefs = (seatId: string): string[] => {
    const seatInfo = getSeatInfo(seatId)
    return seatInfo?.pricingRefs || []
  }

  // 🚀 NEW: Convert seat position to pricing ObjectKeys for backend
  const convertSeatPositionsToPricingRefs = (seatPositions: string[]): string[] => {
    const pricingRefs: string[] = []
    
    seatPositions.forEach(seatId => {
      const refs = getSeatPricingRefs(seatId)
      pricingRefs.push(...refs)
    })
    
    // Remove duplicates and return
    return Array.from(new Set(pricingRefs))
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

  // 🚀 PERFORMANCE: Pre-compute seat characteristics map (runs only when seats change)
  const seatCharacteristicsMap = useMemo(() => {
    if (!seats || seats.length === 0) return {}
    
    return seats.reduce((map, seat) => {
      const row = seat.location.row.number.value
      const column = seat.location.column
      const seatId = `${row}${column}`
      
      map[seatId] = {
        type: getSeatType(seat),
        features: getSeatFeatures(seat),
        codes: seat.location.characteristics?.characteristic?.map(c => c.code) || [],
        available: seat.availability !== 'unavailable' && seat.availability !== 'occupied'
      }
      return map
    }, {} as Record<string, { type: string; features: string[]; codes: string[]; available: boolean }>)
  }, [seats])

  // 🎯 FILTER LOGIC: Find seats matching the active filter
  const applySeatFilter = useCallback((filterType: 'standard' | 'premium' | 'preferred' | 'exit' | null) => {
    if (!filterType || Object.keys(seatCharacteristicsMap).length === 0) {
      setActiveFilter(null)
      setHighlightedSeats([])
      setFilterCount(0)
      return
    }

    const matchingSeats = Object.keys(seatCharacteristicsMap).filter(seatId => {
      const seatChar = seatCharacteristicsMap[seatId]
      return seatChar.type === filterType && seatChar.available
    })

    setActiveFilter(filterType)
    setHighlightedSeats(matchingSeats)
    setFilterCount(matchingSeats.length)
    
    logger.info(`🎯 Applied ${filterType} filter: ${matchingSeats.length} seats found`)
  }, [seatCharacteristicsMap])

  // 🔄 TOGGLE FILTER: Click same filter to clear, click different to switch
  const toggleSeatFilter = useCallback((filterType: 'standard' | 'premium' | 'preferred' | 'exit' | null) => {
    if (activeFilter === filterType) {
      // Clear filter if clicking the same type
      applySeatFilter(null)
    } else {
      // Apply new filter
      applySeatFilter(filterType)
    }
  }, [activeFilter, applySeatFilter])

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
    
    // 🚀 NEW: Check for API errors that indicate no seats available
    if (actualData?.Errors?.Error || actualData?.error) {
      const errorMessage = actualData?.Errors?.Error?.[0]?.value || actualData?.error?.message || 'Seat availability error'
      logger.warn('⚠️ API returned error - no seats available:', errorMessage)
      setSeats([])
      setSeatMap(null)
      setInternalError(`Seat selection unavailable: ${errorMessage}`)
      return
    }
    
    // Set seat display configuration from all cabin sections
    if (actualData?.flights?.[0]?.cabin) {
      const cabinSections = actualData.flights[0].cabin
      logger.info(`🛫 Processing ${cabinSections.length} cabin sections`)
      
      // Set combined configuration for all cabins
      const allCabinSections = cabinSections.map((cabin: any, index: number) => ({
        index: index + 1,
        seatDisplay: cabin.seatDisplay,
        code: cabin.code || 'Y',
        cabinLayout: cabin.cabinLayout || {}
      }))
      
      setSeatMap({ cabinSections: allCabinSections })
      
      logger.info('✅ Set multi-cabin seat map configuration from response:', {
        cabin_count: allCabinSections.length,
        cabin_details: allCabinSections.map((cabin: CabinSection) => ({
          index: cabin.index,
          columns_count: cabin.seatDisplay?.columns?.length || 0,
          row_range: cabin.seatDisplay?.rows,
          is_upper_deck: cabin.seatDisplay?.rows?.upperDeckInd || false
        }))
      })
    } else {
      logger.warn('⚠️ No cabin sections found, using fallback configuration')
      setSeatMap({
        cabinSections: [{
          index: 1,
          seatDisplay: {
            columns: [
              {value: "A", position: "left"}, 
              {value: "B", position: "center"}, 
              {value: "C", position: "aisle"}, 
              {value: "D", position: "aisle"}, 
              {value: "E", position: "center"}, 
              {value: "F", position: "right"}
            ],
            rows: { first: 1, last: 30, upperDeckInd: false },
            component: []
          },
          code: 'Y',
          cabinLayout: {}
        }]
      })
    }

    // Set seats data - check multiple possible locations
    let seatsArray = null
    
    if (actualData?.dataLists?.seatList?.seats) {
      seatsArray = actualData.dataLists.seatList.seats
      // logger.info(`✅ Found ${seatsArray.length} seats in dataLists.seatList.seats`)
    } else if (actualData?.dataLists?.seats) {
      seatsArray = actualData.dataLists.seats
      // logger.info(`✅ Found ${seatsArray.length} seats in dataLists.seats`)
    } else if (actualData?.seats) {
      seatsArray = actualData.seats
      // logger.info(`✅ Found ${seatsArray.length} seats in top-level seats`)
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
      
      // 🚀 CRITICAL FIX: Validate seat map against actual seat data
      if (rows.length > 0) {
        logger.info('🔧 Validated multi-cabin seat map against actual seat data:', {
          min_row: minRow,
          max_row: maxRow,
          total_rows_with_seats: rows.length,
          total_seats: seatsArray.length
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
      logger.warn('⚠️ No seats found in response - seats not available')
      // Set empty state - no fallback seat map
      setSeats([])
      setSeatMap(null)
    }
  }

  // 🚀 UPDATED: Use preloaded data when available
  useEffect(() => {
    if (preloadedData) {
      // Use preloaded data from parent component
      logger.info('⚡ SeatSelection using preloaded data from parent component')
      processSeatAvailabilityData(preloadedData)
      return
    }
    
    // 🚫 LEGACY: Only fallback to individual loading if no preloaded data
    if (!flightPriceResponse) return
    
    logger.warn('⚠️ SeatSelection falling back to individual data loading (should be avoided)')
    loadSeatAvailabilityFallback()
  }, [flightPriceResponse, preloadedData])
  
  const loadSeatAvailabilityFallback = async () => {
    setInternalError(null)

    try {
      logger.info('🪑 Loading seat availability data (fallback)...')
      
      // Check simple cache manager first
      const sessionId = localStorage.getItem('flight_session_id')
      if (sessionId) {
        const simpleCacheManager = await import('@/utils/simple-cache-manager')
        const proactiveCacheResult = simpleCacheManager.simpleCacheManager.getSeatAvailability(sessionId)
        
        if (proactiveCacheResult.success && proactiveCacheResult.data) {
          logger.info('⚡ Using cached seat data in fallback!')
          processSeatAvailabilityData(proactiveCacheResult.data)
          return
        }
      }

      // Final fallback to API
      logger.info('💻 Making direct seat API call (fallback)')
      const response = await api.getSeatAvailability(flightPriceResponse, segmentKey)
      processSeatAvailabilityData(response.data)
      
    } catch (err) {
      logger.error("❌ Error in seat availability fallback:", err)
      setInternalError("Failed to load seat map. Seats may not be available for this flight.")
      // Set empty state - no fallback seat map
      setSeatMap(null)
      setSeats([])
    }


  }

  // 🔍 DEBUG: Log dynamic layout information for all cabins
  useEffect(() => {
    if (seatMap?.cabinSections && seatMap.cabinSections.length > 0) {
      logger.info('🚀 MULTI-CABIN SEAT LAYOUT:', {
        total_cabins: seatMap.cabinSections.length,
        cabin_details: seatMap.cabinSections.map((cabin: CabinSection) => ({
          cabin_index: cabin.index,
          cabin_code: cabin.code,
          columns: cabin.seatDisplay?.columns?.map((col: any) => col.value) || [],
          column_count: cabin.seatDisplay?.columns?.length || 0,
          row_range: `${cabin.seatDisplay?.rows?.first}-${cabin.seatDisplay?.rows?.last}`,
          is_upper_deck: cabin.seatDisplay?.rows?.upperDeckInd || false
        }))
      })
    }
  }, [seatMap?.cabinSections])

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
    
    // 🚀 CRITICAL FIX: Convert seat positions to pricing ObjectKeys for OrderCreate
    const pricingRefs = convertSeatPositionsToPricingRefs(newSelectedSeats)
    
    logger.info(`🪑 Seat selection changed from [${selectedSeats.join(', ')}] to [${newSelectedSeats.join(', ')}]`)
    logger.info(`🎯 Pricing ObjectKeys for OrderCreate: [${pricingRefs.join(', ')}]`)
    
    // Calculate the total price for the new selection
    const totalPrice = newSelectedSeats.reduce((total, seatId) => {
      return total + getSeatPrice(seatId)
    }, 0)
    
    // Pass seat positions, pricing refs, and actual total price
    onSeatChange(flightType, newSelectedSeats, pricingRefs, totalPrice)
  }

  const getTotalPrice = (): number => {
    return selectedSeats.reduce((total, seatId) => {
      return total + getSeatPrice(seatId)
    }, 0)
  }

  if (isLoading) {
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

  if (displayError && !seatMap) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Seat Selection - {flightType}</CardTitle>
          <CardDescription className="text-red-600">{displayError}</CardDescription>
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

  // 🚀 NEW: Handle no seats available state (only when not loading and no error)
  if (!isLoading && !displayError && (!seatMap?.cabinSections || seats.length === 0)) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Seat Selection - {flightType}</CardTitle>
          <CardDescription>Seat availability information</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <div className="mb-6">
              <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No Seats Available
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4 max-w-md mx-auto">
                We're sorry, but seat selection is not available for this flight at the moment. 
                This could be due to airline restrictions or technical limitations.
              </p>
              {displayError && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 mb-4 max-w-md mx-auto">
                  <div className="flex items-center gap-2 text-sm text-yellow-800 dark:text-yellow-200">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    {displayError}
                  </div>
                </div>
              )}
              <div className="text-sm text-gray-500 dark:text-gray-400">
                You can still proceed with your booking and seats will be assigned by the airline.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const cabinSections = seatMap?.cabinSections || []

  // 🚀 DYNAMIC LAYOUT: Generate grid template and column layout for each cabin section
  const generateDynamicLayoutForCabin = (cabinColumns: string[]) => {
    if (!cabinColumns.length) {
      // Fallback to standard 3-3-3 layout
      return {
        gridTemplate: '30px repeat(3, 40px) 60px repeat(3, 40px) 60px repeat(3, 40px) 30px',
        columnLayout: ['A', 'B', 'C', '', 'D', 'E', 'F', '', 'H', 'J', 'K']
      }
    }

    // Create dynamic column layout with aisles
    const columnLayout = []
    let gridTemplate = '30px ' // Row number column
    
    // 🚀 INTELLIGENT AISLE PLACEMENT: Detect aisle positions based on column letters
    const getAislePositions = (cols: string[]) => {
      const aisles = []
      
      // Look for natural break points in the alphabet sequence
      for (let i = 1; i < cols.length; i++) {
        const currentChar = cols[i].charCodeAt(0)
        const prevChar = cols[i-1].charCodeAt(0)
        
        // If there's a gap in the alphabet (e.g., C to E, F to H), add an aisle
        if (currentChar - prevChar > 1) {
          aisles.push(i)
        }
      }
      
      // If no natural breaks found, use standard configurations
      if (aisles.length === 0) {
        const standardConfigs: Record<number, number[]> = {
          6: [3],           // ABC DEF
          7: [3],           // ABC DEFG  
          8: [2, 6],        // AB CDEF GH
          9: [3, 6],        // ABC DEF GHI
          10: [3, 7],       // ABC DEFG HIJ
          11: [3, 8],       // ABC DEFGH IJK
          12: [3, 9]        // ABC DEFGHI JKL
        }
        return standardConfigs[cols.length] || []
      }
      
      return aisles
    }

    const aislePositions = getAislePositions(cabinColumns)
    
    for (let i = 0; i < cabinColumns.length; i++) {
      const column = cabinColumns[i]
      
      // Add aisle space before this column if it's an aisle position
      if (aislePositions.includes(i)) {
        columnLayout.push('')
        gridTemplate += '60px ' // Aisle space
      }
      
      columnLayout.push(column)
      gridTemplate += '40px ' // Seat column
    }
    
    gridTemplate += '30px' // Row number column (right side)
    
    return { gridTemplate, columnLayout }
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-6 bg-purple-600 rounded-full"></div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Complete Seat Map - {flightType}</h2>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          All seats are shown for your reference. Choose any available seat that fits your needs and budget.
          {cabinSections.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {cabinSections.map((cabin: CabinSection, index: number) => {
                const columns = cabin.seatDisplay?.columns?.map((col: any) => col.value) || []
                const isUpperDeck = cabin.seatDisplay?.rows?.upperDeckInd || false
                return (
                  <span key={index} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-md text-xs font-medium">
                    {isUpperDeck ? '🔼 Upper Deck' : `Cabin ${cabin.index}`}: {columns.length}-col ({columns.join('')})
                  </span>
                )
              })}
            </div>
          )}
        </div>
        {displayError && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm text-yellow-800 dark:text-yellow-200">
            ⚠️ {displayError}
          </div>
        )}

        {/* Compact Seat Types Guide with Hover Tooltips */}
        <div className="bg-gradient-to-r from-blue-50 via-purple-50 to-green-50 dark:from-blue-900/20 dark:via-purple-900/20 dark:to-green-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">🪑 Seat Guide</h3>
            <p className="text-xs text-gray-600 dark:text-gray-300">Hover over icons for details</p>
          </div>
          
          {/* Compact Seat Types Row */}
          <div className="flex items-center justify-center gap-6 mb-4">
            
            {/* Standard Seats */}
            <div className="group relative">
              <button
                onClick={() => toggleSeatFilter('standard')}
                className={cn(
                  "w-10 h-10 border-2 border-primary-500 rounded-lg flex items-center justify-center text-sm font-bold text-primary-600 cursor-pointer hover:scale-110 transition-all duration-200",
                  activeFilter === 'standard' 
                    ? "bg-primary-500 text-white shadow-lg ring-2 ring-primary-300" 
                    : "bg-white dark:bg-gray-700 hover:bg-primary-50 dark:hover:bg-primary-900/20"
                )}
              >
                A
              </button>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                  <div className="font-semibold text-primary-400">STANDARD</div>
                  <div>Free Economy Seats</div>
                  <div className="text-gray-300 dark:text-gray-600">Click to highlight on seat map</div>
                </div>
              </div>
            </div>

            {/* Premium Seats */}
            <div className="group relative">
              <button
                onClick={() => toggleSeatFilter('premium')}
                className={cn(
                  "w-10 h-10 border-2 border-blue-500 rounded-lg flex items-center justify-center text-sm font-bold text-blue-600 cursor-pointer hover:scale-110 transition-all duration-200 relative",
                  activeFilter === 'premium' 
                    ? "bg-blue-500 text-white shadow-lg ring-2 ring-blue-300" 
                    : "bg-white dark:bg-gray-700 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                )}
              >
                B
                <span className={cn(
                  "absolute -top-1 -right-1 text-xs",
                  activeFilter === 'premium' ? "text-blue-200" : "text-blue-500"
                )}>+</span>
              </button>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                  <div className="font-semibold text-blue-400">PREMIUM</div>
                  <div>Extra Comfort Seats</div>
                  <div className="text-gray-300 dark:text-gray-600">Click to highlight on seat map</div>
                </div>
              </div>
            </div>

            {/* Preferred Seats */}
            <div className="group relative">
              <button
                onClick={() => toggleSeatFilter('preferred')}
                className={cn(
                  "w-10 h-10 border-2 border-amber-500 rounded-lg flex items-center justify-center text-sm font-bold text-amber-600 cursor-pointer hover:scale-110 transition-all duration-200 relative",
                  activeFilter === 'preferred' 
                    ? "bg-amber-500 text-white shadow-lg ring-2 ring-amber-300" 
                    : "bg-white dark:bg-gray-700 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                )}
              >
                C
                <span className={cn(
                  "absolute -top-1 -right-1 text-xs",
                  activeFilter === 'preferred' ? "text-amber-200" : "text-amber-500"
                )}>₹</span>
              </button>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                  <div className="font-semibold text-amber-400">PREFERRED</div>
                  <div>Chargeable Location</div>
                  <div className="text-gray-300 dark:text-gray-600">Click to highlight on seat map</div>
                </div>
              </div>
            </div>

            {/* Emergency Exit */}
            <div className="group relative">
              <button
                onClick={() => toggleSeatFilter('exit')}
                className={cn(
                  "w-10 h-10 border-2 border-red-500 rounded-lg flex items-center justify-center text-sm font-bold text-red-600 cursor-pointer hover:scale-110 transition-all duration-200 relative",
                  activeFilter === 'exit' 
                    ? "bg-red-500 text-white shadow-lg ring-2 ring-red-300" 
                    : "bg-white dark:bg-gray-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                )}
              >
                E
                <span className={cn(
                  "absolute -top-1 -left-1 text-xs",
                  activeFilter === 'exit' ? "text-red-200" : "text-red-500"
                )}>⚠️</span>
              </button>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                  <div className="font-semibold text-red-400">EMERGENCY EXIT</div>
                  <div>Special Requirements</div>
                  <div className="text-gray-300 dark:text-gray-600">Click to highlight on seat map</div>
                </div>
              </div>
            </div>

            {/* Status Indicators */}
            <div className="group relative">
              <div className="flex gap-1">
                <div className="w-5 h-5 bg-gradient-to-br from-primary-500 to-primary-700 border border-primary-600 rounded text-xs text-white flex items-center justify-center">✓</div>
                <div className="w-5 h-5 bg-gray-300 dark:bg-gray-600 border border-gray-400 dark:border-gray-500 rounded text-xs text-gray-600 flex items-center justify-center opacity-60">✕</div>
              </div>
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
                  <div className="font-semibold">SEAT STATUS</div>
                  <div>Blue ✓ = Selected</div>
                  <div className="text-gray-300 dark:text-gray-600">Gray ✕ = Unavailable/Taken</div>
                </div>
              </div>
            </div>
          </div>

          {/* Compact Features Row with Hover Tooltips */}
          <div className="border-t border-gray-200 dark:border-gray-600 pt-3">
            <div className="flex items-center justify-center gap-4 text-lg">
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Window Seat">
                🪟
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Window Seat
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Power Outlet">
                🔌
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Power Outlet
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Entertainment">
                📺
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Entertainment
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Leg Rest">
                🦵
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Leg Rest
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Emergency Exit">
                🚨
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Emergency Exit
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Near Lavatory">
                🚽
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Near Lavatory
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Near Galley">
                🍽️
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Near Galley
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Pet Friendly">
                🐕
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Pet Friendly
                  </div>
                </div>
              </span>
              <span className="cursor-help hover:scale-125 transition-transform group relative" title="Accessible">
                ♿
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none">
                  <div className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg px-2 py-1 whitespace-nowrap shadow-lg">
                    Accessible
                  </div>
                </div>
              </span>
            </div>
          </div>

          {/* Quick Reference */}
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 text-center">
            <p className="text-xs text-gray-600 dark:text-gray-300">
              <strong>Based on IATA codes:</strong> 
              <span className="text-blue-600"> L/FC/EC = Premium</span> • 
              <span className="text-amber-600"> CH = Preferred</span> • 
              <span className="text-red-600"> E = Emergency</span> • 
              <span className="text-primary-600"> Others = Standard</span>
            </p>
          </div>
        </div>
      </div>

      {/* Filter Status Indicator */}
      {activeFilter && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
              <div>
                <div className="font-semibold text-yellow-800 dark:text-yellow-200">
                  Filtering by: {activeFilter === 'standard' ? 'Standard Seats' : 
                                activeFilter === 'premium' ? 'Premium Seats' : 
                                activeFilter === 'preferred' ? 'Preferred Seats' : 'Emergency Exit Seats'}
                </div>
                <div className="text-sm text-yellow-700 dark:text-yellow-300">
                  {filterCount} matching seats highlighted • Others faded for clarity
                </div>
              </div>
            </div>
            <button
              onClick={() => toggleSeatFilter(null)}
              className="px-4 py-2 bg-white dark:bg-gray-700 border border-yellow-300 dark:border-yellow-600 text-yellow-700 dark:text-yellow-300 rounded-lg hover:bg-yellow-50 dark:hover:bg-yellow-900/30 transition-colors duration-200 text-sm font-medium"
            >
              Clear Filter
            </button>
          </div>
        </div>
      )}

      {/* Multi-Cabin Aircraft Seat Map */}
      <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
        <div className="max-w-4xl mx-auto space-y-8">
          {cabinSections.map((cabin: CabinSection, cabinIndex: number) => {
            const columns = cabin.seatDisplay?.columns?.map((col: any) => col.value) || []
            const rowRange = cabin.seatDisplay?.rows || { first: 1, last: 30, upperDeckInd: false }
            const totalRows = rowRange.last - rowRange.first + 1
            const isUpperDeck = rowRange.upperDeckInd
            const { gridTemplate, columnLayout } = generateDynamicLayoutForCabin(columns)
            
            return (
              <div key={`cabin-${cabinIndex}`} className="relative">
                {/* Intelligent Cabin Section Header */}
                <div className="flex items-center gap-3 mb-4">
                  <div className={cn(
                    "px-3 py-1 rounded-full text-sm font-semibold",
                    isUpperDeck 
                      ? "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200" 
                      : "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200"
                  )}>
                    {getSectionDisplayName(cabin)} 
                    {cabin.code && cabin.code !== 'Y' && ` (${getCabinClassName(cabin.code)})`}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">
                    Rows {rowRange.first}-{rowRange.last} • {columns.length} columns ({columns.join('')})
                  </div>
                  {/* Separation Type Indicator */}
                  {cabin.separationType && (
                    <div className={cn(
                      "px-2 py-1 rounded text-xs font-medium",
                      getSeparationStyling(cabin.separationType)
                    )}>
                      {getSeparationDescription(cabin.separationType)}
                    </div>
                  )}
                </div>

                {/* Aircraft container for this cabin */}
                <div className={cn(
                  "bg-gradient-to-b from-gray-100 to-white dark:from-gray-700 dark:to-gray-800 rounded-lg p-6 relative",
                  isUpperDeck && "bg-gradient-to-b from-purple-100 to-purple-50 dark:from-purple-900/20 dark:to-purple-800/10 border-2 border-purple-200 dark:border-purple-700"
                )}>
                  {/* Aircraft nose (only for first cabin) */}
                  {cabinIndex === 0 && (
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 w-20 h-16 bg-gradient-to-b from-gray-400 to-gray-100 dark:from-gray-500 dark:to-gray-700 rounded-t-full"></div>
                  )}
                  
                  {/* Seat rows for this cabin */}
                  <div className="space-y-2 pt-2">
                    {Array.from({ length: totalRows }).map((_, rowIndex) => {
                      const rowNum = rowRange.first + rowIndex
                      const isExitRow = rowNum === 30 || rowNum === 40 || rowNum === 63 || rowNum === 75 // Common exit rows
                      
                      return (
                        <div key={`${cabin.index}-${rowNum}`} className={cn(
                          "grid gap-1 items-center justify-center",
                          isExitRow && "bg-blue-50 dark:bg-blue-900/20 border-2 border-dashed border-blue-400 dark:border-blue-500 rounded-lg p-2 my-2"
                        )} style={{ gridTemplateColumns: gridTemplate }}>
                          {/* Row number left */}
                          <div className="text-center text-sm font-semibold text-gray-600 dark:text-gray-300">{rowNum}</div>
                          
                          {/* Dynamic seats with proper spacing for this cabin */}
                          {columnLayout.map((col, colIndex) => {
                            if (col === '') return <div key={`cabin-${cabin.index}-aisle-${colIndex}`} className="w-15"></div>
                            
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
                            
                            // 🎯 FILTERING LOGIC: Apply highlight/fade effects based on active filter
                            if (activeFilter) {
                              const seatCharacteristics = seatCharacteristicsMap[seatId]
                              const matchesFilter = seatCharacteristics && highlightedSeats.includes(seatId)
                              
                              if (matchesFilter && isAvailable && seatInfo) {
                                // Highlight matching seats with glow effect
                                seatClasses += " ring-4 ring-yellow-400 ring-opacity-75 shadow-lg shadow-yellow-200 scale-105 z-10"
                              } else if (isAvailable && seatInfo) {
                                // Fade non-matching available seats
                                seatClasses += " opacity-40"
                              }
                            }
                            
                            if (!isAvailable || !seatInfo) {
                              seatClasses += " bg-gray-300 dark:bg-gray-600 border-gray-400 dark:border-gray-500 cursor-not-allowed opacity-60"
                            } else if (isSelected) {
                              seatClasses += " bg-gradient-to-br from-primary-500 to-primary-700 border-primary-600 text-white shadow-lg scale-105"
                            } else {
                              switch (seatType) {
                                case 'premium':
                                  seatClasses += " bg-white dark:bg-gray-700 border-blue-500 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                                  break
                                case 'preferred':
                                  seatClasses += " bg-white dark:bg-gray-700 border-amber-500 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                                  break
                                case 'exit':
                                  seatClasses += " bg-white dark:bg-gray-700 border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                                  break
                                default: // standard
                                  seatClasses += " bg-white dark:bg-gray-700 border-primary-500 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20"
                              }
                            }

                            return (
                              <div key={`${cabin.index}-${seatId}`} className="relative">
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
                                            {restrictions.join(', ')}
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
                          <div className="text-center text-sm font-semibold text-gray-600 dark:text-gray-300">{rowNum}</div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Selected seats summary with passenger assignments */}
      {selectedSeats.length > 0 && (
        <div className="bg-primary-50 border border-primary-200 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h4 className="font-semibold text-primary-800">
                Selected Seats ({selectedSeats.length}/{passengers.length})
              </h4>
            </div>
            <div className="text-right">
              <div className="text-sm text-primary-600">Total Seat Fees</div>
              <div className="font-bold text-xl text-primary-800">
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
                <div key={passenger.objectKey} className="flex items-center justify-between bg-primary-50 border border-primary-200 rounded-lg p-2 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    <span className="font-medium text-primary-800">
                      {passenger.name || `Passenger ${index + 1}`}
                    </span>
                  </div>
                  <div className="text-right">
                    {assignedSeat ? (
                      <div>
                        <div className="font-semibold text-primary-700">Seat {assignedSeat}</div>
                        <div className="text-xs text-primary-600">
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
                <div className="text-primary-600 text-sm font-medium">All passengers have seats</div>
              ) : (
                <div className="text-amber-600 text-sm font-medium">
                  {passengers.length - selectedSeats.length} passenger(s) need seats
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
