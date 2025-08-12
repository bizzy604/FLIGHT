"use client"

import { memo } from "react"
import { ArrowRight } from "lucide-react"
import type { FlightOffer } from "@/types/flight-api"

interface FlightRouteDisplayProps {
  flight: FlightOffer
  searchParams?: {
    tripType?: string
    origin?: string
    destination?: string
  }
  className?: string
}

export const FlightRouteDisplay = memo(function FlightRouteDisplay({
  flight,
  searchParams,
  className
}: FlightRouteDisplayProps) {
  if (searchParams?.tripType === 'round-trip') {
    return (
      <div className={`mb-4 ${className || ''}`}>
        <RoundTripRouteDisplay flight={flight} searchParams={searchParams} />
      </div>
    )
  }

  return (
    <div className={`mb-4 ${className || ''}`}>
      <OneWayRouteDisplay flight={flight} searchParams={searchParams} />
    </div>
  )
})

// Round-trip route display component
const RoundTripRouteDisplay = memo(function RoundTripRouteDisplay({
  flight,
  searchParams
}: {
  flight: FlightOffer
  searchParams?: { origin?: string; destination?: string }
}) {
  const segments = flight.segments || []

  // Determine outbound and return segments
  let outboundSegments: any[] = []
  let returnSegments: any[] = []

  if (segments.length > 0) {
    // Find the turnaround point (where we reach the destination)
    const searchDestination = searchParams?.destination || ''
    let turnaroundIndex = -1

    // Look for the first occurrence of the destination airport
    for (let i = 0; i < segments.length; i++) {
      if (segments[i].arrival?.airport === searchDestination) {
        turnaroundIndex = i
        break
      }
    }

    if (turnaroundIndex > -1) {
      outboundSegments = segments.slice(0, turnaroundIndex + 1)
      returnSegments = segments.slice(turnaroundIndex + 1)
    } else {
      // Fallback: split in half
      const midPoint = Math.ceil(segments.length / 2)
      outboundSegments = segments.slice(0, midPoint)
      returnSegments = segments.slice(midPoint)
    }
  }

  // Outbound journey details
  const outboundOrigin = outboundSegments[0]?.departure?.airport || searchParams?.origin || ''
  const outboundDestination = outboundSegments[outboundSegments.length - 1]?.arrival?.airport || searchParams?.destination || ''
  const outboundDepartureTime = outboundSegments[0]?.departure?.time || '--:--'
  const outboundArrivalTime = outboundSegments[outboundSegments.length - 1]?.arrival?.time || '--:--'
  const outboundStops = outboundSegments.length > 1 ? outboundSegments.length - 1 : 0

  // Return journey details
  const returnOrigin = returnSegments[0]?.departure?.airport || searchParams?.destination || ''
  const returnDestination = returnSegments[returnSegments.length - 1]?.arrival?.airport || searchParams?.origin || ''
  const returnDepartureTime = returnSegments[0]?.departure?.time || '--:--'
  const returnArrivalTime = returnSegments[returnSegments.length - 1]?.arrival?.time || '--:--'
  const returnStops = returnSegments.length > 1 ? returnSegments.length - 1 : 0

  return (
    <div className="space-y-4">
      {/* Outbound Journey */}
      <div className="flex items-center justify-between">
        <div className="text-center">
          <div className="text-xl font-bold">
            {outboundDepartureTime}
          </div>
          <div className="text-sm text-muted-foreground">
            {outboundOrigin}
          </div>
          <div className="text-xs text-muted-foreground">
            Departure
          </div>
        </div>

        <div className="flex flex-col items-center px-4">
          <div className="text-xs text-muted-foreground mb-1">
            Outbound
          </div>
          <div className="flex items-center">
            <div className="h-px bg-border flex-1 w-12"></div>
            <ArrowRight className="mx-2 h-3 w-3 text-muted-foreground" />
            <div className="h-px bg-border flex-1 w-12"></div>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {outboundStops > 0 ? `${outboundStops} stop${outboundStops > 1 ? 's' : ''}` : 'Direct'}
          </div>
        </div>

        <div className="text-center">
          <div className="text-xl font-bold">
            {outboundArrivalTime}
          </div>
          <div className="text-sm text-muted-foreground">
            {outboundDestination}
          </div>
          <div className="text-xs text-muted-foreground">
            Arrival
          </div>
        </div>
      </div>

      {/* Return Journey */}
      {returnSegments.length > 0 && (
        <div className="flex items-center justify-between border-t pt-3">
          <div className="text-center">
            <div className="text-xl font-bold">
              {returnDepartureTime}
            </div>
            <div className="text-sm text-muted-foreground">
              {returnOrigin}
            </div>
            <div className="text-xs text-muted-foreground">
              Departure
            </div>
          </div>

          <div className="flex flex-col items-center px-4">
            <div className="text-xs text-muted-foreground mb-1">
              Return
            </div>
            <div className="flex items-center">
              <div className="h-px bg-border flex-1 w-12"></div>
              <ArrowRight className="mx-2 h-3 w-3 text-muted-foreground" />
              <div className="h-px bg-border flex-1 w-12"></div>
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {returnStops > 0 ? `${returnStops} stop${returnStops > 1 ? 's' : ''}` : 'Direct'}
            </div>
          </div>

          <div className="text-center">
            <div className="text-xl font-bold">
              {returnArrivalTime}
            </div>
            <div className="text-sm text-muted-foreground">
              {returnDestination}
            </div>
            <div className="text-xs text-muted-foreground">
              Arrival
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

// One-way route display component
const OneWayRouteDisplay = memo(function OneWayRouteDisplay({
  flight,
  searchParams
}: {
  flight: FlightOffer
  searchParams?: { origin?: string; destination?: string }
}) {
  // Use route_display if available, otherwise fallback to segment logic
  const routeDisplay = flight.route_display
  const useSearchRoute = routeDisplay && searchParams?.origin && searchParams?.destination

  let originAirport: string, destinationAirport: string, originTime: string, destinationTime: string, stopInfo: string

  if (useSearchRoute) {
    // Use search parameters as authoritative source
    originAirport = searchParams.origin || ''
    destinationAirport = searchParams.destination || ''

    // Find corresponding segment times
    const firstSegment = flight.segments?.find(seg => seg.departure?.airport === originAirport)
    const lastSegment = flight.segments?.find(seg => seg.arrival?.airport === destinationAirport)

    originTime = firstSegment?.departure?.time || '--:--'
    destinationTime = lastSegment?.arrival?.time || '--:--'

    // Show stops information
    const stops = routeDisplay.stops || []
    stopInfo = stops.length > 0 ? `${stops.length} stop${stops.length > 1 ? 's' : ''} (via ${stops.join(', ')})` : 'Direct'
  } else {
    // Fallback to original segment logic
    originAirport = flight.segments?.[0]?.departure?.airport || ''
    destinationAirport = flight.segments?.[flight.segments.length - 1]?.arrival?.airport || ''
    originTime = flight.segments?.[0]?.departure?.time || '--:--'
    destinationTime = flight.segments?.[flight.segments.length - 1]?.arrival?.time || '--:--'
    stopInfo = flight.segments && flight.segments.length > 1 ? `${flight.segments.length - 1} stop${flight.segments.length > 2 ? 's' : ''}` : 'Direct'
  }

  return (
    <div className="flex items-center justify-between">
      <div className="text-center">
        <div className="text-2xl font-bold">
          {originTime}
        </div>
        <div className="text-sm text-muted-foreground">
          {originAirport}
        </div>
        <div className="text-xs text-muted-foreground">
          {useSearchRoute ? 'Origin' : 'Departure'}
        </div>
      </div>

      <div className="flex flex-col items-center px-4">
        <div className="text-xs text-muted-foreground mb-1">
          {flight.duration}
        </div>
        <div className="flex items-center">
          <div className="h-px bg-border flex-1 w-16"></div>
          <ArrowRight className="mx-2 h-4 w-4 text-muted-foreground" />
          <div className="h-px bg-border flex-1 w-16"></div>
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {stopInfo}
        </div>
      </div>

      <div className="text-center">
        <div className="text-2xl font-bold">
          {destinationTime}
        </div>
        <div className="text-sm text-muted-foreground">
          {destinationAirport}
        </div>
        <div className="text-xs text-muted-foreground">
          {useSearchRoute ? 'Destination' : 'Arrival'}
        </div>
      </div>
    </div>
  )
})

FlightRouteDisplay.displayName = "FlightRouteDisplay"