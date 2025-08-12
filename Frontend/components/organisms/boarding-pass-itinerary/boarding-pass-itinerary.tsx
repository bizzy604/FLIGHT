"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Plane, MapPin, Calendar, Clock } from "lucide-react"

interface BoardingPassItineraryProps {
  data: any
}

export function BoardingPassItinerary({ data }: BoardingPassItineraryProps) {
  if (!data) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Boarding pass data not available</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
        <CardContent className="p-6">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center mb-2">
              <Plane className="w-6 h-6 mr-2" />
              <h2 className="text-xl font-bold">Boarding Pass</h2>
            </div>
            <p className="text-blue-100">
              {data.bookingReference || 'Booking Reference'}
            </p>
          </div>

          {/* Passenger Info */}
          <div className="mb-6">
            <h3 className="text-sm font-medium mb-2 text-blue-100">PASSENGER</h3>
            <p className="text-lg font-bold">
              {data.passengers?.[0]?.firstName} {data.passengers?.[0]?.lastName || 'Passenger Name'}
            </p>
          </div>

          {/* Flight Info */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="text-sm font-medium mb-2 text-blue-100">FROM</h3>
              <div className="flex items-center">
                <MapPin className="w-4 h-4 mr-2" />
                <div>
                  <p className="font-bold">{data.flights?.[0]?.departure?.airport || 'DEP'}</p>
                  <p className="text-sm text-blue-100">
                    {data.flights?.[0]?.departure?.city || 'Departure City'}
                  </p>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium mb-2 text-blue-100">TO</h3>
              <div className="flex items-center">
                <MapPin className="w-4 h-4 mr-2" />
                <div>
                  <p className="font-bold">{data.flights?.[0]?.arrival?.airport || 'ARR'}</p>
                  <p className="text-sm text-blue-100">
                    {data.flights?.[0]?.arrival?.city || 'Arrival City'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Departure Info */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="text-sm font-medium mb-2 text-blue-100">DEPARTURE</h3>
              <div className="flex items-center">
                <Calendar className="w-4 h-4 mr-2" />
                <p className="font-bold">
                  {data.flights?.[0]?.departure?.date || 'Date'}
                </p>
              </div>
              <div className="flex items-center mt-1">
                <Clock className="w-4 h-4 mr-2" />
                <p className="font-bold">
                  {data.flights?.[0]?.departure?.time || 'Time'}
                </p>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium mb-2 text-blue-100">FLIGHT</h3>
              <p className="font-bold text-lg">
                {data.flights?.[0]?.flightNumber || 'FL123'}
              </p>
              <p className="text-sm text-blue-100">
                {data.flights?.[0]?.airline || 'Airline'}
              </p>
            </div>
          </div>

          {/* Additional Info */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-blue-400">
            <div>
              <h3 className="text-xs font-medium text-blue-100">GATE</h3>
              <p className="font-bold">{data.flights?.[0]?.gate || 'TBA'}</p>
            </div>
            <div>
              <h3 className="text-xs font-medium text-blue-100">SEAT</h3>
              <p className="font-bold">{data.flights?.[0]?.seat || 'TBA'}</p>
            </div>
            <div>
              <h3 className="text-xs font-medium text-blue-100">TERMINAL</h3>
              <p className="font-bold">{data.flights?.[0]?.terminal || 'T1'}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}