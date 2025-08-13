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

// IATA Seat Characteristic Codes mapping
const seatCodes = {
  '1': 'Restricted seat',
  '9': 'Center seat',
  'A': 'Aisle seat',
  'B': 'Bassinet facility',
  'CH': 'Chargeable seat',
  'E': 'Emergency exit',
  'FC': 'Front of cabin',
  'H': 'Handicapped facilities',
  'IE': 'Not suitable for child',
  'K': 'Bulkhead seat',
  'L': 'Extra leg space',
  'LS': 'Left side',
  'OW': 'Overwing',
  'RS': 'Right side',
  'W': 'Window seat',
  'AL': 'Adjacent to lavatory',
  '1A': 'No infants allowed',
  '1B': 'No medical passengers',
  '1C': 'No unaccompanied minors',
  '1D': 'Restricted recline'
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

  // Load seat availability from backend
  useEffect(() => {
    const loadSeatAvailability = async () => {
      if (!flightPriceResponse) return

      setLoading(true)
      setError(null)

      try {
        // Check cache first
        const cacheResponse = await api.checkSeatAvailabilityCache(flightPriceResponse, segmentKey)
        
        let seatData = null
        
        if (cacheResponse.data?.cache_hit) {
          console.log("SeatAvailability cache hit")
          seatData = cacheResponse.data.data
        } else {
          console.log("SeatAvailability cache miss, fetching from API")
          const response = await api.getSeatAvailability(flightPriceResponse, segmentKey)
          seatData = response.data
        }

        if (seatData?.flights?.[0]?.cabin?.[0]?.seatDisplay) {
          const seatDisplay = seatData.flights[0].cabin[0].seatDisplay
          setSeatMap({
            columns: seatDisplay.columns?.map((col: any) => col.value) || [],
            rows: seatDisplay.rows || { first: 1, last: 30 },
            components: seatDisplay.component || []
          })
        }

        if (seatData?.dataLists?.seatList?.seats) {
          setSeats(seatData.dataLists.seatList.seats)
        } else {
          // Create mock data for fallback
          setSeats([])
          setSeatMap({
            columns: ["A", "B", "C", "", "D", "E", "F"],
            rows: { first: 1, last: 30 },
            components: []
          })
        }
      } catch (err) {
        console.error("Error loading seat availability:", err)
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

    loadSeatAvailability()
  }, [flightPriceResponse, segmentKey])

  const getSeatInfo = (seatId: string): Seat | null => {
    return seats.find(seat => {
      const row = seat.location.row.number.value
      const column = seat.location.column
      return `${row}${column}` === seatId
    })
  }

  const getSeatType = (seat: Seat): 'standard' | 'premium' | 'exit' | 'preferred' => {
    if (!seat.location.characteristics?.characteristic) return 'standard'
    
    const codes = seat.location.characteristics.characteristic.map(c => c.code)
    
    if (codes.includes('E')) return 'exit' // Emergency exit gets priority
    if (codes.includes('FC') || codes.includes('K') || codes.includes('L')) return 'premium' // Front cabin, bulkhead, or extra leg space
    if (codes.includes('CH') && seat.price?.total?.value && seat.price.total.value > 0) return 'preferred' // Chargeable seats
    
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
    
    if (codes.includes('B')) icons.push('🚼')
    if (codes.includes('H')) icons.push('♿')
    if (codes.includes('AL')) icons.push('🚽')
    if (codes.includes('1A') || codes.includes('1B') || codes.includes('1C') || codes.includes('IE')) icons.push('⚠️')
    if (codes.includes('OW')) icons.push('✈️')
    
    return icons
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
    if (!isSeatAvailable(seatId)) return

    const currentlySelected = selectedSeats.includes(seatId)
    let newSelectedSeats: string[]

    if (currentlySelected) {
      // Deselect: Remove the seat from the array
      newSelectedSeats = selectedSeats.filter(s => s !== seatId)
    } else {
      // Select: Add the seat to the array
      newSelectedSeats = [...selectedSeats, seatId]
    }
    
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
          <h2 className="text-xl font-bold text-gray-900">Select Your Seat - {flightType}</h2>
        </div>
        {error && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm text-yellow-800">
            ⚠️ {error}
          </div>
        )}

        {/* Seat Type Guide Banner */}
        <div className="bg-gradient-to-r from-blue-50 via-yellow-50 to-green-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex gap-6 flex-wrap items-center justify-around">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-white border-2 border-green-500 rounded-lg"></div>
              <div>
                <div className="font-semibold text-green-600">FREE</div>
                <div className="text-xs text-gray-600">Standard</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-white border-2 border-amber-500 rounded-lg relative">
                <span className="absolute top-0 right-0 text-xs text-amber-500">₹</span>
              </div>
              <div>
                <div className="font-semibold text-amber-600">PREFERRED</div>
                <div className="text-xs text-gray-600">Extra cost</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-white border-2 border-blue-500 rounded-lg relative">
                <span className="absolute bottom-0 right-0 text-xs text-blue-500">+</span>
              </div>
              <div>
                <div className="font-semibold text-blue-600">EXTRA SPACE</div>
                <div className="text-xs text-gray-600">Premium</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-gradient-to-br from-green-400 to-green-600 border-2 border-green-500 rounded-lg"></div>
              <div>
                <div className="font-semibold text-green-600">✓ SELECTED</div>
                <div className="text-xs text-gray-600">Your choice</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-gray-300 border-2 border-gray-400 rounded-lg opacity-60 relative">
                <span className="absolute inset-0 flex items-center justify-center text-gray-600">✕</span>
              </div>
              <div>
                <div className="font-semibold text-gray-600">TAKEN</div>
                <div className="text-xs text-gray-600">Unavailable</div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature legend */}
        <div className="flex gap-4 flex-wrap text-xs bg-yellow-50 p-3 rounded-lg">
          <div className="flex items-center gap-1">
            <span>🚼</span> Bassinet
          </div>
          <div className="flex items-center gap-1">
            <span>♿</span> Accessible
          </div>
          <div className="flex items-center gap-1">
            <span>⚠️</span> Restrictions
          </div>
          <div className="flex items-center gap-1">
            <span>🚽</span> Near Lavatory
          </div>
          <div className="flex items-center gap-1">
            <span>✈️</span> Overwing
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
                            seatClasses += " bg-white border-blue-500 text-blue-600 hover:bg-blue-50"
                            break
                          default:
                            seatClasses += " bg-white border-green-500 text-green-600 hover:bg-green-50"
                        }
                      }

                      return (
                        <div key={seatId} className="relative group">
                          <button
                            className={seatClasses}
                            onClick={() => handleSeatSelect(seatId)}
                            disabled={!isAvailable || !seatInfo}
                          >
                            {col}
                            {/* Price indicator */}
                            {seatType === 'preferred' && !isSelected && (
                              <span className="absolute top-0 right-0 text-xs text-amber-500">₹</span>
                            )}
                            {seatType === 'premium' && !isSelected && (
                              <span className="absolute bottom-0 right-0 text-xs text-blue-500">+</span>
                            )}
                            {/* Icons */}
                            {icons.length > 0 && (
                              <div className="absolute -top-1 -right-1 flex gap-1">
                                {icons.slice(0, 2).map((icon, i) => (
                                  <span key={i} className="text-xs">{icon}</span>
                                ))}
                              </div>
                            )}
                          </button>
                          
                          {/* Tooltip */}
                          {(isAvailable && seatInfo) && (
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50">
                              <div className="bg-gray-900 text-white text-xs rounded-lg p-3 whitespace-nowrap min-w-36 shadow-lg">
                                <div className="font-bold mb-1 pb-1 border-b border-gray-600">
                                  Seat {seatId} - {price > 0 ? `₹${price.toLocaleString('en-IN')}` : 'FREE'}
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

      {/* Selected seats summary */}
      {selectedSeats.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-green-800">Selected Seats ({selectedSeats.length})</h4>
              <p className="text-sm text-green-600">
                {selectedSeats.join(", ")}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-green-600">Total Seat Fees</div>
              <div className="font-bold text-xl text-green-800">
                {getSeatCurrency()} {getTotalPrice().toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
