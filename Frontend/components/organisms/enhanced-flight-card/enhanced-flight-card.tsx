"use client"

import { useState } from 'react'
import { ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { 
  FlightHeader,
  FlightRouteDisplay,
  FlightSegmentDetails,
  FlightPricePanel
} from "@/components/molecules"
import { useFlightSelection } from "./use-flight-selection"
import type { FlightOffer } from "@/types/flight-api"

interface EnhancedFlightCardProps {
  flight: FlightOffer
  showExtendedDetails?: boolean
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

export function EnhancedFlightCard({ 
  flight, 
  showExtendedDetails = false, 
  searchParams 
}: EnhancedFlightCardProps) {
  const [expanded, setExpanded] = useState(showExtendedDetails)
  
  const {
    isSelecting,
    buildFlightUrl,
    handleFlightSelect
  } = useFlightSelection({ flight, searchParams })

  const flightUrl = buildFlightUrl()

  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
          {/* Flight Details */}
          <div className="p-4 md:p-6">
            {/* Flight Header - Airline info and badges */}
            <FlightHeader 
              flight={flight} 
              searchParams={searchParams}
            />

            {/* Route and Time Display */}
            <FlightRouteDisplay 
              flight={flight} 
              searchParams={searchParams}
            />

            {/* Expandable Details */}
            {expanded && (
              <div className="space-y-4">
                <Separator />
                <FlightSegmentDetails 
                  flight={flight} 
                  searchParams={searchParams}
                />
              </div>
            )}

            {/* Toggle Button */}
            <div className="mt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
                className="w-full"
              >
                {expanded ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    Show More Details
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Price and Book Button */}
          <FlightPricePanel
            flight={flight}
            flightUrl={flightUrl}
            isSelecting={isSelecting}
            onFlightSelect={handleFlightSelect}
          />
        </div>
      </CardContent>
    </Card>
  )
}