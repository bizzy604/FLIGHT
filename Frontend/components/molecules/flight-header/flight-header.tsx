"use client"

import { memo } from "react"
import Image from "next/image"
import { Badge } from "@/components/ui/badge"
import type { FlightOffer } from "@/types/flight-api"

interface FlightHeaderProps {
  flight: FlightOffer
  searchParams?: {
    tripType?: string
  }
  className?: string
}

export const FlightHeader = memo(function FlightHeader({
  flight,
  searchParams,
  className
}: FlightHeaderProps) {
  return (
    <div className={`mb-4 flex items-center ${className || ''}`}>
      <div className="flex items-center">
        <Image
          src={flight.airline?.logo || "/placeholder-logo.svg"}
          alt={flight.airline?.name || "Airline"}
          width={32}
          height={32}
          className="mr-3 rounded"
        />
        <div>
          <div className="font-semibold text-sm">{flight.airline?.name}</div>
          <div className="text-xs text-muted-foreground">
            {flight.segments?.map((segment, index) => (
              <span key={`flight-${flight.id}-segment-${index}-${segment.airline?.flightNumber || 'unknown'}`}>
                {segment.airline?.flightNumber}
                {index < (flight.segments?.length || 0) - 1 && ", "}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="ml-auto flex items-center space-x-2">
        {flight.fare?.fareFamily && (
          <Badge variant="secondary">
            {flight.fare.fareFamily}
          </Badge>
        )}
        {searchParams?.tripType === 'round-trip' && (
          <Badge variant="outline">
            Round Trip
          </Badge>
        )}
      </div>
    </div>
  )
})

FlightHeader.displayName = "FlightHeader"