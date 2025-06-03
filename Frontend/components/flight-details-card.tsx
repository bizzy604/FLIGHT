import Image from "next/image"
import { Clock, Info, Luggage, Plane, Wifi } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface FlightDetailsCardProps {
  flight: any // Using any for brevity, but would use a proper type in a real app
}

export function FlightDetailsCard({ flight }: FlightDetailsCardProps) {
  return (
    <div className="p-4 sm:p-6">
      <div className="mb-6 flex items-center">
        <div className="flex items-center">
          <Image
            src={flight.airline.logo || "/placeholder.svg"}
            alt={flight.airline.name}
            width={40}
            height={40}
            className="mr-3 rounded-full"
          />
          <div>
            <p className="font-medium">{flight.airline.name}</p>
            <p className="text-xs text-muted-foreground">
              {flight.airline.code} {flight.airline.flightNumber} • {flight.aircraft}
            </p>
          </div>
        </div>

        {flight.stops === 0 && (
          <Badge variant="outline" className="ml-auto">
            Direct
          </Badge>
        )}

        {flight.stops > 0 && (
          <Badge variant="outline" className="ml-auto">
            {flight.stops} {flight.stops === 1 ? "stop" : "stops"}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] items-start gap-2">
        {/* Departure */}
        <div>
          <p className="text-2xl font-bold">{flight.departure.time}</p>
          <p className="text-sm font-medium">{flight.departure.airport}</p>
          <p className="text-xs text-muted-foreground">{flight.departure.city}</p>
          <p className="mt-1 text-xs">Terminal {flight.departure.terminal}</p>
        </div>

        {/* Flight Path Visualization */}
        <div className="flex flex-col items-center">
          <p className="text-xs font-medium text-muted-foreground">{flight.duration}</p>
          <div className="relative my-2 w-full">
            <Separator className="absolute top-1/2 h-[2px] w-full -translate-y-1/2" />

            {flight.stops === 0 && <Plane className="relative mx-auto h-4 w-4 rotate-90 bg-background" />}

            {flight.stops > 0 && flight.stopDetails && (
              <div className="relative flex w-full items-center justify-center space-x-1">
                <div className="h-2 w-2 rounded-full bg-primary"></div>
                {flight.stopDetails.map((stop: any, index: number) => (
                  <div key={index} className="flex items-center">
                    <div className="text-xs font-medium text-muted-foreground">{stop.airport}</div>
                    <div className="h-2 w-2 rounded-full bg-primary"></div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Arrival */}
        <div className="text-right">
          <p className="text-2xl font-bold">{flight.arrival.time}</p>
          <p className="text-sm font-medium">{flight.arrival.airport}</p>
          <p className="text-xs text-muted-foreground">{flight.arrival.city}</p>
          <p className="mt-1 text-xs">Terminal {flight.arrival.terminal}</p>
        </div>
      </div>

      {/* Flight Details */}
      <div className="mt-6 rounded-md bg-muted p-4">
        <h3 className="mb-2 text-sm font-medium">Flight Details</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs font-medium">Baggage Allowance</p>
            <div className="mt-1 flex items-start space-x-2 text-xs text-muted-foreground">
              <Luggage className="mt-0.5 h-3 w-3 flex-shrink-0" />
              <div>
                <p>Carry-on: {flight.baggageAllowance.carryOn}</p>
                <p>Checked: {flight.baggageAllowance.checked}</p>
              </div>
            </div>
          </div>

          <div>
            <p className="text-xs font-medium">Aircraft</p>
            <div className="mt-1 flex items-start space-x-2 text-xs text-muted-foreground">
              <Plane className="mt-0.5 h-3 w-3 flex-shrink-0" />
              <div>
                <p>{flight.aircraft}</p>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger className="flex items-center underline">
                      <span>Seat map</span>
                      <Info className="ml-1 h-3 w-3" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>View seat map</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>
          </div>

          <div>
            <p className="text-xs font-medium">Amenities</p>
            <div className="mt-1 flex items-start space-x-2 text-xs text-muted-foreground">
              <Wifi className="mt-0.5 h-3 w-3 flex-shrink-0" />
              <div>
                {flight.amenities.map((amenity: string, index: number) => (
                  <p key={index}>{amenity}</p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* On-time Performance */}
      <div className="mt-4 flex items-center text-xs text-muted-foreground">
        <Clock className="mr-1 h-3 w-3" />
        <span>On-time performance: 92%</span>
      </div>
    </div>
  )
}

