"use client"

import { memo } from "react"
import Image from "next/image"
import { ArrowRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { FlightOffer } from "@/types/flight-api"

interface FlightSegmentDetailsProps {
  flight: FlightOffer
  searchParams?: {
    tripType?: string
    destination?: string
  }
  className?: string
}

export const FlightSegmentDetails = memo(function FlightSegmentDetails({
  flight,
  searchParams,
  className
}: FlightSegmentDetailsProps) {
  return (
    <div className={className}>
      <Tabs defaultValue="segments" className="w-full">
        <TabsList className="grid w-full grid-cols-1">
          <TabsTrigger value="segments">Flight Details</TabsTrigger>
        </TabsList>

        <TabsContent value="segments" className="space-y-4">
          {searchParams?.tripType === 'round-trip' ? (
            <RoundTripSegmentDetails flight={flight} searchParams={searchParams} />
          ) : (
            <OneWaySegmentDetails flight={flight} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
})

// Round-trip segment details
const RoundTripSegmentDetails = memo(function RoundTripSegmentDetails({
  flight,
  searchParams
}: {
  flight: FlightOffer
  searchParams?: { destination?: string }
}) {
  const segments = flight.segments || []

  // Determine outbound and return segments (same logic as route display)
  let outboundSegments: any[] = []
  let returnSegments: any[] = []

  if (segments.length > 0) {
    const searchDestination = searchParams?.destination || ''
    let turnaroundIndex = -1

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
      const midPoint = Math.ceil(segments.length / 2)
      outboundSegments = segments.slice(0, midPoint)
      returnSegments = segments.slice(midPoint)
    }
  }

  return (
    <div className="space-y-6">
      {/* Outbound Segments */}
      {outboundSegments.length > 0 && (
        <div>
          <h4 className="font-semibold text-sm text-muted-foreground mb-3 flex items-center">
            <ArrowRight className="w-4 h-4 mr-2" />
            Outbound Journey
          </h4>
          <div className="space-y-3">
            {outboundSegments.map((segment, index) => (
              <SegmentCard
                key={`outbound-${index}-${segment.airline?.flightNumber}`}
                segment={segment}
                airlineLogo={flight.airline?.logo}
                airlineName={flight.airline?.name}
              />
            ))}
          </div>
        </div>
      )}

      {/* Return Segments */}
      {returnSegments.length > 0 && (
        <div>
          <h4 className="font-semibold text-sm text-muted-foreground mb-3 flex items-center">
            <ArrowRight className="w-4 h-4 mr-2 rotate-180" />
            Return Journey
          </h4>
          <div className="space-y-3">
            {returnSegments.map((segment, index) => (
              <SegmentCard
                key={`return-${index}-${segment.airline?.flightNumber}`}
                segment={segment}
                airlineLogo={flight.airline?.logo}
                airlineName={flight.airline?.name}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
})

// One-way segment details
const OneWaySegmentDetails = memo(function OneWaySegmentDetails({
  flight
}: {
  flight: FlightOffer
}) {
  return (
    <div className="space-y-3">
      {flight.segments?.map((segment, index) => (
        <SegmentCard
          key={`flight-${flight.id}-detail-segment-${index}-${segment.airline?.flightNumber || 'unknown'}-${segment.departure?.airport || 'unknown'}`}
          segment={segment}
          airlineLogo={flight.airline?.logo}
          airlineName={flight.airline?.name}
        />
      ))}
    </div>
  )
})

// Individual segment card component
const SegmentCard = memo(function SegmentCard({
  segment,
  airlineLogo,
  airlineName
}: {
  segment: any
  airlineLogo?: string
  airlineName?: string
}) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Image
            src={airlineLogo || "/airlines/default.svg"}
            alt={segment.airline?.name || airlineName || "Airline"}
            width={24}
            height={24}
            className="mr-2 rounded"
          />
          <span className="font-medium">
            {segment.airline?.name || airlineName}
          </span>
        </div>
        <Badge variant="outline">
          {segment.airline?.flightNumber || segment.aircraft?.name || segment.aircraft?.code}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="font-medium">Departure</div>
          <div className="text-lg font-semibold">
            {segment.departure?.time || '--:--'}
          </div>
          <div className="text-xs text-muted-foreground">
            {segment.departure?.datetime ? new Date(segment.departure.datetime).toLocaleDateString() : ''}
          </div>
          <div className="text-muted-foreground">
            {segment.departure?.airportName || segment.departure?.airport || 'Unknown'} ({segment.departure?.airport})
          </div>
          {segment.departure?.terminal && (
            <div className="text-xs text-muted-foreground">
              Terminal {segment.departure.terminal}
            </div>
          )}
        </div>
        <div>
          <div className="font-medium">Arrival</div>
          <div className="text-lg font-semibold">
            {segment.arrival?.time || '--:--'}
          </div>
          <div className="text-xs text-muted-foreground">
            {segment.arrival?.datetime ? new Date(segment.arrival.datetime).toLocaleDateString() : ''}
          </div>
          <div className="text-muted-foreground">
            {segment.arrival?.airportName || segment.arrival?.airport || 'Unknown'} ({segment.arrival?.airport})
          </div>
          {segment.arrival?.terminal && (
            <div className="text-xs text-muted-foreground">
              Terminal {segment.arrival.terminal}
            </div>
          )}
        </div>
      </div>

      <div className="mt-2 text-sm text-muted-foreground">
        Duration: {segment.duration && segment.duration !== 'Unknown' ? segment.duration : 'Not available'}
      </div>
    </div>
  )
})

FlightSegmentDetails.displayName = "FlightSegmentDetails"