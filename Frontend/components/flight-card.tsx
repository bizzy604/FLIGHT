import Link from "next/link"
import Image from "next/image"
import { ArrowRight, Clock, Luggage } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

interface FlightCardProps {
  flight: {
    id: string
    airline: {
      name: string
      logo: string
      code: string
      flightNumber: string
    }
    departure: {
      airport: string
      city: string
      time: string
      date: string
    }
    arrival: {
      airport: string
      city: string
      time: string
      date: string
    }
    duration: string
    stops: number
    stopDetails?: {
      airport: string
      city: string
      duration: string
    }[]
    price: number
    seatsAvailable: number
  }
}

export function FlightCard({ flight }: FlightCardProps) {
  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto]">
          {/* Flight Details */}
          <div className="p-4 md:p-6">
            <div className="mb-4 flex items-center">
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
                    {flight.airline.code} {flight.airline.flightNumber}
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

            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
              {/* Departure */}
              <div>
                <p className="text-2xl font-bold">{flight.departure.time}</p>
                <p className="text-sm font-medium">{flight.departure.airport}</p>
                <p className="text-xs text-muted-foreground">{flight.departure.city}</p>
              </div>

              {/* Flight Path Visualization */}
              <div className="flex flex-col items-center">
                <p className="text-xs font-medium text-muted-foreground">{flight.duration}</p>
                <div className="relative my-2 w-full">
                  <Separator className="absolute top-1/2 h-[2px] w-full -translate-y-1/2" />

                  {flight.stops === 0 && <ArrowRight className="relative mx-auto h-4 w-4 bg-background" />}

                  {flight.stops > 0 && flight.stopDetails && (
                    <div className="relative flex w-full items-center justify-center space-x-1">
                      <div className="h-2 w-2 rounded-full bg-primary"></div>
                      {flight.stopDetails.map((stop, index) => (
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
              </div>
            </div>

            {/* Stop Details */}
            {flight.stops > 0 && flight.stopDetails && (
              <div className="mt-3 rounded-md bg-muted p-2 text-xs">
                <p className="font-medium">
                  {flight.stops === 1 ? "Layover" : "Layovers"}:
                  {flight.stopDetails.map((stop, index) => (
                    <span key={index}>
                      {" "}
                      {stop.city} ({stop.airport}) - {stop.duration}
                      {index < flight.stopDetails!.length - 1 ? "," : ""}
                    </span>
                  ))}
                </p>
              </div>
            )}

            {/* Additional Info */}
            <div className="mt-4 flex items-center text-xs text-muted-foreground">
              <div className="flex items-center">
                <Luggage className="mr-1 h-3 w-3" />
                <span>Carry-on included</span>
              </div>
              <div className="ml-4 flex items-center">
                <Clock className="mr-1 h-3 w-3" />
                <span>On-time performance: 92%</span>
              </div>
              <div className="ml-auto">
                <span className="font-medium text-foreground">{flight.seatsAvailable} seats left at this price</span>
              </div>
            </div>
          </div>

          {/* Price and CTA */}
          <div className="flex flex-col justify-between border-t bg-muted p-4 md:border-l md:border-t-0">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Price per person</p>
              <p className="text-3xl font-bold">${flight.price}</p>
              <p className="text-xs text-muted-foreground">Round trip, all taxes included</p>
            </div>

            <div className="mt-4 flex flex-col space-y-2">
              <Link href={`/flights/${flight.id}`}>
                <Button className="w-full">Select</Button>
              </Link>
              <Link href={`/flights/${flight.id}/details`}>
                <Button variant="outline" className="w-full">
                  View Details
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

