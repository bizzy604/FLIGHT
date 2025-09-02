"use client"

import { memo } from "react"
import Link from "next/link"
import { LoadingButton } from "@/components/ui/button"
import type { FlightOffer } from "@/types/flight-api"

interface FlightPricePanelProps {
  flight: FlightOffer
  flightUrl: string
  isSelecting: boolean
  onFlightSelect: (e: React.MouseEvent) => void
  className?: string
}

export const FlightPricePanel = memo(function FlightPricePanel({
  flight,
  flightUrl,
  isSelecting,
  onFlightSelect,
  className
}: FlightPricePanelProps) {
  return (
    <div className={`bg-muted/50 p-4 md:p-6 flex flex-col justify-between min-w-[200px] ${className || ''}`}>
      <div className="text-center mb-4">
        <div className="text-2xl font-bold">
          {flight.currency} {flight.price}
        </div>
        <div className="text-sm text-muted-foreground">
          for all passengers
        </div>
      </div>

      <Link href={flightUrl} className="w-full">
        <LoadingButton
          className="w-full"
          onClick={onFlightSelect}
          loading={isSelecting}
          loadingText="Selecting..."
        >
          Select Flight
        </LoadingButton>
      </Link>
    </div>
  )
})

FlightPricePanel.displayName = "FlightPricePanel"