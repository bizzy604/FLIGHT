"use client"

import { memo } from "react"
import { Calendar as CalendarIcon, MapPin, Users, ArrowRight } from "lucide-react"
import { cn } from "@/utils/cn"
import type { FlightRouteInfoProps, PassengerCounts } from "./flight-route-info.types"

const formatPassengerCount = (passengers: PassengerCounts): string => {
  const { adults, children, infants } = passengers
  const parts = []
  
  if (adults > 0) parts.push(`${adults} ${adults === 1 ? 'adult' : 'adults'}`)
  if (children > 0) parts.push(`${children} ${children === 1 ? 'child' : 'children'}`)
  if (infants > 0) parts.push(`${infants} ${infants === 1 ? 'infant' : 'infants'}`)
  
  const breakdown = parts.join(', ')
  const total = adults + children + infants
  return `${breakdown} (${total} ${total === 1 ? 'passenger' : 'passengers'})`
}

export const FlightRouteInfo = memo(function FlightRouteInfo({
  origin,
  originCode,
  destination,
  destinationCode,
  departDate,
  returnDate,
  adults,
  children,
  infants,
  price,
  currency,
  compact = false,
  showPrice = true,
  className,
}: FlightRouteInfoProps) {
  const passengerCounts = { adults, children, infants }
  const totalPassengers = adults + children + infants

  if (compact) {
    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex items-center gap-2 text-sm">
          <MapPin className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <div className="flex items-center gap-1">
            <span className="font-medium">{originCode}</span>
            <ArrowRight className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium">{destinationCode}</span>
          </div>
          <span className="text-muted-foreground">•</span>
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">{totalPassengers}p</span>
          {showPrice && price && currency && (
            <>
              <span className="text-muted-foreground">•</span>
              <span className="font-medium">{price.toFixed(2)} {currency}</span>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold">Flight Details & Booking</h1>

      {/* Mobile Layout - Stacked */}
      <div className="mt-3 space-y-3 sm:hidden">
        <div className="flex items-center text-sm text-muted-foreground">
          <MapPin className="mr-2 h-4 w-4 flex-shrink-0" />
          <span className="break-words">
            {origin} ({originCode}) to {destination} ({destinationCode})
          </span>
        </div>
        <div className="flex items-center text-sm text-muted-foreground">
          <CalendarIcon className="mr-2 h-4 w-4 flex-shrink-0" />
          <span>
            {departDate}
            {returnDate && ` - ${returnDate}`}
          </span>
        </div>
        <div className="flex items-center text-sm text-muted-foreground">
          <Users className="mr-2 h-4 w-4 flex-shrink-0" />
          <span className="text-xs">
            {formatPassengerCount(passengerCounts)}
          </span>
        </div>
        {showPrice && price && currency && (
          <div className="bg-muted/50 rounded-lg p-3">
            <div className="text-lg font-bold text-foreground">
              Total: {price.toFixed(2)} {currency}
            </div>
          </div>
        )}
      </div>

      {/* Desktop Layout - Horizontal */}
      <div className="mt-2 hidden sm:flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
        <div className="flex items-center">
          <MapPin className="mr-1 h-4 w-4" />
          <span>
            {origin} ({originCode}) to {destination} ({destinationCode})
          </span>
        </div>
        <div className="flex items-center">
          <CalendarIcon className="mr-1 h-4 w-4" />
          <span>
            {departDate}
            {returnDate && ` - ${returnDate}`}
          </span>
        </div>
        <div className="flex items-center">
          <Users className="mr-1 h-4 w-4" />
          <span className="text-xs lg:text-sm">
            {formatPassengerCount(passengerCounts)}
          </span>
        </div>
        {showPrice && price && currency && (
          <div className="ml-auto font-medium text-foreground text-base lg:text-lg">
            Total: {price.toFixed(2)} {currency}
          </div>
        )}
      </div>
    </div>
  )
})

FlightRouteInfo.displayName = "FlightRouteInfo"