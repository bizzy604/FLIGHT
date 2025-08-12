"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Plane, Calendar, Users, FileText } from "lucide-react"

interface OfficialItineraryProps {
  data: any
}

export function OfficialItinerary({ data }: OfficialItineraryProps) {
  if (!data) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Itinerary data not available</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <Plane className="w-8 h-8 text-blue-600 mr-2" />
          <h1 className="text-2xl font-bold">Flight Itinerary</h1>
        </div>
        <p className="text-muted-foreground">
          Booking Reference: {data.bookingReference || 'N/A'}
        </p>
      </div>

      {/* Flight Information */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Flight Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.flights && data.flights.length > 0 ? (
              data.flights.map((flight: any, index: number) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="font-semibold">Departure</p>
                      <p>{flight.departure?.airport || 'N/A'}</p>
                      <p className="text-sm text-muted-foreground">
                        {flight.departure?.dateTime || 'N/A'}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="font-semibold">Flight</p>
                      <p>{flight.flightNumber || 'N/A'}</p>
                      <p className="text-sm text-muted-foreground">
                        {flight.airline || 'N/A'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">Arrival</p>
                      <p>{flight.arrival?.airport || 'N/A'}</p>
                      <p className="text-sm text-muted-foreground">
                        {flight.arrival?.dateTime || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-muted-foreground">No flight information available</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Passenger Information */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Passengers
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.passengers && data.passengers.length > 0 ? (
            <div className="space-y-3">
              {data.passengers.map((passenger: any, index: number) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium">
                      {passenger.firstName} {passenger.lastName}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {passenger.passengerType || 'Adult'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">
                      {passenger.documentNumber || 'N/A'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No passenger information available</p>
          )}
        </CardContent>
      </Card>

      {/* Important Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Important Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p>• Please arrive at the airport at least 2 hours before domestic flights and 3 hours before international flights.</p>
            <p>• Ensure all travel documents are valid and up to date.</p>
            <p>• Check baggage restrictions and prohibited items before traveling.</p>
            <p>• Web check-in is available 24 hours before departure.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}